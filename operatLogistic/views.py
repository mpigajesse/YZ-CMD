from django.shortcuts               import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib                 import messages
from django.db.models               import Q
from django.core.paginator          import Paginator
from django.http                    import JsonResponse
from django.views.decorators.http   import require_POST
from django.utils                   import timezone
from django.db                      import transaction

from parametre.models import Operateur
from commande.models  import Commande, Envoi, EnumEtatCmd, EtatCommande


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


# Vues pour le profil, à compléter si nécessaire
@login_required
def profile_logistique(request):
    return render(request, 'operatLogistic/profile.html')


@login_required
def modifier_profile_logistique(request):
    messages.info(request, "Cette fonctionnalité est en cours de développement.")
    return redirect('operatLogistic:profile')


@login_required
def changer_mot_de_passe_logistique(request):
    messages.info(request, "Cette fonctionnalité est en cours de développement.")
    return redirect('operatLogistic:profile')


@login_required
def parametre(request):
    return render(request, 'operatLogistic/parametre.html')


@login_required
def marquer_livree(request, commande_id):
    messages.info(request, "Cette fonctionnalité est en cours de développement.")
    return redirect('operatLogistic:detail_commande', commande_id=commande_id)


@login_required
def signaler_probleme(request, commande_id):
    messages.info(request, "Cette fonctionnalité est en cours de développement.")
    return redirect('operatLogistic:detail_commande', commande_id=commande_id)


@login_required
def changer_etat_sav(request, commande_id):
    messages.info(request, "Cette fonctionnalité est en cours de développement.")
    return redirect('operatLogistic:detail_commande', commande_id=commande_id)


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
            # Créer une nouvelle commande SAV
            nouvelle_commande = Commande.objects.create(
                client=commande_originale.client,
                ville=commande_originale.ville,
                adresse=commande_originale.adresse,
                total_cmd=0,  # Sera recalculé
                num_cmd=f"SAV-{commande_originale.num_cmd}",
                id_yz=f"SAV-{commande_originale.id_yz}",
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
            sous_total=prix_unitaire * quantite
        )
        
        # Recalculer le total de la commande
        total_commande = commande.paniers.aggregate(
            total=models.Sum('sous_total')
        )['total'] or 0
        commande.total_cmd = total_commande
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
        panier.sous_total = panier.article.prix_unitaire * nouvelle_quantite
        panier.save()
        
        # Recalculer le total de la commande
        total_commande = commande.paniers.aggregate(
            total=models.Sum('sous_total')
        )['total'] or 0
        commande.total_cmd = total_commande
        commande.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Quantité modifiée avec succès',
            'total_commande': float(commande.total_cmd)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


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
            total=models.Sum('sous_total')
        )['total'] or 0
        commande.total_cmd = total_commande
        commande.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Article supprimé avec succès',
            'total_commande': float(commande.total_cmd)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
