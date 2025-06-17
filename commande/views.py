from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib import messages
from django.core import serializers
from django.http import JsonResponse
from django.db import transaction
import json
from .models import Commande, Panier, EnumEtatCmd
from client.models import Client
from parametre.models import Ville, Operateur
from article.models import Article

# Create your views here.

@login_required
def liste_commandes(request):
    commandes = Commande.objects.all()
    search_query = request.GET.get('search', '')
    
    if search_query:
        commandes = commandes.filter(
            Q(num_cmd__icontains=search_query) |
            Q(id_yz__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query) |
            Q(produit_init__icontains=search_query)
        )

    # Triez par ID YZ croissant (1, 2, 3, ...)
    commandes = commandes.order_by('id_yz')

    paginator = Paginator(commandes, 10)  # 10 commandes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calculer les statistiques des états de commandes
    from .models import EtatCommande
    
    # Compter les commandes par état - utiliser distinct() pour éviter les doublons
    commandes_non_affectees = Commande.objects.filter(
        etats__enum_etat__libelle__exact='Non affectée',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    commandes_affectees = Commande.objects.filter(
        etats__enum_etat__libelle__exact='Affectée',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    commandes_erronnees = Commande.objects.filter(
        etats__enum_etat__libelle__exact='Erronée',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    commandes_doublons = Commande.objects.filter(
        etats__enum_etat__libelle__exact='Doublon',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    # Commandes nouvelles = commandes sans état actuel
    commandes_avec_etat = EtatCommande.objects.filter(date_fin__isnull=True).values_list('commande_id', flat=True).distinct()
    commandes_nouvelles = Commande.objects.exclude(id__in=commandes_avec_etat).count()

    # Récupérer les opérateurs actifs pour l'affectation
    operateurs = Operateur.objects.filter(actif=True)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_commandes': Commande.objects.count(),
        'commandes_non_affectees': commandes_non_affectees,
        'commandes_affectees': commandes_affectees,
        'commandes_erronnees': commandes_erronnees,
        'commandes_doublons': commandes_doublons,
        'commandes_nouvelles': commandes_nouvelles,
        'operateurs': operateurs,
    }
    return render(request, 'commande/liste.html', context)

@login_required
def detail_commande(request, pk):
    commande = get_object_or_404(Commande, pk=pk)
    paniers = Panier.objects.filter(commande=commande)
    historique_etats = commande.historique_etats.all()

    context = {
        'commande': commande,
        'paniers': paniers,
        'historique_etats': historique_etats,
    }
    return render(request, 'commande/detail.html', context)

@login_required
def creer_commande(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Récupérer les données de base de la commande
                num_cmd = request.POST.get('num_cmd')
                date_cmd = request.POST.get('date_cmd')
                client_id = request.POST.get('client')
                ville_id = request.POST.get('ville')
                adresse = request.POST.get('adresse')
                is_upsell = request.POST.get('is_upsell') == 'on'
                
                # Vérifier que le numéro de commande n'existe pas déjà (si fourni)
                if num_cmd and Commande.objects.filter(num_cmd=num_cmd).exists():
                    messages.error(request, f"Une commande avec le numéro {num_cmd} existe déjà.")
                    return redirect('commande:creer')
                
                # Créer la commande (l'ID YZ sera généré automatiquement)
                commande_data = {
                    'date_cmd': date_cmd,
                    'client_id': client_id,
                    'ville_id': ville_id,
                    'adresse': adresse,
                    'is_upsell': is_upsell,
                    'total_cmd': 0  # Sera calculé après ajout des articles
                }
                
                # Ajouter num_cmd seulement s'il est fourni, sinon laisser l'ID YZ être généré
                if num_cmd:
                    commande_data['num_cmd'] = num_cmd
                
                commande = Commande.objects.create(**commande_data)
                
                # Traiter les articles du panier
                total_commande = 0
                article_counter = 0
                
                while f'article_{article_counter}' in request.POST:
                    article_id = request.POST.get(f'article_{article_counter}')
                    quantite = request.POST.get(f'quantite_{article_counter}')
                    sous_total = request.POST.get(f'sous_total_{article_counter}')
                    
                    if article_id and quantite and sous_total:
                        try:
                            article = Article.objects.get(pk=article_id)
                            quantite = int(quantite)
                            sous_total = float(sous_total)
                            
                            # Créer l'entrée dans le panier
                            Panier.objects.create(
                                commande=commande,
                                article=article,
                                quantite=quantite,
                                sous_total=sous_total
                            )
                            
                            total_commande += sous_total
                        except (Article.DoesNotExist, ValueError):
                            pass
                    
                    article_counter += 1
                
                # Mettre à jour le total de la commande
                commande.total_cmd = total_commande
                commande.save()
                
                messages.success(request, f"La commande {commande.id_yz} a été créée avec succès.")
                return redirect('commande:detail', pk=commande.pk)
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la création de la commande: {str(e)}")
            return redirect('commande:creer')
    
    clients = Client.objects.all()
    villes = Ville.objects.all()
    articles = Article.objects.all()
    articles_json = serializers.serialize('json', articles, fields=('nom', 'reference', 'description', 'prix_unitaire', 'qte_disponible', 'categorie', 'couleur', 'pointure', 'image'))
    
    context = {
        'clients': clients,
        'villes': villes,
        'articles': articles,
        'articles_json': articles_json,
    }
    return render(request, 'commande/creer.html', context)

@login_required
def modifier_commande(request, pk):
    commande = get_object_or_404(Commande, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Mettre à jour les informations de base de la commande
                commande.num_cmd = request.POST.get('num_cmd')
                commande.date_cmd = request.POST.get('date_cmd')
                commande.client_id = request.POST.get('client')
                commande.ville_id = request.POST.get('ville')
                commande.adresse = request.POST.get('adresse')
                commande.is_upsell = request.POST.get('is_upsell') == 'on'
                
                # Gérer le changement d'état si spécifié
                nouvel_etat_id = request.POST.get('etat')
                if nouvel_etat_id:
                    try:
                        nouvel_etat = EnumEtatCmd.objects.get(pk=nouvel_etat_id)
                        
                        # Terminer l'état actuel s'il existe
                        etat_actuel = commande.etat_actuel
                        if etat_actuel:
                            etat_actuel.terminer_etat(request.user.operateur if hasattr(request.user, 'operateur') else None)
                        
                        # Créer le nouvel état
                        from .models import EtatCommande
                        EtatCommande.objects.create(
                            commande=commande,
                            enum_etat=nouvel_etat,
                            operateur=request.user.operateur if hasattr(request.user, 'operateur') else None,
                            commentaire=f"État modifié lors de la modification de la commande"
                        )
                        
                        messages.success(request, f"État de la commande changé vers '{nouvel_etat.libelle}'.")
                        
                    except EnumEtatCmd.DoesNotExist:
                        messages.warning(request, "L'état sélectionné n'existe pas.")
                
                # Supprimer tous les anciens articles du panier
                Panier.objects.filter(commande=commande).delete()
                
                # Ajouter les nouveaux articles du panier
                total_commande = 0
                article_counter = 0
                
                while f'article_{article_counter}' in request.POST:
                    article_id = request.POST.get(f'article_{article_counter}')
                    quantite = request.POST.get(f'quantite_{article_counter}')
                    sous_total = request.POST.get(f'sous_total_{article_counter}')
                    
                    if article_id and quantite and sous_total:
                        try:
                            article = Article.objects.get(pk=article_id)
                            quantite = int(quantite)
                            sous_total = float(sous_total)
                            
                            # Créer l'entrée dans le panier
                            Panier.objects.create(
                                commande=commande,
                                article=article,
                                quantite=quantite,
                                sous_total=sous_total
                            )
                            
                            total_commande += sous_total
                        except (Article.DoesNotExist, ValueError):
                            pass
                    
                    article_counter += 1
                
                # Mettre à jour le total de la commande
                commande.total_cmd = total_commande
                commande.save()
                
                messages.success(request, f"La commande {commande.id_yz} a été modifiée avec succès.")
                return redirect('commande:detail', pk=commande.pk)
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification de la commande: {str(e)}")
            return redirect('commande:modifier', pk=pk)
    
    clients = Client.objects.all()
    villes = Ville.objects.all()
    articles = Article.objects.all()
    paniers = Panier.objects.filter(commande=commande)
    etats_disponibles = EnumEtatCmd.objects.all().order_by('ordre', 'libelle')
    
    # Sérialiser les articles en JSON avant de les passer au template
    articles_json = serializers.serialize('json', articles, fields=('nom', 'reference', 'description', 'prix_unitaire', 'qte_disponible', 'categorie', 'couleur', 'pointure', 'image'))
    
    # Sérialiser les paniers en JSON avant de les passer au template
    paniers_json = serializers.serialize('json', paniers, fields=('article', 'quantite', 'sous_total'))

    context = {
        'commande': commande,
        'clients': clients,
        'villes': villes,
        'articles': articles,
        'paniers': paniers,
        'etats_disponibles': etats_disponibles,
        'articles_json': articles_json, # Passer la version JSON au contexte
        'paniers_json': paniers_json, # Passer la version JSON des paniers au contexte
    }
    return render(request, 'commande/modifier.html', context)

@login_required
def supprimer_commande(request, pk):
    commande = get_object_or_404(Commande, pk=pk)
    if request.method == 'POST':
        commande.delete()
        messages.success(request, "La commande a été supprimée avec succès.")
        return redirect('commande:liste')
    # Pour la modale de confirmation, on pourrait rendre un template simple ou gérer via JS
    return render(request, 'composant_generale/modal_confirmation_suppression.html', {
        'item_id': pk,
        'item_name': f"Commande {commande.num_cmd}",
        'delete_url': request.path, # L'URL de suppression est la page actuelle
        'redirect_url': '/commande/liste/',
    })

@login_required
def gestion_etats(request):
    """Page de gestion des états de commande"""
    from django.db.models import Count
    from .models import EtatCommande
    
    # Récupérer tous les états définis
    etats_definis = EnumEtatCmd.objects.all().order_by('ordre', 'libelle')
    
    # Statistiques par état
    stats_etats = {}
    for etat in etats_definis:
        # Compter les commandes actuellement dans cet état
        commandes_actuelles = EtatCommande.objects.filter(
            enum_etat=etat,
            date_fin__isnull=True  # États actifs (non terminés)
        ).count()
        
        # Compter le total historique pour cet état
        total_historique = EtatCommande.objects.filter(enum_etat=etat).count()
        
        stats_etats[etat.id] = {
            'commandes_actuelles': commandes_actuelles,
            'total_historique': total_historique
        }
    
    # Statistiques générales
    total_commandes = Commande.objects.count()
    commandes_sans_etat = Commande.objects.filter(etats__isnull=True).count()
    total_etats_definis = etats_definis.count()
    total_transitions = EtatCommande.objects.count()
    
    context = {
        'etats_definis': etats_definis,
        'stats_etats': stats_etats,
        'total_commandes': total_commandes,
        'commandes_sans_etat': commandes_sans_etat,
        'total_etats_definis': total_etats_definis,
        'total_transitions': total_transitions,
    }
    return render(request, 'commande/etats.html', context)

@require_POST
@login_required
def supprimer_commandes_masse(request):
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucune commande sélectionnée pour la suppression.")
        return redirect('commande:liste')

    try:
        count = Commande.objects.filter(pk__in=selected_ids).delete()[0]
        messages.success(request, f"{count} commande(s) supprimée(s) avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('commande:liste')

# Vues CRUD pour la gestion des états

@require_POST
@login_required
def ajouter_etat(request):
    """Ajouter un nouvel état de commande"""
    try:
        libelle = request.POST.get('libelle')
        couleur = request.POST.get('couleur')
        ordre = request.POST.get('ordre')
        
        if not libelle or not couleur or not ordre:
            return JsonResponse({'success': False, 'error': 'Tous les champs sont requis'})
        
        # Vérifier si l'état existe déjà
        if EnumEtatCmd.objects.filter(libelle=libelle).exists():
            return JsonResponse({'success': False, 'error': 'Un état avec ce libellé existe déjà'})
        
        # Créer le nouvel état
        EnumEtatCmd.objects.create(
            libelle=libelle,
            couleur=couleur,
            ordre=int(ordre)
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def modifier_etat(request, etat_id):
    """Modifier un état de commande existant"""
    try:
        etat = get_object_or_404(EnumEtatCmd, id=etat_id)
        
        libelle = request.POST.get('libelle')
        couleur = request.POST.get('couleur')
        ordre = request.POST.get('ordre')
        
        if not libelle or not couleur or not ordre:
            return JsonResponse({'success': False, 'error': 'Tous les champs sont requis'})
        
        # Vérifier si un autre état avec ce libellé existe
        if EnumEtatCmd.objects.filter(libelle=libelle).exclude(id=etat_id).exists():
            return JsonResponse({'success': False, 'error': 'Un état avec ce libellé existe déjà'})
        
        # Modifier l'état
        etat.libelle = libelle
        etat.couleur = couleur
        etat.ordre = int(ordre)
        etat.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def supprimer_etat(request, etat_id):
    """Supprimer un état de commande"""
    try:
        etat = get_object_or_404(EnumEtatCmd, id=etat_id)
        
        # Vérifier si l'état est utilisé dans des commandes
        from .models import EtatCommande
        if EtatCommande.objects.filter(enum_etat=etat).exists():
            return JsonResponse({'success': False, 'error': 'Impossible de supprimer cet état car il est utilisé dans des commandes'})
        
        etat.delete()
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def changer_couleur_etat(request, etat_id):
    """Changer la couleur d'un état de commande"""
    try:
        etat = get_object_or_404(EnumEtatCmd, id=etat_id)
        
        data = json.loads(request.body)
        couleur = data.get('couleur')
        
        if not couleur:
            return JsonResponse({'success': False, 'error': 'Couleur requise'})
        
        etat.couleur = couleur
        etat.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def monter_etat(request, etat_id):
    """Monter un état dans l'ordre"""
    try:
        etat = get_object_or_404(EnumEtatCmd, id=etat_id)
        
        # Trouver l'état précédent (ordre inférieur)
        etat_precedent = EnumEtatCmd.objects.filter(ordre__lt=etat.ordre).order_by('-ordre').first()
        
        if etat_precedent:
            # Échanger les ordres
            ordre_temp = etat.ordre
            etat.ordre = etat_precedent.ordre
            etat_precedent.ordre = ordre_temp
            
            etat.save()
            etat_precedent.save()
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Cet état est déjà en première position'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def descendre_etat(request, etat_id):
    """Descendre un état dans l'ordre"""
    try:
        etat = get_object_or_404(EnumEtatCmd, id=etat_id)
        
        # Trouver l'état suivant (ordre supérieur)
        etat_suivant = EnumEtatCmd.objects.filter(ordre__gt=etat.ordre).order_by('ordre').first()
        
        if etat_suivant:
            # Échanger les ordres
            ordre_temp = etat.ordre
            etat.ordre = etat_suivant.ordre
            etat_suivant.ordre = ordre_temp
            
            etat.save()
            etat_suivant.save()
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Cet état est déjà en dernière position'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# Vues pour la gestion des commandes par état

@login_required
def commandes_affectees(request):
    """Page des commandes affectées"""
    from .models import EtatCommande
    
    # Récupérer SEULEMENT les commandes avec un état "Affectée" exact et actuel
    commandes_affectees = Commande.objects.filter(
        etats__enum_etat__libelle__exact='Affectée',
        etats__date_fin__isnull=True
    ).distinct().order_by('-date_cmd')
    
    # Filtrage par recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_affectees = commandes_affectees.filter(
            Q(num_cmd__icontains=search_query) |
            Q(id_yz__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(commandes_affectees, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_affectees = commandes_affectees.count()
    total_montant = sum(cmd.total_cmd for cmd in commandes_affectees)
    
    # Statistiques par opérateur (pour les commandes affectées)
    operateurs_stats = {}
    for commande in commandes_affectees:
        etat_actuel = commande.etat_actuel
        if etat_actuel and etat_actuel.operateur:
            operateur_nom = etat_actuel.operateur.get_full_name()
            if operateur_nom not in operateurs_stats:
                operateurs_stats[operateur_nom] = {'count': 0, 'montant': 0}
            operateurs_stats[operateur_nom]['count'] += 1
            operateurs_stats[operateur_nom]['montant'] += commande.total_cmd
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_affectees': total_affectees,
        'total_montant': total_montant,
        'operateurs_stats': operateurs_stats,
        'page_title': 'Commandes Affectées',
        'page_subtitle': 'Gestion des commandes assignées aux opérateurs',
    }
    return render(request, 'commande/affectees.html', context)

@login_required
def commandes_annulees(request):
    """Page des commandes annulées"""
    from .models import EtatCommande
    
    # Récupérer les commandes avec un état "Annulée" actuel
    commandes_annulees = Commande.objects.filter(
        etats__enum_etat__libelle__icontains='Annulée',
        etats__date_fin__isnull=True
    ).distinct().order_by('-date_cmd')
    
    # Filtrage par recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_annulees = commandes_annulees.filter(
            Q(num_cmd__icontains=search_query) |
            Q(id_yz__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(commandes_annulees, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_annulees = commandes_annulees.count()
    total_montant_perdu = sum(cmd.total_cmd for cmd in commandes_annulees)
    
    # Statistiques par motif d'annulation
    motifs_annulation = {}
    for commande in commandes_annulees:
        motif = commande.motif_annulation or 'Non spécifié'
        motifs_annulation[motif] = motifs_annulation.get(motif, 0) + 1
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_annulees': total_annulees,
        'total_montant_perdu': total_montant_perdu,
        'motifs_annulation': motifs_annulation,
        'page_title': 'Commandes Annulées',
        'page_subtitle': 'Suivi des commandes annulées et motifs',
    }
    return render(request, 'commande/annulees.html', context)

# Nouvelles vues pour l'affectation et changement de statut

@require_POST
@login_required
def affecter_commandes(request):
    """Affecter des commandes à un opérateur"""
    try:
        commande_ids = request.POST.getlist('commande_ids[]')
        operateur_id = request.POST.get('operateur_id')
        
        if not commande_ids or not operateur_id:
            return JsonResponse({'success': False, 'error': 'Commandes et opérateur requis'})
        
        operateur = get_object_or_404(Operateur, id=operateur_id)
        
        # Récupérer ou créer l'état "Affectée"
        etat_affectee, created = EnumEtatCmd.objects.get_or_create(
            libelle='Affectée',
            defaults={'ordre': 20, 'couleur': '#3B82F6'}
        )
        
        commandes_affectees = 0
        for commande_id in commande_ids:
            try:
                commande = Commande.objects.get(id=commande_id)
                
                # Terminer l'état actuel s'il existe
                etat_actuel = commande.etat_actuel
                if etat_actuel:
                    etat_actuel.terminer_etat(operateur)
                
                # Créer le nouvel état "Affectée"
                from .models import EtatCommande
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=etat_affectee,
                    operateur=operateur,
                    commentaire=f"Commande affectée à {operateur.get_full_name()}"
                )
                
                commandes_affectees += 1
                
            except Commande.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True, 
            'message': f'{commandes_affectees} commande(s) affectée(s) à {operateur.get_full_name()}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def changer_statut_commandes(request):
    """Changer le statut de commandes"""
    try:
        commande_ids = request.POST.getlist('commande_ids[]')
        nouvel_etat_id = request.POST.get('nouvel_etat_id')
        commentaire = request.POST.get('commentaire', '')
        
        if not commande_ids or not nouvel_etat_id:
            return JsonResponse({'success': False, 'error': 'Commandes et nouvel état requis'})
        
        nouvel_etat = get_object_or_404(EnumEtatCmd, id=nouvel_etat_id)
        
        commandes_modifiees = 0
        for commande_id in commande_ids:
            try:
                commande = Commande.objects.get(id=commande_id)
                
                # Terminer l'état actuel s'il existe
                etat_actuel = commande.etat_actuel
                if etat_actuel:
                    etat_actuel.terminer_etat(request.user.operateur if hasattr(request.user, 'operateur') else None)
                
                # Créer le nouvel état
                from .models import EtatCommande
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=nouvel_etat,
                    operateur=request.user.operateur if hasattr(request.user, 'operateur') else None,
                    commentaire=commentaire or f"Statut changé vers {nouvel_etat.libelle}"
                )
                
                commandes_modifiees += 1
                
            except Commande.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True, 
            'message': f'{commandes_modifiees} commande(s) passée(s) au statut "{nouvel_etat.libelle}"'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def changer_statut_commande_unique(request, commande_id):
    """Changer le statut d'une commande unique depuis la liste"""
    try:
        nouvel_etat_id = request.POST.get('nouvel_etat_id')
        commentaire = request.POST.get('commentaire', '')
        
        if not nouvel_etat_id:
            return JsonResponse({'success': False, 'error': 'Nouvel état requis'})
        
        commande = get_object_or_404(Commande, id=commande_id)
        nouvel_etat = get_object_or_404(EnumEtatCmd, id=nouvel_etat_id)
        
        # Terminer l'état actuel s'il existe
        etat_actuel = commande.etat_actuel
        if etat_actuel:
            etat_actuel.terminer_etat(request.user.operateur if hasattr(request.user, 'operateur') else None)
        
        # Créer le nouvel état
        from .models import EtatCommande
        EtatCommande.objects.create(
            commande=commande,
            enum_etat=nouvel_etat,
            operateur=request.user.operateur if hasattr(request.user, 'operateur') else None,
            commentaire=commentaire or f"Statut changé vers {nouvel_etat.libelle}"
        )
        
        return JsonResponse({'success': True, 'message': f'Statut de la commande changé vers "{nouvel_etat.libelle}"'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
@login_required
def desaffecter_commandes(request):
    """Désaffecter des commandes (remettre à l'état 'En attente')"""
    try:
        commande_ids = request.POST.getlist('commande_ids[]')
        
        if not commande_ids:
            return JsonResponse({'success': False, 'error': 'Aucune commande sélectionnée'})
        
        # Récupérer ou créer l'état "En attente"
        etat_en_attente, created = EnumEtatCmd.objects.get_or_create(
            libelle='En attente',
            defaults={'ordre': 5, 'couleur': '#9CA3AF'}
        )
        
        commandes_desaffectees = 0
        for commande_id in commande_ids:
            try:
                commande = Commande.objects.get(id=commande_id)
                
                # Vérifier si la commande est actuellement affectée
                etat_actuel = commande.etat_actuel
                if etat_actuel and etat_actuel.enum_etat.libelle == 'Affectée':
                    # Terminer l'état actuel
                    etat_actuel.terminer_etat(request.user.operateur if hasattr(request.user, 'operateur') else None)
                    
                    # Créer le nouvel état "En attente"
                    from .models import EtatCommande
                    EtatCommande.objects.create(
                        commande=commande,
                        enum_etat=etat_en_attente,
                        operateur=request.user.operateur if hasattr(request.user, 'operateur') else None,
                        commentaire="Commande désaffectée - remise en attente"
                    )
                    
                    commandes_desaffectees += 1
                
            except Commande.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True, 
            'message': f'{commandes_desaffectees} commande(s) désaffectée(s) avec succès'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def nettoyer_etats_doublons(request):
    """Vue de maintenance pour nettoyer les états en double"""
    if request.method == 'POST':
        try:
            from django.db.models import Count
            from .models import EtatCommande
            
            # Trouver les commandes avec plusieurs états actifs
            commandes_doublons = EtatCommande.objects.filter(
                date_fin__isnull=True
            ).values('commande_id').annotate(
                count=Count('id')
            ).filter(count__gt=1)
            
            etats_nettoyes = 0
            for doublon in commandes_doublons:
                commande_id = doublon['commande_id']
                
                # Récupérer tous les états actifs de cette commande
                etats_actifs = EtatCommande.objects.filter(
                    commande_id=commande_id,
                    date_fin__isnull=True
                ).order_by('-date_debut')
                
                # Garder seulement le plus récent, terminer les autres
                for i, etat in enumerate(etats_actifs):
                    if i > 0:  # Garder le premier (plus récent), terminer les autres
                        etat.terminer_etat()
                        etats_nettoyes += 1
            
            if etats_nettoyes > 0:
                messages.success(request, f"{etats_nettoyes} état(s) en double nettoyé(s) avec succès.")
            else:
                messages.info(request, "Aucun état en double détecté.")
                
        except Exception as e:
            messages.error(request, f"Erreur lors du nettoyage: {str(e)}")
    
    # Statistiques pour la page de maintenance
    from django.db.models import Count
    from .models import EtatCommande
    
    # Compter les doublons
    doublons_count = EtatCommande.objects.filter(
        date_fin__isnull=True
    ).values('commande_id').annotate(
        count=Count('id')
    ).filter(count__gt=1).count()
    
    # Statistiques par état
    stats_etats = EtatCommande.objects.filter(
        date_fin__isnull=True
    ).values('enum_etat__libelle').annotate(
        count=Count('commande_id', distinct=True)
    ).order_by('-count')
    
    context = {
        'doublons_count': doublons_count,
        'stats_etats': stats_etats,
        'page_title': 'Maintenance des États',
        'page_subtitle': 'Nettoyage et diagnostic des états de commandes',
    }
    
    return render(request, 'commande/maintenance_etats.html', context)
