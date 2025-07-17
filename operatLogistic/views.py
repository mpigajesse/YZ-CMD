from django.shortcuts               import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib                 import messages
from django.db.models               import Q, Sum, Max
from django.core.paginator          import Paginator
from django.http                    import JsonResponse
from django.views.decorators.http   import require_POST
from django.utils                   import timezone
from django.db                      import transaction

from parametre.models import Operateur
from commande.models  import Commande, Envoi, EnumEtatCmd, EtatCommande, Operation


def corriger_affectation_commandes_renvoyees():
    """
    Fonction utilitaire pour corriger automatiquement l'affectation des commandes renvoyées.
    À appeler périodiquement ou lors de problèmes d'affectation.
    """
    try:
        # Trouver toutes les commandes renvoyées en préparation
        commandes_renvoyees = Commande.objects.filter(
            etats__enum_etat__libelle='En préparation',
            etats__date_fin__isnull=True
        ).distinct()
        
        corrections_effectuees = 0
        
        for commande in commandes_renvoyees:
            # Trouver l'état actuel
            etat_actuel = commande.etats.filter(
                enum_etat__libelle='En préparation', 
                date_fin__isnull=True
            ).first()
            
            if not etat_actuel:
                continue
                
            # Chercher l'opérateur original qui avait préparé
            etat_preparee_original = commande.etats.filter(
                enum_etat__libelle='Préparée',
                date_fin__isnull=False
            ).order_by('-date_fin').first()
            
            operateur_cible = None
            
            if etat_preparee_original and etat_preparee_original.operateur:
                if (etat_preparee_original.operateur.type_operateur == 'PREPARATION' and 
                    etat_preparee_original.operateur.actif):
                    operateur_cible = etat_preparee_original.operateur
            
            # Si pas d'opérateur original, prendre le moins chargé
            if not operateur_cible:
                operateurs_preparation = Operateur.objects.filter(
                    type_operateur='PREPARATION',
                    actif=True
                ).order_by('id')
                
                if operateurs_preparation.exists():
                    from django.db.models import Count, Q
                    operateur_cible = operateurs_preparation.annotate(
                        commandes_en_cours=Count('etats_modifies', filter=Q(
                            etats_modifies__enum_etat__libelle__in=['À imprimer', 'En préparation'],
                            etats_modifies__date_fin__isnull=True
                        ))
                    ).order_by('commandes_en_cours', 'id').first()
            
            # Corriger l'affectation si nécessaire
            if operateur_cible and etat_actuel.operateur != operateur_cible:
                ancien_operateur = etat_actuel.operateur
                etat_actuel.operateur = operateur_cible
                etat_actuel.save()
                corrections_effectuees += 1
                print(f"✅ Correction: Commande {commande.id_yz} réaffectée de {ancien_operateur} vers {operateur_cible.nom_complet}")
        
        return corrections_effectuees
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction des affectations: {e}")
        return 0


@login_required
def dashboard(request):
    """Page d'accueil de l'interface opérateur logistique."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    # Statistiques simples pour le dashboard
    en_preparation    = Commande.objects.filter(etats__enum_etat__libelle='En préparation', etats__date_fin__isnull=True).distinct().count()
    prets_expedition  = Commande.objects.filter(etats__enum_etat__libelle='Préparée',        etats__date_fin__isnull=True).distinct().count()
    expedies          = Commande.objects.filter(etats__enum_etat__libelle='En cours de livraison', etats__date_fin__isnull=True).distinct().count()
    
    context = {
        'operateur'        : operateur,
        'en_preparation'   : en_preparation,
        'prets_expedition' : prets_expedition,
        'expedies'         : expedies,
        'page_title'       : 'Tableau de Bord Logistique',
    }
    return render(request, 'composant_generale/operatLogistic/home.html', context)


@login_required
def liste_commandes(request):
    """Liste des commandes affectées à cet opérateur logistique."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    # Récupérer les commandes avec les relations nécessaires
    # Essayer plusieurs états possibles pour les commandes logistiques
    commandes_list = Commande.objects.filter(
        Q(etats__enum_etat__libelle='En cours de livraison') |
        Q(etats__enum_etat__libelle='Préparée') |
        Q(etats__enum_etat__libelle='Expédiée') |
        Q(etats__enum_etat__libelle='En livraison'),
        etats__operateur=operateur,
        etats__date_fin__isnull=True
    ).select_related(
        'client', 
        'ville', 
        'ville__region'
    ).prefetch_related(
        'etats__enum_etat',
        'etats__operateur'
    ).distinct().order_by('-etats__date_debut')
    
    # Debug: afficher les commandes trouvées
    print(f"🔍 Debug: {commandes_list.count()} commandes trouvées pour l'opérateur {operateur.nom}")
    for cmd in commandes_list[:3]:  # Afficher les 3 premières pour debug
        print(f"  - Commande {cmd.id_yz}: Client={cmd.client}, Ville={cmd.ville}")
    
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_list = commandes_list.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query)
        )
    
    # Calculer le total des montants
    total_montant = sum(cmd.total_cmd or 0 for cmd in commandes_list)
    
    paginator   = Paginator(commandes_list, 20)
    page_number = request.GET.get('page')
    page_obj    = paginator.get_page(page_number)
    
    context = {
        'page_obj'        : page_obj,
        'search_query'    : search_query,
        'total_commandes' : commandes_list.count(),
        'total_montant'   : total_montant,
        'page_title'      : 'Commandes en Livraison',
        'page_subtitle'   : f'Gestion des livraisons affectées à {operateur.prenom} {operateur.nom}',
    }
    return render(request, 'operatLogistic/liste_commande.html', context)


@login_required
def detail_commande(request, commande_id):
    """Détails d'une commande pour l'opérateur logistique."""
    commande = get_object_or_404(Commande, id=commande_id)
    # Idéalement, ajouter une vérification pour s'assurer que l'opérateur a le droit de voir cette commande
    context = {
        'commande'   : commande,
        'page_title' : f'Détail Commande {commande.id_yz}',
    }
    return render(request, 'operatLogistic/detail_commande.html', context)


# Vues pour le profil
@login_required
def profile_logistique(request):
    """Afficher le profil de l'opérateur logistique."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    context = {
        'operateur': operateur,
        'user': request.user,
    }
    return render(request, 'operatLogistic/profile.html', context)


@login_required
def modifier_profile_logistique(request):
    """Modifier le profil de l'opérateur logistique."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    if request.method == 'POST':
        # Récupérer les données du formulaire
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        telephone = request.POST.get('telephone', '').strip()
        adresse = request.POST.get('adresse', '').strip()
        photo = request.FILES.get('photo')
        
        # Validation
        if not first_name or not last_name or not email:
            messages.error(request, "Le prénom, le nom et l'email sont obligatoires.")
            return render(request, 'operatLogistic/modifier_profile.html', {
                'operateur': operateur,
                'user': request.user,
            })
        
        try:
            # Mettre à jour les informations de l'utilisateur
            user = request.user
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            
            # Mettre à jour les informations de l'opérateur
            operateur.prenom = first_name
            operateur.nom = last_name
            operateur.mail = email
            operateur.telephone = telephone if telephone else None
            operateur.adresse = adresse if adresse else None
            
            # Gérer la photo de profil
            if photo:
                operateur.photo = photo
            
            operateur.save()
            
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('operatLogistic:profile')
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la mise à jour du profil : {str(e)}")
    
    context = {
        'operateur': operateur,
        'user': request.user,
    }
    return render(request, 'operatLogistic/modifier_profile.html', context)



@login_required
def parametre(request):
    return render(request, 'operatLogistic/parametre.html')


@login_required
def marquer_livree(request, commande_id):
    messages.info(request, "Cette fonctionnalité est en cours de développement.")
    return redirect('operatLogistic:detail_commande', commande_id=commande_id)


@login_required
def signaler_probleme(request, commande_id):
    """Afficher le formulaire pour signaler un problème avec une commande."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    commande = get_object_or_404(Commande, id=commande_id)
    
    context = {
        'commande': commande,
        'page_title': 'Signaler un Problème',
        'page_subtitle': f'Commande {commande.id_yz}'
    }
    
    return render(request, 'operatLogistic/signaler_probleme.html', context)


@login_required
@require_POST
def changer_etat_sav(request, commande_id):
    """Changer l'état d'une commande pour le SAV (Reportée, Livrée, etc.)."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Récupérer les données du formulaire
        nouvel_etat = request.POST.get('nouvel_etat')
        commentaire = request.POST.get('commentaire', '').strip()
        date_report = request.POST.get('date_report')
        
        if not nouvel_etat:
            return JsonResponse({'success': False, 'error': 'Nouvel état non spécifié.'})
        
        # Validation des états autorisés
        etats_autorises = ['Reportée', 'Livrée', 'Livrée avec changement', 'Retournée']
        if nouvel_etat not in etats_autorises:
            return JsonResponse({'success': False, 'error': 'État non autorisé.'})
        
        with transaction.atomic():
            # Terminer l'état actuel
            if commande.etat_actuel:
                commande.etat_actuel.terminer_etat(operateur)
            
            # Créer le nouvel état
            etat_enum, _ = EnumEtatCmd.objects.get_or_create(
                libelle=nouvel_etat,
                defaults={'ordre': 80, 'couleur': '#6B7280'}
            )
            
            # Commentaire spécifique selon l'état
            commentaire_final = commentaire
            if nouvel_etat == 'Reportée':
                if date_report:
                    commentaire_final = f"Livraison reportée au {date_report}. {commentaire}"
                else:
                    commentaire_final = f"Livraison reportée. {commentaire}"
            elif nouvel_etat == 'Livrée avec changement':
                commentaire_final = f"Livraison effectuée avec changement d'articles. {commentaire}"
            elif nouvel_etat == 'Retournée':
                commentaire_final = f"Commande retournée par l'opérateur logistique. {commentaire}"
            
            # Créer le nouvel état
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_enum,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=commentaire_final
            )
            
            # Si c'est un report, mettre à jour l'envoi si il existe
            if nouvel_etat == 'Reportée' and commande.envois.exists():
                envoi = commande.envois.first()
                envoi.status = 'reporte'
                envoi.date_report = date_report if date_report else timezone.now().date()
                envoi.motif_report = commentaire
                envoi.save()
            
            # Créer une opération pour tracer l'action
            Operation.objects.create(
                commande=commande,
                type_operation='CHANGEMENT_ETAT_SAV',
                conclusion=f"État changé vers '{nouvel_etat}'. {commentaire_final}",
                operateur=operateur
            )
            
            messages.success(request, f"État de la commande changé vers '{nouvel_etat}' avec succès.")
            
            return JsonResponse({
                'success': True,
                'message': f'État changé vers {nouvel_etat} avec succès',
                'nouvel_etat': nouvel_etat
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def creer_envoi(request, commande_id):
    """Créer un envoi pour une commande."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        with transaction.atomic():
            # Vérifier si un envoi existe déjà
            if commande.envois.exists():
                return JsonResponse({'success': False, 'error': 'Un envoi existe déjà pour cette commande.'})
            
            # Créer l'envoi
            envoi = Envoi.objects.create(
                commande=commande,
                date_livraison_prevue=timezone.now().date(),
                operateur_creation=operateur,
                status='en_preparation'
            )
            
            # Générer un numéro d'envoi unique
            envoi.numero_envoi = f"ENV-{commande.id_yz}-{envoi.id:04d}"
            envoi.save()
            
            # Mettre à jour l'état de la commande si nécessaire
            if not commande.etat_actuel or commande.etat_actuel.enum_etat.libelle != 'En cours de livraison':
                # Fermer l'état actuel
                if commande.etat_actuel:
                    commande.etat_actuel.date_fin = timezone.now()
                    commande.etat_actuel.save()
                
                # Créer l'état "En cours de livraison"
                etat_enum, _ = EnumEtatCmd.objects.get_or_create(
                    libelle='En cours de livraison',
                    defaults={'ordre': 60, 'couleur': '#3B82F6'}
                )
                
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=etat_enum,
                    operateur=operateur,
                    date_debut=timezone.now(),
                    commentaire=f"Envoi créé: {envoi.numero_envoi}"
                )
            
            return JsonResponse({
                'success': True,
                'message': f'Envoi {envoi.numero_envoi} créé avec succès',
                'numero_envoi': envoi.numero_envoi
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def rafraichir_articles(request, commande_id):
    """Rafraîchir la section des articles d'une commande."""
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # S'assurer que les totaux sont à jour
        commande.recalculer_totaux_upsell()
        
        context = {
            'commande': commande
        }
        
        # Rendre le template partiel
        from django.template.loader import render_to_string
        html = render_to_string('operatLogistic/partials/_articles_section.html', context, request=request)
        
        return JsonResponse({
            'success': True,
            'html': html,
            'total_commande': float(commande.total_cmd),
            'articles_count': commande.paniers.count()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_articles(request):
    """API pour récupérer les articles disponibles."""
    try:
        from article.models import Article
        from django.core.serializers import serialize
        import json
        
        # Récupérer tous les articles actifs
        articles = Article.objects.filter(actif=True).order_by('nom')
        
        # Sérialiser les articles avec les champs nécessaires
        articles_data = []
        for article in articles:
            # Calculer si l'article a une promo active
            has_promo_active = False
            if hasattr(article, 'promotions') and article.promotions.exists():
                has_promo_active = article.promotions.filter(active=True).exists()
                
                article_data = {
                    'id': article.id,
                'nom': article.nom,
                'reference': article.reference,
                'description': article.description,
                'prix_unitaire': float(article.prix_unitaire),
                'prix_actuel': float(article.prix_unitaire),  # Prix de base
                'qte_disponible': article.qte_disponible,
                'categorie': article.categorie if article.categorie else None,
                'couleur': article.couleur,
                'pointure': article.pointure,
                'phase': article.phase,
                'isUpsell': article.isUpsell,
                    'has_promo_active': has_promo_active,
                # Prix upsell si disponibles
                'prix_upsell_1': float(article.prix_upsell_1) if article.prix_upsell_1 else None,
                'prix_upsell_2': float(article.prix_upsell_2) if article.prix_upsell_2 else None,
                'prix_upsell_3': float(article.prix_upsell_3) if article.prix_upsell_3 else None,
                'prix_upsell_4': float(article.prix_upsell_4) if article.prix_upsell_4 else None,
            }
                articles_data.append(article_data)
        
        return JsonResponse({
            'success': True,
            'articles': articles_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
@require_POST
def creer_commande_sav(request, commande_id):
    """Créer une nouvelle commande SAV pour les articles défectueux retournés."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande_originale = get_object_or_404(Commande, id=commande_id)
        
        # Vérifier que la commande est bien retournée
        if not commande_originale.etat_actuel or commande_originale.etat_actuel.enum_etat.libelle != 'Retournée':
            return JsonResponse({'success': False, 'error': 'Cette commande n\'est pas retournée.'})
        
        # Récupérer les articles défectueux depuis la requête POST
        import json
        articles_defectueux = json.loads(request.POST.get('articles_defectueux', '[]'))
        commentaire = request.POST.get('commentaire', '')
        
        if not articles_defectueux:
            return JsonResponse({'success': False, 'error': 'Aucun article défectueux spécifié.'})
        
        with transaction.atomic():
            # Générer un ID YZ unique pour la commande SAV
            last_id_yz = Commande.objects.aggregate(
                max_id=Max('id_yz')
            )['max_id']
            new_id_yz = (last_id_yz or 0) + 1
            
            # Créer une nouvelle commande SAV
            nouvelle_commande = Commande.objects.create(
                client=commande_originale.client,
                ville=commande_originale.ville,
                adresse=commande_originale.adresse,
                total_cmd=0,  # Sera recalculé
                num_cmd=f"SAV-{commande_originale.num_cmd}",
                id_yz=new_id_yz,
                is_upsell=False,
                compteur=0
            )
            
            total = 0
            # Créer les paniers pour les articles défectueux
            for article_data in articles_defectueux:
                article_id = article_data['article_id']
                quantite = int(article_data['quantite'])
                
                # Récupérer l'article original
                panier_original = commande_originale.paniers.filter(
                    article_id=article_id
                ).first()
                
                if panier_original:
                    from commande.models import Panier
                    Panier.objects.create(
                        commande=nouvelle_commande,
                        article=panier_original.article,
                    quantite=quantite,
                        sous_total=panier_original.article.prix_unitaire * quantite
                    )
                    total += panier_original.article.prix_unitaire * quantite
            
            # Mettre à jour le total de la commande
            nouvelle_commande.total_cmd = total
            nouvelle_commande.save()
            
            # Créer l'état initial "Non affectée"
            enum_etat = EnumEtatCmd.objects.get(libelle='Non affectée')
            EtatCommande.objects.create(
                commande=nouvelle_commande,
                enum_etat=enum_etat,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=f"Commande SAV créée pour articles défectueux de {commande_originale.id_yz}. {commentaire}"
            )
            
            messages.success(request, 
                f"Commande SAV {nouvelle_commande.id_yz} créée avec succès pour {len(articles_defectueux)} article(s) défectueux.")
            
            return JsonResponse({
                'success': True,
                'message': f'Commande SAV {nouvelle_commande.id_yz} créée avec succès',
                'commande_sav_id': nouvelle_commande.id,
                'commande_sav_num': nouvelle_commande.id_yz,
                'total': float(total)
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

    
@login_required
@require_POST
def ajouter_article(request, commande_id):
    """Ajouter un article à une commande."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        article_id = request.POST.get('article_id')
        quantite = int(request.POST.get('quantite', 1))
        
        if not article_id:
            return JsonResponse({'success': False, 'error': 'ID de l\'article manquant.'})
        
        from article.models import Article
        from commande.models import Panier
        
        article = get_object_or_404(Article, id=article_id)
        
        # Vérifier le stock si la commande est confirmée
        if commande.etat_actuel and commande.etat_actuel.enum_etat.libelle == 'Confirmée':
            if article.qte_disponible < quantite:
                        return JsonResponse({
                    'success': False, 
                    'error': f'Stock insuffisant. Disponible: {article.qte_disponible}, Demandé: {quantite}'
                })
            
            # Décrémenter le stock
            article.qte_disponible -= quantite
            article.save()
        
        # Calculer le prix selon le compteur de la commande
        prix_unitaire = article.prix_unitaire
        if commande.compteur > 0:
            if commande.compteur == 1 and article.prix_upsell_1:
                prix_unitaire = article.prix_upsell_1
            elif commande.compteur == 2 and article.prix_upsell_2:
                prix_unitaire = article.prix_upsell_2
            elif commande.compteur == 3 and article.prix_upsell_3:
                prix_unitaire = article.prix_upsell_3
            elif commande.compteur >= 4 and article.prix_upsell_4:
                prix_unitaire = article.prix_upsell_4
        
        # Créer le panier
        panier = Panier.objects.create(
                        commande=commande,
            article=article,
            quantite=quantite,
            sous_total=float(prix_unitaire * quantite)
        )
            
            # Recalculer le total de la commande
        total_commande = commande.paniers.aggregate(
            total=Sum('sous_total')
        )['total'] or 0
        commande.total_cmd = float(total_commande)
        commande.save()
            
        return JsonResponse({
            'success': True,
            'message': 'Article ajouté avec succès',
            'panier_id': panier.id,
            'total_commande': float(commande.total_cmd)
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

    
@login_required
@require_POST
def modifier_quantite_article(request, commande_id):
    """Modifier la quantité d'un article dans une commande."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        panier_id = request.POST.get('panier_id')
        nouvelle_quantite = int(request.POST.get('quantite', 1))
            
        if not panier_id:
                return JsonResponse({'success': False, 'error': 'ID du panier manquant.'})
        
        from commande.models import Panier
        
        panier = get_object_or_404(Panier, id=panier_id, commande=commande)
        ancienne_quantite = panier.quantite
        difference = nouvelle_quantite - ancienne_quantite
        
        # Vérifier le stock si la commande est confirmée
        if commande.etat_actuel and commande.etat_actuel.enum_etat.libelle == 'Confirmée':
            if difference > 0 and panier.article.qte_disponible < difference:
                return JsonResponse({
                    'success': False, 
                    'error': f'Stock insuffisant. Disponible: {panier.article.qte_disponible}, Demandé: {difference}'
                })
            
            # Ajuster le stock
            panier.article.qte_disponible -= difference
            panier.article.save()
        
        # Mettre à jour le panier
        panier.quantite = nouvelle_quantite
        panier.sous_total = float(panier.article.prix_unitaire * nouvelle_quantite)
        panier.save()
        
        # Recalculer le total de la commande
        total_commande = commande.paniers.aggregate(
            total=Sum('sous_total')
        )['total'] or 0
        commande.total_cmd = float(total_commande)
        commande.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Quantité modifiée avec succès',
            'total_commande': float(commande.total_cmd),
            'sous_total': float(panier.sous_total),
            'article_nom': panier.article.nom,
            'ancienne_quantite': ancienne_quantite
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

    
@login_required
@require_POST
def renvoyer_en_preparation(request, commande_id):
    """Renvoie une commande aux opérateurs de préparation pour modification du panier."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        commentaire = request.POST.get('commentaire', '').strip()
        
        if not commentaire:
            return JsonResponse({'success': False, 'error': 'Un commentaire est obligatoire pour expliquer le renvoi.'})
        
        # Vérifier que la commande est bien en cours de livraison
        if not commande.etat_actuel or commande.etat_actuel.enum_etat.libelle != 'En cours de livraison':
            return JsonResponse({
                'success': False, 
                'error': 'Cette commande n\'est pas en cours de livraison. Seules les commandes en cours de livraison peuvent être renvoyées en préparation.'
            })
        
        with transaction.atomic():
            # 0. Corriger automatiquement les affectations existantes si nécessaire
            corrections = corriger_affectation_commandes_renvoyees()
            if corrections > 0:
                print(f"🔧 {corrections} affectations corrigées automatiquement")
            
            # 1. Terminer l'état "En cours de livraison" actuel
            etat_actuel = commande.etat_actuel
            etat_actuel.terminer_etat(operateur)
            
            # 2. Créer ou récupérer l'état "En préparation"
            etat_en_preparation, _ = EnumEtatCmd.objects.get_or_create(
                libelle='En préparation',
                defaults={'ordre': 30, 'couleur': '#3B82F6'}
            )
            
            # 3. Identifier et réaffecter à l'opérateur de préparation original
            # Chercher l'opérateur qui avait préparé cette commande initialement
            operateur_preparation_original = None
            
            # Chercher dans l'historique des états "Préparée" de cette commande
            etat_preparee_precedent = commande.etats.filter(
                enum_etat__libelle='Préparée',
                date_fin__isnull=False  # État terminé
            ).order_by('-date_fin').first()
            
            if etat_preparee_precedent and etat_preparee_precedent.operateur:
                # Vérifier que cet opérateur est toujours actif et de type préparation
                if (etat_preparee_precedent.operateur.type_operateur == 'PREPARATION' and 
                    etat_preparee_precedent.operateur.actif):
                    operateur_preparation_original = etat_preparee_precedent.operateur
                    print(f"✅ Opérateur original trouvé: {operateur_preparation_original.nom_complet}")
                else:
                    print(f"⚠️  Opérateur original trouvé mais non disponible: {etat_preparee_precedent.operateur.nom_complet} (type: {etat_preparee_precedent.operateur.type_operateur}, actif: {etat_preparee_precedent.operateur.actif})")
            else:
                print("⚠️  Aucun état 'Préparée' trouvé dans l'historique de la commande")
            
            # Si pas d'opérateur original trouvé ou plus actif, prendre le moins chargé
            if not operateur_preparation_original:
                operateurs_preparation = Operateur.objects.filter(
                    type_operateur='PREPARATION',
                    actif=True
                ).order_by('id')
                
                if operateurs_preparation.exists():
                    from django.db.models import Count, Q
                    
                    # Annoter chaque opérateur avec le nombre de commandes en cours
                    operateurs_charges = operateurs_preparation.annotate(
                        commandes_en_cours=Count('etats_modifies', filter=Q(
                            etats_modifies__enum_etat__libelle__in=['À imprimer', 'En préparation'],
                            etats_modifies__date_fin__isnull=True
                        ))
                    ).order_by('commandes_en_cours', 'id')
                    
                    # L'opérateur le moins chargé est le premier de la liste
                    operateur_preparation_original = operateurs_charges.first()
                    print(f"✅ Affectation au moins chargé: {operateur_preparation_original.nom_complet} ({operateur_preparation_original.commandes_en_cours} commandes en cours)")
                else:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Aucun opérateur de préparation disponible. Impossible de renvoyer la commande.'
                    })
            
            # Vérification finale de sécurité
            if not operateur_preparation_original:
                return JsonResponse({
                    'success': False, 
                    'error': 'Impossible de déterminer un opérateur de préparation pour cette commande.'
                })
            
            # Créer le nouvel état "En préparation" avec l'opérateur affecté
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_en_preparation,
                operateur=operateur_preparation_original,
                date_debut=timezone.now(),
                commentaire=f"Commande renvoyée en préparation pour modification du panier client. Demande client: {commentaire}"
            )
            
            # 4. Créer une opération pour tracer l'action
            Operation.objects.create(
                commande=commande,
                type_operation='RENVOI_PREPARATION',
                conclusion=f"Commande renvoyée aux opérateurs de préparation suite à demande de modification client: {commentaire}",
                operateur=operateur
            )
            
            messages.success(request, 
                f"Commande {commande.id_yz} renvoyée avec succès aux opérateurs de préparation pour modification du panier client.")
            
            return JsonResponse({
                'success': True,
                'message': f'Commande {commande.id_yz} renvoyée aux opérateurs de préparation. Ils effectueront les modifications demandées par le client.',
                'nouvel_etat': 'En préparation',
                'commande_id': commande.id
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def commandes_renvoyees_preparation(request):
    """Affiche les commandes que cet opérateur logistique a renvoyées en préparation."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    # Récupérer les commandes que cet opérateur a renvoyées en préparation
    # On cherche les commandes qui ont un état "En préparation" actif
    commandes_renvoyees = Commande.objects.filter(
        etats__enum_etat__libelle='En préparation',
        etats__date_fin__isnull=True  # État actif
    ).select_related(
        'client', 
        'ville', 
        'ville__region'
    ).prefetch_related(
        'etats__enum_etat',
        'etats__operateur'
    ).distinct()
    
    # Filtrer pour ne garder que celles qui ont été renvoyées par cet opérateur logistique
    commandes_filtrees = []
    for commande in commandes_renvoyees:
        # Récupérer tous les états de la commande dans l'ordre chronologique
        etats_commande = commande.etats.all().order_by('date_debut')
        
        # Trouver l'état "En préparation" actuel
        etat_preparation_actuel = None
        for etat in etats_commande:
            if etat.enum_etat.libelle == 'En préparation' and not etat.date_fin:
                etat_preparation_actuel = etat
                break
        
        if etat_preparation_actuel:
            # Trouver l'état précédent (le dernier état terminé avant l'état "En préparation" actuel)
            etat_precedent = None
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_preparation_actuel.date_debut:
                    if etat.enum_etat.libelle != 'En préparation':
                        etat_precedent = etat
                        break
            
            # Si l'état précédent était "En cours de livraison", c'est un renvoi depuis la logistique
            if etat_precedent and etat_precedent.enum_etat.libelle == 'En cours de livraison':
                # Vérifier que cet opérateur logistique était impliqué
                # Soit comme opérateur de l'état précédent, soit comme opérateur qui a créé l'envoi
                if (etat_precedent.operateur == operateur or 
                    commande.envois.filter(operateur_creation=operateur).exists()):
                    commande.etat_precedent = etat_precedent
                    commande.date_renvoi = etat_preparation_actuel.date_debut
                    commandes_filtrees.append(commande)
            
            # Alternative : chercher dans les opérations de traçabilité
            # Si une commande a une opération de renvoi en préparation par cet opérateur
            from commande.models import Operation
            operation_renvoi = Operation.objects.filter(
                commande=commande,
                type_operation='RENVOI_PREPARATION',
                operateur=operateur
            ).first()
            
            if operation_renvoi:
                commande.etat_precedent = etat_precedent
                commande.date_renvoi = operation_renvoi.date_operation
                if commande not in commandes_filtrees:
                    commandes_filtrees.append(commande)
            
            # 4. Vérifier si c'est une commande de renvoi créée lors d'une livraison partielle
            # Chercher les commandes de renvoi créées par cet opérateur lors d'une livraison partielle
            if commande.num_cmd and commande.num_cmd.startswith('RENVOI-'):
                # Chercher l'opération de livraison partielle qui a créé cette commande de renvoi
                operation_livraison_partielle = Operation.objects.filter(
                    type_operation='LIVRAISON_PARTIELLE',
                    operateur=operateur,
                    conclusion__icontains=commande.num_cmd.replace('RENVOI-', '')
                ).first()
                
                if operation_livraison_partielle:
                    commande.etat_precedent = None  # Pas d'état précédent pour les commandes de renvoi
                    commande.date_renvoi = etat_preparation_actuel.date_debut
                    commande.type_renvoi = 'livraison_partielle'
                    if commande not in commandes_filtrees:
                        commandes_filtrees.append(commande)
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_filtrees = [cmd for cmd in commandes_filtrees if 
            search_query.lower() in str(cmd.id_yz).lower() or
            search_query.lower() in (cmd.num_cmd or '').lower() or
            search_query.lower() in cmd.client.nom.lower() or
            search_query.lower() in cmd.client.prenom.lower() or
            search_query.lower() in (cmd.client.numero_tel or '').lower()
        ]
    
    # Tri par date de renvoi (plus récentes en premier)
    commandes_filtrees.sort(key=lambda x: x.date_renvoi, reverse=True)
    
    # Pagination
    paginator = Paginator(commandes_filtrees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_renvoyees = len(commandes_filtrees)
    valeur_totale = sum(cmd.total_cmd or 0 for cmd in commandes_filtrees)
    
    # Commandes renvoyées aujourd'hui
    aujourd_hui = timezone.now().date()
    renvoyees_aujourd_hui = sum(1 for cmd in commandes_filtrees if cmd.date_renvoi.date() == aujourd_hui)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_renvoyees': total_renvoyees,
        'valeur_totale': valeur_totale,
        'renvoyees_aujourd_hui': renvoyees_aujourd_hui,
        'page_title': 'Commandes Renvoyées en Préparation',
        'page_subtitle': f'Commandes que vous avez renvoyées aux opérateurs de préparation',
        'operateur': operateur,
    }
    return render(request, 'operatLogistic/commandes_renvoyees_preparation.html', context)


@login_required
@require_POST
def supprimer_article(request, commande_id):
    """Supprimer un article d'une commande."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        panier_id = request.POST.get('panier_id')
        
        if not panier_id:
            return JsonResponse({'success': False, 'error': 'ID du panier manquant.'})
        
        from commande.models import Panier
        
        panier = get_object_or_404(Panier, id=panier_id, commande=commande)
        quantite_supprimee = panier.quantite
        
        # Réincrémenter le stock si la commande est confirmée
        if commande.etat_actuel and commande.etat_actuel.enum_etat.libelle == 'Confirmée':
            panier.article.qte_disponible += quantite_supprimee
            panier.article.save()
                        
        # Supprimer le panier
        panier.delete()
                
                # Recalculer le total de la commande
        total_commande = commande.paniers.aggregate(
            total=Sum('sous_total')
                )['total'] or 0
        commande.total_cmd = float(total_commande)
        commande.save()
            
        return JsonResponse({
                'success': True,
            'message': 'Article supprimé avec succès',
            'total_commande': float(commande.total_cmd)
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def livraison_partielle(request, commande_id):
    """Gérer une livraison partielle avec sélection d'articles."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Profil d\'opérateur logistique non trouvé.'})
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Vérifier que la commande est bien en cours de livraison
        if not commande.etat_actuel or commande.etat_actuel.enum_etat.libelle != 'En cours de livraison':
            return JsonResponse({
                'success': False, 
                'error': 'Cette commande n\'est pas en cours de livraison. Seules les commandes en cours de livraison peuvent être livrées partiellement.'
            })
        
        # Récupérer les données du formulaire
        import json
        articles_livres = json.loads(request.POST.get('articles_livres', '[]'))
        articles_renvoyes = json.loads(request.POST.get('articles_renvoyes', '[]'))
        commentaire = request.POST.get('commentaire', '').strip()
        
        if not commentaire:
            return JsonResponse({'success': False, 'error': 'Un commentaire est obligatoire pour expliquer la livraison partielle.'})
        
        if not articles_livres:
            return JsonResponse({'success': False, 'error': 'Aucun article à livrer spécifié.'})
        
        if not articles_renvoyes:
            return JsonResponse({'success': False, 'error': 'Aucun article à renvoyer spécifié.'})
        
        with transaction.atomic():
            # 1. Terminer l'état "En cours de livraison" actuel
            etat_actuel = commande.etat_actuel
            etat_actuel.terminer_etat(operateur)
            
            # 2. Créer l'état "Livrée Partiellement"
            etat_livree_partiellement, _ = EnumEtatCmd.objects.get_or_create(
                libelle='Livrée Partiellement',
                defaults={'ordre': 70, 'couleur': '#3B82F6'}
            )
            
            # 3. Créer le nouvel état avec le commentaire
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_livree_partiellement,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=f"Livraison partielle effectuée. {commentaire}"
            )
            
            # 4. Créer une nouvelle commande pour les articles renvoyés
            # Filtrer les articles renvoyés pour éviter les doublons avec les articles livrés
            articles_renvoyes_filtres = []
            articles_livres_ids = [article_data['article_id'] for article_data in articles_livres]
            
            for article_renvoye in articles_renvoyes:
                # Ne pas ajouter si l'article est déjà dans les articles livrés
                if article_renvoye['article_id'] not in articles_livres_ids:
                    articles_renvoyes_filtres.append(article_renvoye)
                else:
                    # Vérifier si c'est une quantité partielle à renvoyer
                    article_livre = next((a for a in articles_livres if a['article_id'] == article_renvoye['article_id']), None)
                    if article_livre and article_renvoye['quantite'] > article_livre['quantite']:
                        # Ajouter seulement la quantité restante
                        quantite_restante = article_renvoye['quantite'] - article_livre['quantite']
                        if quantite_restante > 0:
                            articles_renvoyes_filtres.append({
                                **article_renvoye,
                                'quantite': quantite_restante
                            })
            
            if articles_renvoyes_filtres:
                # Générer un ID YZ unique pour la commande de renvoi
                last_id_yz = Commande.objects.aggregate(
                    max_id=Max('id_yz')
                )['max_id']
                new_id_yz = (last_id_yz or 0) + 1
                
                nouvelle_commande = Commande.objects.create(
                    client=commande.client,
                    ville=commande.ville,
                    adresse=commande.adresse,
                    total_cmd=0,  # Sera recalculé
                    num_cmd=f"RENVOI-{commande.num_cmd}",
                    id_yz=new_id_yz,
                    is_upsell=False,
                    compteur=0
                )
                
                total_renvoi = 0
                # Créer les paniers pour les articles renvoyés
                for article_data in articles_renvoyes_filtres:
                    panier_original = commande.paniers.filter(
                        article_id=article_data['article_id']
                    ).first()
                    
                    if panier_original:
                        from commande.models import Panier
                        Panier.objects.create(
                            commande=nouvelle_commande,
                            article=panier_original.article,
                            quantite=article_data['quantite'],
                            sous_total=panier_original.article.prix_unitaire * article_data['quantite']
                        )
                        total_renvoi += panier_original.article.prix_unitaire * article_data['quantite']
                
                # Mettre à jour le total de la commande de renvoi
                nouvelle_commande.total_cmd = total_renvoi
                nouvelle_commande.save()
                
                # Mettre à jour les références pour utiliser les articles filtrés
                articles_renvoyes = articles_renvoyes_filtres
                
                # 4.1. Identifier et affecter à l'opérateur de préparation original
                # Chercher l'opérateur qui avait préparé cette commande initialement
                operateur_preparation_original = None
                
                # Chercher dans l'historique des états "Préparée" de la commande originale
                etat_preparee_precedent = commande.etats.filter(
                    enum_etat__libelle='Préparée',
                    date_fin__isnull=False  # État terminé
                ).order_by('-date_fin').first()
                
                if etat_preparee_precedent and etat_preparee_precedent.operateur:
                    # Vérifier que cet opérateur est toujours actif et de type préparation
                    if (etat_preparee_precedent.operateur.type_operateur == 'PREPARATION' and 
                        etat_preparee_precedent.operateur.actif):
                        operateur_preparation_original = etat_preparee_precedent.operateur
                        print(f"✅ Opérateur original trouvé pour livraison partielle: {operateur_preparation_original.nom_complet}")
                    else:
                        print(f"⚠️  Opérateur original trouvé mais non disponible: {etat_preparee_precedent.operateur.nom_complet} (type: {etat_preparee_precedent.operateur.type_operateur}, actif: {etat_preparee_precedent.operateur.actif})")
                else:
                    print("⚠️  Aucun état 'Préparée' trouvé dans l'historique de la commande")
                
                # Si pas d'opérateur original trouvé ou plus actif, prendre le moins chargé
                if not operateur_preparation_original:
                    operateurs_preparation = Operateur.objects.filter(
                        type_operateur='PREPARATION',
                        actif=True
                    ).order_by('id')
                    
                    if operateurs_preparation.exists():
                        from django.db.models import Count, Q
                        
                        # Annoter chaque opérateur avec le nombre de commandes en cours
                        operateurs_charges = operateurs_preparation.annotate(
                            commandes_en_cours=Count('etats_modifies', filter=Q(
                                etats_modifies__enum_etat__libelle__in=['À imprimer', 'En préparation'],
                                etats_modifies__date_fin__isnull=True
                            ))
                        ).order_by('commandes_en_cours', 'id')
                        
                        # L'opérateur le moins chargé est le premier de la liste
                        operateur_preparation_original = operateurs_charges.first()
                        print(f"✅ Affectation au moins chargé pour livraison partielle: {operateur_preparation_original.nom_complet} ({operateur_preparation_original.commandes_en_cours} commandes en cours)")
                    else:
                        return JsonResponse({
                            'success': False, 
                            'error': 'Aucun opérateur de préparation disponible. Impossible de créer la commande de renvoi.'
                        })
                
                # Vérification finale de sécurité
                if not operateur_preparation_original:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Impossible de déterminer un opérateur de préparation pour la commande de renvoi.'
                    })
                
                # Créer l'état "En préparation" pour la commande de renvoi avec l'opérateur original
                etat_en_preparation, _ = EnumEtatCmd.objects.get_or_create(
                    libelle='En préparation',
                    defaults={'ordre': 30, 'couleur': '#3B82F6'}
                )
                
                EtatCommande.objects.create(
                    commande=nouvelle_commande,
                    enum_etat=etat_en_preparation,
                    operateur=operateur_preparation_original,
                    date_debut=timezone.now(),
                    commentaire=f"Commande de renvoi créée suite à livraison partielle de {commande.id_yz}. Articles non livrés: {len(articles_renvoyes)}. Affectée à l'opérateur original: {operateur_preparation_original.nom_complet}"
                )
            
            # 5. Mettre à jour les quantités des articles livrés dans la commande originale
            # et supprimer les articles complètement renvoyés
            for article_data in articles_livres:
                panier = commande.paniers.filter(
                    article_id=article_data['article_id']
                ).first()
                
                if panier:
                    if article_data['quantite'] > 0:
                        # Mettre à jour la quantité et le sous-total
                        panier.quantite = article_data['quantite']
                        panier.sous_total = panier.article.prix_unitaire * article_data['quantite']
                        panier.save()
                    else:
                        # Si quantité = 0, supprimer l'article de la commande originale
                        panier.delete()
            
            # Supprimer les articles complètement renvoyés de la commande originale
            # Utiliser les articles filtrés pour éviter les conflits
            articles_renvoyes_ids = [article_data['article_id'] for article_data in articles_renvoyes]
            commande.paniers.filter(article_id__in=articles_renvoyes_ids).delete()
            
            # 6. Recalculer le total de la commande originale
            total_commande = commande.paniers.aggregate(
                total=Sum('sous_total')
            )['total'] or 0
            commande.total_cmd = float(total_commande)
            commande.save()
            
            # 7. Créer une opération pour tracer l'action
            Operation.objects.create(
                commande=commande,
                type_operation='LIVRAISON_PARTIELLE',
                conclusion=f"Livraison partielle effectuée. Articles livrés: {len(articles_livres)}, Articles renvoyés: {len(articles_renvoyes)}. {commentaire}",
                operateur=operateur
            )
            
            # 8. Créer une opération pour tracer l'affectation de la commande de renvoi
            if articles_renvoyes and operateur_preparation_original:
                Operation.objects.create(
                    commande=nouvelle_commande,
                    type_operation='AFFECTATION_AUTO_PREPARATION',
                    conclusion=f"Commande de renvoi automatiquement affectée à l'opérateur original: {operateur_preparation_original.nom_complet} suite à livraison partielle de {commande.id_yz}",
                    operateur=operateur
                )
            
            messages.success(request, 
                f"Livraison partielle effectuée avec succès. {len(articles_livres)} article(s) livré(s), {len(articles_renvoyes)} article(s) renvoyé(s) en préparation.")
            
            return JsonResponse({
                'success': True,
                'message': f'Livraison partielle effectuée avec succès',
                'articles_livres': len(articles_livres),
                'articles_renvoyes': len(articles_renvoyes),
                'commande_renvoi_id': nouvelle_commande.id if articles_renvoyes else None,
                'commande_renvoi_num': nouvelle_commande.id_yz if articles_renvoyes else None
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def api_panier_commande(request, commande_id):
    """API pour récupérer les données du panier d'une commande."""
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Récupérer les paniers avec les articles
        paniers = commande.paniers.select_related('article').all()
        
        # Préparer les données du panier
        paniers_data = []
        for panier in paniers:
            paniers_data.append({
                'id': panier.id,
                'nom': panier.article.nom,
                'reference': panier.article.reference,
                'quantite': panier.quantite,
                'prix_unitaire': f"{panier.article.prix_unitaire:.2f}",
                'sous_total': f"{panier.sous_total:.2f}",
                'pointure': panier.article.pointure,
                'couleur': panier.article.couleur,
            })
        
        # Préparer les données de la commande
        commande_data = {
            'id': commande.id,
            'id_yz': commande.id_yz,
            'num_cmd': commande.num_cmd,
            'total_cmd': f"{commande.total_cmd:.2f}",
            'date_cmd': commande.date_cmd.strftime('%d/%m/%Y') if commande.date_cmd else None,
            'etat_actuel': commande.etat_actuel.enum_etat.libelle if commande.etat_actuel else None,
        }
        
        return JsonResponse({
            'success': True,
            'commande': commande_data,
            'paniers': paniers_data,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
