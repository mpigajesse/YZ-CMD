from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Sum, Count
from django.db import models, transaction
from django.core.paginator import Paginator
from django.contrib import messages
from django.core import serializers
from django.http import JsonResponse, HttpResponse # Import HttpResponse for partial rendering
import json
from .models import Commande, Panier, EnumEtatCmd
from client.models import Client
from parametre.models import Ville, Operateur, Region # Import Region
from article.models import Article
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, datetime
from django.template.loader import render_to_string # Import render_to_string

# Create your views here.

@login_required
def liste_commandes(request):
    commandes = Commande.objects.select_related('client', 'ville').prefetch_related('etats__enum_etat')
    search_query = request.GET.get('search', '')
    ville_filter = request.GET.get('ville_filter', '')
    ville_init_filter = request.GET.get('ville_init_filter', '')
    region_filter = request.GET.get('region_filter', '')
    etat_filter = request.GET.get('etat_filter', '')
    sync_filter = request.GET.get('sync_filter', '') # Nouveau filtre
    custom_sync_date = request.GET.get('custom_sync_date', '') # Nouvelle date personnalisée
    
    # Recherche par texte général
    if search_query:
        # Vérifier si la recherche correspond exactement à une ville_init
        exact_ville_init_match = Commande.objects.filter(
            ville_init__iexact=search_query
        ).exists()
        
        if exact_ville_init_match:
            # Si la recherche correspond exactement à une ville_init, on filtre directement
            commandes = commandes.filter(ville_init__iexact=search_query)
        else:
            commandes = commandes.filter(
                Q(num_cmd__icontains=search_query) |
                Q(id_yz__icontains=search_query) |
                Q(client__nom__icontains=search_query) |
                Q(client__prenom__icontains=search_query) |
                Q(client__numero_tel__icontains=search_query) |
                Q(produit_init__icontains=search_query) |
                # Recherche par ville (dans les deux champs)
                Q(ville__nom__icontains=search_query) |
                Q(ville_init__icontains=search_query) |
                # Recherche par région
                Q(ville__region__nom_region__icontains=search_query) |
                # Recherche par état de commande
                Q(etats__enum_etat__libelle__icontains=search_query) |
                # Recherche par adresse
                Q(adresse__icontains=search_query)
            ).distinct()
    
    # Filtre par ville du système
    if ville_filter:
        commandes = commandes.filter(ville_id=ville_filter)
    
    # Filtre par ville initiale (du fichier) - indépendant des autres filtres
    if ville_init_filter:
        commandes = commandes.filter(ville_init__iexact=ville_init_filter)
    
    # Filtre par région
    if region_filter:
        commandes = commandes.filter(ville__region_id=region_filter)
    
    # Filtre par état spécifique
    if etat_filter:
        commandes = commandes.filter(
            etats__enum_etat_id=etat_filter,
            etats__date_fin__isnull=True  # État actuel
        ).distinct()

    # Nouveau filtre pour les commandes synchronisées
    if sync_filter:
        commandes = commandes.filter(origine='GSheet') # Ensure we only filter GSheet origin commands
        if sync_filter == 'last_minute':
            commandes = commandes.filter(last_sync_date__gte=timezone.now() - timedelta(minutes=1))
        elif sync_filter == 'last_hour':
            commandes = commandes.filter(last_sync_date__gte=timezone.now() - timedelta(hours=1))
        elif sync_filter == 'today':
            commandes = commandes.filter(last_sync_date__date=timezone.now().date())
        elif sync_filter == 'last_24_hours':
            commandes = commandes.filter(last_sync_date__gte=timezone.now() - timedelta(hours=24))
        elif sync_filter == 'last_7_days':
            commandes = commandes.filter(last_sync_date__gte=timezone.now() - timedelta(days=7))
        elif sync_filter == 'custom_date' and custom_sync_date:
            try:
                filter_date = datetime.strptime(custom_sync_date, '%Y-%m-%d').date()
                # Filter for orders synced on the selected date
                commandes = commandes.filter(last_sync_date__date=filter_date)
            except ValueError:
                pass # Ignore invalid date

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
    
    # Récupérer les listes pour les filtres
    # from parametre.models import Ville, Region # Already imported
    villes = Ville.objects.all().order_by('nom')
    regions = Region.objects.all().order_by('nom_region')
    etats = EnumEtatCmd.objects.all().order_by('ordre', 'libelle')
    
    # Récupérer les villes uniques du champ ville_init
    villes_init = Commande.objects.exclude(ville_init__isnull=True).exclude(ville_init='').values_list('ville_init', flat=True).distinct().order_by('ville_init')

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'ville_filter': ville_filter,
        'ville_init_filter': ville_init_filter,
        'region_filter': region_filter,
        'etat_filter': etat_filter,
        'sync_filter': sync_filter, # Ajouter le nouveau filtre au contexte
        'custom_sync_date': custom_sync_date, # Ajouter la date personnalisée au contexte
        'villes': villes,
        'villes_init': villes_init,
        'regions': regions,
        'etats': etats,
        'total_commandes': Commande.objects.count(),
        'commandes_non_affectees': commandes_non_affectees,
        'commandes_affectees': commandes_affectees,
        'commandes_erronnees': commandes_erronnees,
        'commandes_doublons': commandes_doublons,
        'commandes_nouvelles': commandes_nouvelles,
        'operateurs': operateurs,
    }
    
    # Check if the request is AJAX
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Render only the table body and pagination as HTML
        html_table_body = render_to_string('commande/partials/_commande_table_body.html', context, request=request)
        html_pagination = render_to_string('commande/partials/_pagination.html', context, request=request)
        
        return JsonResponse({
            'html_table_body': html_table_body,
            'html_pagination': html_pagination,
            'total_commands_display': f"Affichage de {page_obj.start_index()} à {page_obj.end_index()} sur {page_obj.paginator.count} commandes.",
            'total_commands_count': page_obj.paginator.count # Add this to the JSON response
        })
        
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
                # Déterminer le type de client
                type_client = request.POST.get('type_client')
                
                # Gestion du client
                if type_client == 'nouveau':
                    # Créer un nouveau client
                    client = Client.objects.create(
                        prenom=request.POST.get('nouveau_prenom'),
                        nom=request.POST.get('nouveau_nom'),
                        numero_tel=request.POST.get('nouveau_telephone'),
                        email=request.POST.get('nouveau_email', '')  # Email optionnel
                    )
                else:
                    # Utiliser un client existant
                    client_id = request.POST.get('client')
                    if not client_id:
                        messages.error(request, "Veuillez sélectionner un client.")
                        return redirect('commande:creer')
                    client = Client.objects.get(pk=client_id)

                # Récupérer les autres données de la commande
                ville_id = request.POST.get('ville_livraison')
                adresse = request.POST.get('adresse')
                is_upsell = request.POST.get('is_upsell') == 'on'
                
                # Créer la commande
                commande = Commande.objects.create(
                    client=client,
                    ville_id=ville_id,
                    adresse=adresse,
                    total_cmd=0,  # Sera calculé après ajout des articles
                    is_upsell=is_upsell,
                    origine='ADMIN'  # Définir l'origine comme Administrateur
                )
                
                # Traiter les articles du panier
                total_commande = 0
                article_counter = 0
                
                while f'article_{article_counter}' in request.POST:
                    article_id = request.POST.get(f'article_{article_counter}')
                    if article_id:
                        article = Article.objects.get(pk=article_id)
                        quantite = int(request.POST.get(f'quantite_{article_counter}', 1))
                        
                        # Calculer le sous-total selon la logique upsell
                        from commande.templatetags.commande_filters import calculer_sous_total_upsell
                        sous_total = calculer_sous_total_upsell(article, quantite)
                        
                        # Créer le panier
                        Panier.objects.create(
                            commande=commande,
                            article=article,
                            quantite=quantite,
                            sous_total=sous_total
                        )
                        
                        # Mettre à jour le total
                        total_commande += sous_total
                        
                        # Incrémenter le compteur si c'est un article upsell
                        if article.isUpsell and quantite > 1:
                            commande.compteur += 1
                    
                    article_counter += 1
                
                # Mettre à jour le total de la commande
                commande.total_cmd = total_commande
                commande.save()
                
                messages.success(request, "La commande a été créée avec succès.")
                return redirect('commande:detail', pk=commande.pk)
                
        except Client.DoesNotExist:
            messages.error(request, "Le client sélectionné n'existe pas.")
        except Article.DoesNotExist:
            messages.error(request, "Un des articles sélectionnés n'existe pas.")
        except Exception as e:
            messages.error(request, f"Une erreur s'est produite lors de la création de la commande : {str(e)}")
        
        return redirect('commande:creer')
    
    # GET request
    context = {
        'clients': Client.objects.all().order_by('nom', 'prenom'),
        'articles': Article.objects.all().order_by('nom'),
        'villes': Ville.objects.select_related('region').all().order_by('nom'),
    }
    
    # Debug des frais de livraison
    for ville in context['villes']:
        print(f"Ville: {ville.nom}, Frais: {ville.frais_livraison}, Région: {ville.region.nom_region if ville.region else 'N/A'}")
    
    return render(request, 'commande/creer.html', context)

@login_required
def modifier_commande(request, pk):
    commande = get_object_or_404(Commande, pk=pk)
    if request.method == 'POST':
        try:
            with transaction.atomic():
                action = request.POST.get('action', 'update_info')
                
                if action == 'update_client':
                    # === MISE À JOUR DU TÉLÉPHONE CLIENT UNIQUEMENT ===
                    if 'telephone_client' in request.POST and request.POST.get('telephone_client'):
                        ancien_tel = commande.client.numero_tel
                        nouveau_tel = request.POST.get('telephone_client')
                        commande.client.numero_tel = nouveau_tel
                        commande.client.save()
                        messages.success(request, f"Téléphone modifié avec succès : {ancien_tel} → {nouveau_tel}")
                    else:
                        messages.warning(request, "Aucun téléphone fourni pour la modification")
                
                elif action == 'update_panier':
                    # === MISE À JOUR DU PANIER UNIQUEMENT ===
                    # Supprimer tous les anciens articles du panier
                    Panier.objects.filter(commande=commande).delete()
                
                    # Ajouter les nouveaux articles du panier
                    total_commande = 0
                    article_counter = 0
                    
                    while f'article_{article_counter}' in request.POST:
                        article_id = request.POST.get(f'article_{article_counter}')
                        quantite = request.POST.get(f'quantite_{article_counter}')
                        
                        if article_id and quantite:
                            try:
                                article = Article.objects.get(pk=article_id)
                                quantite = int(quantite)
                                
                                # Calculer le sous-total selon la logique upsell
                                from commande.templatetags.commande_filters import calculer_sous_total_upsell
                                sous_total = calculer_sous_total_upsell(article, quantite)
                                
                                # Créer l'entrée dans le panier
                                Panier.objects.create(
                                    commande=commande,
                                    article=article,
                                    quantite=quantite,
                                    sous_total=sous_total
                                )
                                
                                total_commande += sous_total
                                
                                # Incrémenter le compteur si c'est un article upsell
                                if article.isUpsell and quantite > 1:
                                    commande.compteur += 1
                            except (Article.DoesNotExist, ValueError):
                                pass
                        
                        article_counter += 1
                    
                    # Mettre à jour le total de la commande
                    commande.total_cmd = total_commande
                    commande.save()
                    
                    messages.success(request, f"Le panier de la commande {commande.id_yz} a été mis à jour avec succès.")
                
                else:
                    # === MISE À JOUR DES INFORMATIONS GÉNÉRALES ===
                    # Mise à jour de l'adresse de livraison (saisie manuelle)
                    if 'adresse' in request.POST:
                        commande.adresse = request.POST.get('adresse')
                    
                    # Option upsell
                    commande.is_upsell = request.POST.get('is_upsell') == 'on'
                    
                    # Note: La ville et l'adresse de livraison sont issues de la commande originale
                    # Les autres champs (ID YZ, date, client, valeur) sont en lecture seule
                    
                    # Gérer le changement d'état si spécifié (workflow simplifié)
                    nouvel_etat_id = request.POST.get('etat')
                    if nouvel_etat_id:
                        try:
                            nouvel_etat = EnumEtatCmd.objects.get(pk=nouvel_etat_id)
                            
                            # Vérifier que l'état est autorisé (workflow simplifié)
                            etats_autorises = ['Non affectée', 'Annulée']
                            if nouvel_etat.libelle not in etats_autorises:
                                messages.warning(request, f"L'état '{nouvel_etat.libelle}' n'est pas autorisé dans le workflow simplifié.")
                            else:
                                # Traitement spécial pour l'annulation - demander un motif
                                if nouvel_etat.libelle == 'Annulée':
                                    messages.warning(request, "Pour annuler une commande, utilisez le bouton 'Annuler' qui permet de saisir un motif obligatoire.")
                                else:
                                    # Utiliser la fonction utilitaire pour gérer le changement d'état
                                    operateur = request.user.operateur if hasattr(request.user, 'operateur') else None
                                    redirect_url, error = gerer_changement_etat_automatique(
                                        commande, 
                                        nouvel_etat.libelle, 
                                        operateur, 
                                        f"État modifié manuellement vers '{nouvel_etat.libelle}'"
                                    )
                                    
                                    if error:
                                        messages.error(request, f"Erreur lors du changement d'état: {error}")
                                    else:
                                        messages.success(request, f"État de la commande changé vers '{nouvel_etat.libelle}'.")
                                        
                                        # Rediriger automatiquement vers la page appropriée
                                        if nouvel_etat.libelle == 'Non affectée' and redirect_url:
                                            return redirect(redirect_url)
                            
                        except EnumEtatCmd.DoesNotExist:
                            messages.warning(request, "L'état sélectionné n'existe pas.")
                    
                    commande.save()
                    messages.success(request, f"Les informations de la commande {commande.id_yz} ont été mises à jour avec succès.")
                
                # Gestion de la redirection selon l'action
                if action in ['update_panier', 'update_client']:
                    # Pour les mises à jour du panier ou client, rester sur la page
                    pass  # Pas de redirection, on continue à afficher la page
                elif request.POST.get('from') == 'a_traiter':
                    return redirect('commande:a_traiter')
                else:
                    # Pour les autres modifications, rester sur la page
                    pass  # Pas de redirection, on continue à afficher la page
                
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

    # Détecter si on vient de la page "À Traiter"
    from_a_traiter = request.GET.get('from') == 'a_traiter'
    
    # Déterminer le type de problème si on vient de la page "À Traiter"
    probleme_type = None
    if from_a_traiter and commande.etat_actuel:
        if commande.etat_actuel.enum_etat.libelle == 'Doublon':
            probleme_type = 'doublon'
        elif commande.etat_actuel.enum_etat.libelle == 'Erronée':
            probleme_type = 'erronnee'

    context = {
        'commande': commande,
        'clients': clients,
        'villes': villes,
        'articles': articles,
        'paniers': paniers,
        'etats_disponibles': etats_disponibles,
        'articles_json': articles_json, # Passer la version JSON au contexte
        'paniers_json': paniers_json, # Passer la version JSON des paniers au contexte
        'from_a_traiter': from_a_traiter,
        'probleme_type': probleme_type,
    }
    return render(request, 'commande/modifier.html', context)



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

@login_required
def commandes_non_affectees(request):
    """Page des commandes non affectées"""
    from .models import EtatCommande
    
    # Récupérer les IDs des commandes avec état "Non affectée" actuel
    commandes_avec_etat_non_affectee_ids = Commande.objects.filter(
        etats__enum_etat__libelle__exact='Non affectée',
        etats__date_fin__isnull=True
    ).values_list('id', flat=True)
    
    # Récupérer les IDs des commandes sans état actuel (nouvelles commandes)
    commandes_avec_etat_ids = EtatCommande.objects.filter(
        date_fin__isnull=True
    ).values_list('commande_id', flat=True).distinct()
    
    commandes_sans_etat_ids = Commande.objects.exclude(
        id__in=commandes_avec_etat_ids
    ).values_list('id', flat=True)
    
    # Combiner les IDs et récupérer les commandes
    tous_les_ids = list(commandes_avec_etat_non_affectee_ids) + list(commandes_sans_etat_ids)
    commandes_non_affectees = Commande.objects.filter(
        id__in=tous_les_ids
    ).distinct().order_by('-date_cmd')
    
    # Filtrage par recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_non_affectees = commandes_non_affectees.filter(
            Q(num_cmd__icontains=search_query) |
            Q(id_yz__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query) |
            Q(ville__nom__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(commandes_non_affectees, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    total_non_affectees = commandes_non_affectees.count()
    total_montant = sum(cmd.total_cmd for cmd in commandes_non_affectees)
    
    # Statistiques détaillées des commandes non affectées
    commandes_avec_etat_non_affectee_count = len(commandes_avec_etat_non_affectee_ids)
    commandes_sans_etat_count = len(commandes_sans_etat_ids)
    
    # Statistiques des commandes affectées pour comparaison
    total_affectees = Commande.objects.filter(
        etats__enum_etat__libelle__exact='Affectée',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    # Statistiques et listes des opérateurs
    from parametre.models import Operateur
    operateurs_confirmation_list = Operateur.objects.filter(
        type_operateur='CONFIRMATION',
        actif=True
    )
    operateurs_confirmation = operateurs_confirmation_list.count()
    
    operateurs_logistique = Operateur.objects.filter(
        type_operateur='LOGISTIQUE',
        actif=True
    ).count()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_non_affectees': total_non_affectees,
        'total_affectees': total_affectees,
        'total_montant': total_montant,
        'commandes_avec_etat_non_affectee': commandes_avec_etat_non_affectee_count,
        'commandes_nouvelles': commandes_sans_etat_count,
        'operateurs_confirmation': operateurs_confirmation,
        'operateurs_confirmation_list': operateurs_confirmation_list,
        'operateurs_logistique': operateurs_logistique,
        'page_title': 'Commandes Non Affectées',
        'page_subtitle': 'Gestion des affectations de commandes',
    }
    return render(request, 'commande/non_affectees.html', context)

@login_required
def commandes_a_traiter(request):
    """Page des commandes à traiter (doublons et erronées)"""
    from .models import EtatCommande
    
    # Récupérer les commandes avec état "Doublon" ou "Erronée" actuel
    commandes_a_traiter = Commande.objects.filter(
        Q(etats__enum_etat__libelle__exact='Doublon') | 
        Q(etats__enum_etat__libelle__exact='Erronée'),
        etats__date_fin__isnull=True
    ).distinct().order_by('-date_cmd')
    
    # Filtrage par recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_a_traiter = commandes_a_traiter.filter(
            Q(num_cmd__icontains=search_query) |
            Q(id_yz__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query) |
            Q(ville__nom__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(commandes_a_traiter, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques détaillées
    total_a_traiter = commandes_a_traiter.count()
    total_montant = sum(cmd.total_cmd for cmd in commandes_a_traiter)
    
    # Statistiques par type
    commandes_doublons = Commande.objects.filter(
        etats__enum_etat__libelle__exact='Doublon',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    commandes_erronnees = Commande.objects.filter(
        etats__enum_etat__libelle__exact='Erronée',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    # Statistiques des commandes traitées pour comparaison
    commandes_confirmees = Commande.objects.filter(
        etats__enum_etat__libelle__exact='Confirmée',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_a_traiter': total_a_traiter,
        'total_montant': total_montant,
        'commandes_doublons': commandes_doublons,
        'commandes_erronnees': commandes_erronnees,
        'commandes_confirmees': commandes_confirmees,
        'page_title': 'Commandes à Traiter',
        'page_subtitle': 'Gestion des doublons et erreurs',
    }
    return render(request, 'commande/a_traiter.html', context)

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
    import json
    
    try:
        # Parse le JSON depuis la requête
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            nouvel_etat_id = data.get('nouvel_etat_id')
            nouveau_statut = data.get('nouveau_statut')
            commentaire = data.get('commentaire', '')
        else:
            nouvel_etat_id = request.POST.get('nouvel_etat_id')
            nouveau_statut = request.POST.get('nouveau_statut')
            commentaire = request.POST.get('commentaire', '')
        
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Gérer selon que l'on reçoit un ID ou un libellé d'état
        if nouvel_etat_id:
            nouvel_etat = get_object_or_404(EnumEtatCmd, id=nouvel_etat_id)
        elif nouveau_statut:
            # Récupérer ou créer l'état par libellé
            if nouveau_statut.lower() == 'non affectée':
                nouvel_etat, created = EnumEtatCmd.objects.get_or_create(
                    libelle='Non affectée',
                    defaults={'ordre': 10, 'couleur': '#6B7280'}
                )
            else:
                try:
                    nouvel_etat = EnumEtatCmd.objects.get(libelle=nouveau_statut)
                except EnumEtatCmd.DoesNotExist:
                    return JsonResponse({'success': False, 'message': f'L\'état "{nouveau_statut}" n\'existe pas'})
        else:
            return JsonResponse({'success': False, 'message': 'Nouvel état requis'})
        
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
def desaffecter_commande_unique(request, commande_id):
    """Désaffecter une commande unique"""
    import json
    
    try:
        # Parse le JSON depuis la requête
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            motif = data.get('motif', '')
        else:
            motif = request.POST.get('motif', '')
        
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Vérifier si la commande est actuellement affectée
        etat_actuel = commande.etat_actuel
        if not etat_actuel or not etat_actuel.operateur:
            return JsonResponse({'success': False, 'message': 'Cette commande n\'est pas affectée'})
        
        # Récupérer ou créer l'état "Non affectée" 
        etat_non_affectee, created = EnumEtatCmd.objects.get_or_create(
            libelle='Non affectée',
            defaults={'ordre': 1, 'couleur': '#F59E0B'}
        )
        
        # Terminer l'état actuel
        etat_actuel.terminer_etat(request.user.operateur if hasattr(request.user, 'operateur') else None)
        
        # Créer le nouvel état "Non affectée"
        from .models import EtatCommande
        EtatCommande.objects.create(
            commande=commande,
            enum_etat=etat_non_affectee,
            operateur=request.user.operateur if hasattr(request.user, 'operateur') else None,
            commentaire=motif or "Commande désaffectée"
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Commande {commande.id_yz} désaffectée avec succès'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

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
def liste_paniers(request):
    """Vue pour afficher tous les paniers des clients avec filtrage intelligent par état"""
    
    # Récupérer tous les paniers avec leurs relations
    paniers = Panier.objects.select_related(
        'commande', 
        'commande__client', 
        'commande__ville',
        'article'
    ).order_by('-commande__date_cmd', 'commande__id_yz')
    
    # Filtrage par état de commande (priorité car c'est le filtre principal)
    etat_filter = request.GET.get('etat', '')
    if etat_filter:
        paniers = paniers.filter(
            commande__etats__enum_etat__libelle=etat_filter,
            commande__etats__date_fin__isnull=True
        )
    
    # Filtrage par recherche
    search_query = request.GET.get('search', '')
    if search_query:
        paniers = paniers.filter(
            Q(commande__id_yz__icontains=search_query) |
            Q(commande__num_cmd__icontains=search_query) |
            Q(commande__client__nom__icontains=search_query) |
            Q(commande__client__prenom__icontains=search_query) |
            Q(commande__client__numero_tel__icontains=search_query) |
            Q(article__nom__icontains=search_query) |
            Q(article__reference__icontains=search_query)
        )
    
    # Filtrage par client
    client_filter = request.GET.get('client', '')
    if client_filter:
        paniers = paniers.filter(commande__client_id=client_filter)
    
    # Filtrage par article
    article_filter = request.GET.get('article', '')
    if article_filter:
        paniers = paniers.filter(article_id=article_filter)
    
    # Pagination (réduite pour de meilleures performances)
    paginator = Paginator(paniers, 15)  # 15 paniers par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques principales
    total_paniers = paniers.count()
    total_articles = paniers.aggregate(total=Sum('quantite'))['total'] or 0
    total_valeur = paniers.aggregate(total=Sum('sous_total'))['total'] or 0
    
    # Statistiques par état pour les filtres rapides
    from .models import EtatCommande
    stats_etats = {
        'non_affectees': Panier.objects.filter(
            commande__etats__enum_etat__libelle__exact='Non affectée',
            commande__etats__date_fin__isnull=True
        ).count(),
        'affectees': Panier.objects.filter(
            commande__etats__enum_etat__libelle__exact='Affectée',
            commande__etats__date_fin__isnull=True
        ).count(),
        'confirmees': Panier.objects.filter(
            commande__etats__enum_etat__libelle__exact='Confirmée',
            commande__etats__date_fin__isnull=True
        ).count(),
        'livrees': Panier.objects.filter(
            commande__etats__enum_etat__libelle__exact='Livrée',
            commande__etats__date_fin__isnull=True
        ).count(),
        'doublons': Panier.objects.filter(
            commande__etats__enum_etat__libelle__exact='Doublon',
            commande__etats__date_fin__isnull=True
        ).count(),
        'annulees': Panier.objects.filter(
            commande__etats__enum_etat__libelle__exact='Annulée',
            commande__etats__date_fin__isnull=True
        ).count(),
    }
    
    # Données pour les filtres (optimisées)
    clients = Client.objects.all().order_by('nom', 'prenom')[:100]  # Limiter pour les performances
    articles = Article.objects.all().order_by('nom')[:100]  # Limiter pour les performances
    
    # Articles les plus commandés (seulement si pas de filtre état pour éviter la confusion)
    articles_populaires = []
    clients_actifs = []
    if not etat_filter:
        articles_populaires = paniers.values(
            'article__nom', 
            'article__reference'
        ).annotate(
            total_quantite=Sum('quantite'),
            total_commandes=Count('commande', distinct=True)
        ).order_by('-total_quantite')[:10]
        
        # Clients les plus actifs
        clients_actifs = paniers.values(
            'commande__client__nom',
            'commande__client__prenom',
            'commande__client__numero_tel'
        ).annotate(
            total_commandes=Count('commande', distinct=True),
            total_articles=Sum('quantite'),
            total_depense=Sum('sous_total')
        ).order_by('-total_commandes')[:10]
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'client_filter': client_filter,
        'article_filter': article_filter,
        'etat_filter': etat_filter,
        'total_paniers': total_paniers,
        'total_articles': total_articles,
        'total_valeur': total_valeur,
        'stats_etats': stats_etats,
        'clients': clients,
        'articles': articles,
        'articles_populaires': articles_populaires,
        'clients_actifs': clients_actifs,
        'page_title': 'Gestion des Paniers',
        'page_subtitle': f'Vue d\'ensemble des paniers {etat_filter.lower() if etat_filter else "de toutes les commandes"}',
    }
    
    return render(request, 'commande/paniers.html', context)

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

@require_POST
@login_required
def annuler_commande(request, pk):
    """Annuler une commande avec un motif obligatoire"""
    try:
        # Parse le JSON depuis la requête
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            motif = data.get('motif', '').strip()
        else:
            motif = request.POST.get('motif', '').strip()
        
        if not motif:
            return JsonResponse({'success': False, 'message': 'Le motif d\'annulation est obligatoire'})
        
        commande = get_object_or_404(Commande, pk=pk)
        
        # Vérifier que la commande n'est pas déjà annulée
        etat_actuel = commande.etat_actuel
        if etat_actuel and etat_actuel.enum_etat.libelle.lower() == 'annulée':
            return JsonResponse({'success': False, 'message': 'Cette commande est déjà annulée'})
        
        # Récupérer ou créer l'état "Annulée"
        etat_annulee, created = EnumEtatCmd.objects.get_or_create(
            libelle='Annulée',
            defaults={'ordre': 70, 'couleur': '#EF4444'}
        )
        
        # Terminer l'état actuel
        if etat_actuel:
            etat_actuel.terminer_etat(request.user.operateur if hasattr(request.user, 'operateur') else None)
        
        # Créer le nouvel état "Annulée"
        from .models import EtatCommande
        EtatCommande.objects.create(
            commande=commande,
            enum_etat=etat_annulee,
            operateur=request.user.operateur if hasattr(request.user, 'operateur') else None,
            commentaire=f"Commande annulée - Motif: {motif}"
        )
        
        # Sauvegarder le motif d'annulation dans la commande
        commande.motif_annulation = motif
        commande.save()
        
        # Créer une opération d'annulation (seulement si un opérateur existe)
        if hasattr(request.user, 'operateur') and request.user.operateur:
            from .models import Operation
            Operation.objects.create(
                commande=commande,
                type_operation='ANNULATION',
                conclusion=motif,
                operateur=request.user.operateur
            )
        
        return JsonResponse({
            'success': True, 
            'message': f'Commande {commande.id_yz} annulée avec succès. Motif: {motif}',
            'redirect_url': reverse('commande:annulees')
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# Fonction utilitaire pour automatiser les changements d'état
def repartition_automatique_commandes():
    """
    Répartit automatiquement les commandes préparées aux opérateurs logistiques
    selon un algorithme de répartition par ville/région
    """
    from .models import EnumEtatCmd, EtatCommande
    from parametre.models import Operateur
    from django.db.models import Count
    
    try:
        # Récupérer les commandes préparées non encore affectées pour la livraison
        commandes_preparees = Commande.objects.filter(
            etats__enum_etat__libelle='Préparée',
            etats__date_fin__isnull=True  # État actif
        ).exclude(
            # Exclure celles qui ont déjà un état de livraison
            etats__enum_etat__libelle__in=['En cours de livraison', 'Livrée', 'Retournée']
        ).select_related('ville', 'ville__region').distinct()
        
        if not commandes_preparees.exists():
            return 0, "Aucune commande préparée à répartir"
        
        # Récupérer les opérateurs logistiques actifs
        operateurs_logistiques = Operateur.objects.filter(
            type_operateur='LOGISTIQUE',
            actif=True
        )
        
        if not operateurs_logistiques.exists():
            return 0, "Aucun opérateur logistique actif disponible"
        
        # Créer ou récupérer l'état "En cours de livraison"
        etat_livraison, created = EnumEtatCmd.objects.get_or_create(
            libelle='En cours de livraison',
            defaults={'ordre': 60, 'couleur': '#F59E0B'}
        )
        
        commandes_affectees = 0
        
        # Algorithme de répartition simple : round-robin par opérateur
        operateurs_list = list(operateurs_logistiques)
        operateur_index = 0
        
        for commande in commandes_preparees:
            # Sélectionner l'opérateur suivant (round-robin)
            operateur_selectionne = operateurs_list[operateur_index]
            operateur_index = (operateur_index + 1) % len(operateurs_list)
            
            # Terminer l'état "Préparée"
            etat_actuel = commande.etat_actuel
            if etat_actuel and etat_actuel.enum_etat.libelle == 'Préparée':
                etat_actuel.terminer_etat()
            
            # Créer l'état "En cours de livraison" avec l'opérateur affecté
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_livraison,
                operateur=operateur_selectionne,
                commentaire=f"Affectation automatique à {operateur_selectionne.nom_complet} pour livraison"
            )
            
            commandes_affectees += 1
        
        return commandes_affectees, f"{commandes_affectees} commandes réparties automatiquement"
        
    except Exception as e:
        return 0, f"Erreur lors de la répartition automatique: {str(e)}"


def gerer_changement_etat_automatique(commande, nouvel_etat_libelle, operateur=None, commentaire=None):
    """
    Gère automatiquement le changement d'état d'une commande
    Retourne l'URL de redirection appropriée selon le nouvel état
    """
    from .models import EnumEtatCmd, EtatCommande
    try:
        # Récupérer ou créer l'état cible
        if nouvel_etat_libelle.lower() == 'non affectée':
            nouvel_etat, created = EnumEtatCmd.objects.get_or_create(
                libelle='Non affectée',
                defaults={'ordre': 10, 'couleur': '#6B7280'}
            )
            redirect_url = reverse('commande:non_affectees')
        elif nouvel_etat_libelle.lower() == 'annulée':
            nouvel_etat, created = EnumEtatCmd.objects.get_or_create(
                libelle='Annulée',
                defaults={'ordre': 70, 'couleur': '#EF4444'}
            )
            redirect_url = reverse('commande:annulees')
        elif nouvel_etat_libelle == 'En cours de livraison':
            nouvel_etat, created = EnumEtatCmd.objects.get_or_create(
                libelle='En cours de livraison',
                defaults={'ordre': 60, 'couleur': '#F59E0B'}
            )
            redirect_url = None
        elif nouvel_etat_libelle == 'Préparée':
            # Cas spécial : quand une commande devient "Préparée", déclencher la répartition automatique
            nouvel_etat, created = EnumEtatCmd.objects.get_or_create(
                libelle='Préparée',
                defaults={'ordre': 50, 'couleur': '#10B981'}
            )
            redirect_url = None
        else:
            # Pour les autres états, essayer de les récupérer ou les créer
            try:
                nouvel_etat = EnumEtatCmd.objects.get(libelle=nouvel_etat_libelle)
                redirect_url = None
            except EnumEtatCmd.DoesNotExist:
                # Créer l'état s'il n'existe pas avec des valeurs par défaut
                nouvel_etat, created = EnumEtatCmd.objects.get_or_create(
                    libelle=nouvel_etat_libelle,
                    defaults={'ordre': 50, 'couleur': '#6366F1'}
                )
                redirect_url = None
        
        # Terminer l'état actuel
        etat_actuel = commande.etat_actuel
        if etat_actuel:
            etat_actuel.terminer_etat(operateur)
        
        # Créer le nouvel état
        from .models import EtatCommande
        EtatCommande.objects.create(
            commande=commande,
            enum_etat=nouvel_etat,
            operateur=operateur,
            commentaire=commentaire or f"Changement automatique vers '{nouvel_etat.libelle}'"
        )
        
        # Si la commande devient "Préparée", déclencher la répartition automatique après un délai
        if nouvel_etat_libelle == 'Préparée':
            # Utiliser une tâche asynchrone ou un délai pour éviter les conflits
            from django.utils import timezone
            from datetime import timedelta
            import threading
            
            def repartir_apres_delai():
                import time
                time.sleep(2)  # Attendre 2 secondes pour que l'état soit bien enregistré
                repartition_automatique_commandes()
            
            # Lancer la répartition dans un thread séparé
            thread = threading.Thread(target=repartir_apres_delai)
            thread.daemon = True
            thread.start()
        
        return redirect_url, None
        
    except Exception as e:
        return None, str(e)



@login_required
def statistiques_motifs_annulation(request):
    """Vue pour afficher les statistiques des motifs d'annulation"""
    from django.db.models import Count
    
    # Récupérer les commandes annulées avec leurs motifs
    commandes_annulees = Commande.objects.filter(
        etats__enum_etat__libelle__icontains='Annulée',
        etats__date_fin__isnull=True
    ).distinct()
    
    # Statistiques par motif
    motifs_stats = {}
    motifs_predefinis = [
        'Doublon confirmé',
        'Numéro tel incorrect', 
        'Numéro de téléphone injoignable',
        'Client non intéressé',
        'Adresse erronée',
        'Erreur de saisie'
    ]
    
    # Initialiser les compteurs
    for motif in motifs_predefinis:
        motifs_stats[motif] = 0
    motifs_stats['Autres'] = 0
    motifs_stats['Non spécifié'] = 0
    
    # Compter les motifs
    for commande in commandes_annulees:
        motif = commande.motif_annulation
        if not motif:
            motifs_stats['Non spécifié'] += 1
        elif motif in motifs_predefinis:
            motifs_stats[motif] += 1
        else:
            motifs_stats['Autres'] += 1
    
    # Calculer les pourcentages
    total_annulees = commandes_annulees.count()
    motifs_pourcentages = {}
    if total_annulees > 0:
        for motif, count in motifs_stats.items():
            motifs_pourcentages[motif] = round((count / total_annulees) * 100, 1)
    
    context = {
        'motifs_stats': motifs_stats,
        'motifs_pourcentages': motifs_pourcentages,
        'total_annulees': total_annulees,
        'page_title': 'Statistiques des Motifs d\'Annulation',
    }
    
    return render(request, 'commande/statistiques_motifs.html', context)

@login_required
def commandes_confirmees(request):
    """Page des commandes confirmées"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Récupérer toutes les commandes confirmées
    commandes_confirmees = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats', 'operations').distinct()
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_confirmees = commandes_confirmees.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query) |
            Q(etats__operateur__nom__icontains=search_query) |
            Q(etats__operateur__prenom__icontains=search_query)
        ).distinct()
    
    # Tri par date de confirmation (plus récentes en premier)
    commandes_confirmees = commandes_confirmees.order_by('-etats__date_debut')
    
    # Pagination
    paginator = Paginator(commandes_confirmees, 25)  # 25 commandes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)
    
    # Confirmées aujourd'hui
    confirmees_aujourd_hui = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True,
        etats__date_debut__date=today
    ).distinct().count()
    
    # Confirmées cette semaine
    confirmees_semaine = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True,
        etats__date_debut__date__gte=week_start
    ).distinct().count()
    
    # Confirmées ce mois
    confirmees_mois = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True,
        etats__date_debut__date__gte=month_start
    ).distinct().count()
    
    # Total des commandes confirmées
    total_confirmees = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    # Montant total des commandes confirmées
    montant_total = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True
    ).aggregate(total=Sum('total_cmd'))['total'] or 0
    
    # Récupérer les opérateurs de préparation actifs
    operateurs_preparation = Operateur.objects.filter(
        type_operateur='PREPARATION',
        actif=True
    ).order_by('nom', 'prenom')
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_confirmees': total_confirmees,
        'confirmees_aujourd_hui': confirmees_aujourd_hui,
        'confirmees_semaine': confirmees_semaine,
        'confirmees_mois': confirmees_mois,
        'montant_total': montant_total,
        'operateurs_preparation': operateurs_preparation,
        'page_title': 'Commandes Confirmées',
        'page_subtitle': 'Liste des commandes validées prêtes pour la préparation',
    }
    
    return render(request, 'commande/confirmees.html', context)

@login_required
def commandes_preparees(request):
    """Page des commandes préparées"""
    from django.utils import timezone
    from datetime import timedelta

    # Une commande est "préparée" si elle a un état "Préparée" actif
    # ET qu'elle n'a AUCUN état lié à la livraison.
    base_commandes_preparees = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_fin__isnull=True
    ).exclude(
        etats__enum_etat__libelle__in=['En cours de livraison', 'Livrée', 'Retournée']
    ).distinct()

    # Statistiques (calculées avant le filtrage par recherche)
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # Le filtre `etats__date_fin__date` peut causer des doublons si une commande a plusieurs états "En préparation" terminés le même jour.
    # Bien que ce soit un cas rare, l'utilisation de `distinct()` sur la clé primaire de la commande est une bonne pratique.
    preparees_aujourd_hui = base_commandes_preparees.filter(etats__date_fin__date=today).count()
    preparees_semaine = base_commandes_preparees.filter(etats__date_fin__date__gte=start_of_week).count()
    preparees_mois = base_commandes_preparees.filter(etats__date_fin__date__gte=start_of_month).count()
    
    total_preparees = base_commandes_preparees.count()
    total_montant = base_commandes_preparees.aggregate(total=Sum('total_cmd'))['total'] or 0

    # La queryset pour la liste affichée, avec l'optimisation `select_related`
    commandes_preparees = base_commandes_preparees.select_related('client', 'ville', 'ville__region').order_by('-etats__date_fin')
    
    # Filtrage par recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_preparees = commandes_preparees.filter(
            Q(num_cmd__icontains=search_query) |
            Q(id_yz__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(commandes_preparees, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Récupérer les opérateurs de livraison ou logistiques actifs pour l'affectation
    operateurs_livraison = Operateur.objects.filter(
        Q(type_operateur='LIVRAISON') | Q(type_operateur='LOGISTIQUE'),
        actif=True
    )
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_commandes': total_preparees,
        'total_montant': total_montant,
        'preparees_aujourd_hui': preparees_aujourd_hui,
        'preparees_semaine': preparees_semaine,
        'preparees_mois': preparees_mois,
        'operateurs_livraison': operateurs_livraison,
        'page_title': 'Commandes Préparées',
        'page_subtitle': 'Liste des commandes prêtes pour la livraison',
    }
    return render(request, 'commande/preparees.html', context)

@login_required
def suivi_confirmations(request):
    """Vue pour le suivi en temps réel des activités de confirmation des opérateurs"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Récupérer toutes les commandes confirmées par les opérateurs
    commandes_confirmees = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats', 'operations').distinct()
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_confirmees = commandes_confirmees.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query) |
            Q(etats__operateur__nom__icontains=search_query) |
            Q(etats__operateur__prenom__icontains=search_query)
        ).distinct()
    
    # Tri par date de confirmation (plus récentes en premier)
    commandes_confirmees = commandes_confirmees.order_by('-etats__date_debut')
    
    # Pagination
    paginator = Paginator(commandes_confirmees, 25)  # 25 commandes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    this_week = today - timedelta(days=7)
    
    # Compter par période
    confirmees_aujourd_hui = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True,
        etats__date_debut__date=today
    ).distinct().count()
    
    confirmees_hier = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True,
        etats__date_debut__date=yesterday
    ).distinct().count()
    
    confirmees_semaine = Commande.objects.filter(
        etats__enum_etat__libelle='Confirmée',
        etats__date_fin__isnull=True,
        etats__date_debut__date__gte=this_week
    ).distinct().count()
    
    # Compter les commandes en attente (pour information)
    en_attente_count = Commande.objects.filter(
        etats__enum_etat__libelle__in=['Affectée', 'En cours de confirmation'],
        etats__date_fin__isnull=True
    ).distinct().count()
    
    # Montant total des commandes confirmées
    montant_total = commandes_confirmees.aggregate(total=Sum('total_cmd'))['total'] or 0
    
    # Récupérer les opérateurs de préparation actifs
    operateurs_preparation = Operateur.objects.filter(
        type_operateur='PREPARATION',
        actif=True
    ).order_by('nom', 'prenom')
    
    # Récupérer les commandes par opérateur
    commandes_par_operateur = {}
    for commande in commandes_confirmees:
        operateur = commande.etats.filter(enum_etat__libelle='Confirmée').first().operateur
        if operateur:
            if operateur.nom not in commandes_par_operateur:
                commandes_par_operateur[operateur.nom] = []
            commandes_par_operateur[operateur.nom].append(commande)
    
    # Récupérer les jours de vérification
    jours_verification = {
        'aujourd_hui': today,
        'hier': yesterday,
        'semaine': this_week
    }
    
    context = {
        'commandes_confirmees': commandes_confirmees,
        'page_obj': page_obj,
        'search_query': search_query,
        'confirmees_aujourd_hui': confirmees_aujourd_hui,
        'confirmees_hier': confirmees_hier,
        'confirmees_semaine': confirmees_semaine,
        'en_attente_count': en_attente_count,
        'montant_total': montant_total,
        'operateurs_preparation': operateurs_preparation,
        'commandes_par_operateur': sorted(commandes_par_operateur.items()),
        'jours_verification': jours_verification,
    }
    
    return render(request, 'commande/suivi_confirmations.html', context)

@require_POST
@login_required
def affecter_preparation(request, commande_id):
    """Affecter une commande à un opérateur de préparation."""
    if request.method == 'POST':
        try:
            # Vérifier que l'utilisateur est admin
            try:
                operateur_admin = Operateur.objects.get(user=request.user, type_operateur='ADMIN')
            except Operateur.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Accès non autorisé.'})
            
            # Récupérer les données de la requête
            data = json.loads(request.body)
            operateur_id = data.get('operateur_id')
            commentaire = data.get('commentaire', '')
            
            if not operateur_id:
                return JsonResponse({'success': False, 'message': 'Veuillez sélectionner un opérateur.'})
            
            # Récupérer la commande et l'opérateur
            commande = get_object_or_404(Commande, id=commande_id)
            operateur_preparation = get_object_or_404(Operateur, id=operateur_id, type_operateur='PREPARATION', actif=True)
            
            # Vérifier que la commande est confirmée
            etat_actuel = commande.etat_actuel
            if not etat_actuel or etat_actuel.enum_etat.libelle != 'Confirmée':
                return JsonResponse({'success': False, 'message': 'Cette commande n\'est pas confirmée.'})
            
            # Vérifier si un état "À imprimer" existe
            try:
                etat_preparation, created = EnumEtatCmd.objects.get_or_create(
                    libelle='À imprimer',
                    defaults={'ordre': 35, 'couleur': '#F59E0B'}
                )
            except Exception as e:
                return JsonResponse({'success': False, 'message': f'Erreur lors de la récupération de l\'état: {str(e)}'})
            
            # Utiliser une transaction pour s'assurer de la cohérence
            with transaction.atomic():
                # Terminer l'état actuel (Confirmée)
                etat_actuel.terminer_etat(operateur=operateur_admin)
                
                # Créer le nouvel état "À imprimer"
                from .models import EtatCommande
                nouvel_etat = EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=etat_preparation,
                    operateur=operateur_preparation,
                    commentaire=f"Affectée à la préparation par {operateur_admin.nom_complet}. {commentaire}".strip(),
                    date_debut=timezone.now()
                )
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Commande {commande.id_yz} affectée avec succès à {operateur_preparation.nom_complet} pour impression puis préparation.'
                })
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Une erreur est survenue: {str(e)}'})

@require_POST
@login_required
def affecter_livraison(request, commande_id):
    """Affecte une commande préparée à un opérateur de livraison."""
    try:
        data = json.loads(request.body)
        operateur_id = data.get('operateur_id')
        commentaire = data.get('commentaire', '')
        
        if not operateur_id:
            return JsonResponse({'success': False, 'message': 'ID de l\'opérateur manquant.'}, status=400)
        
        commande = get_object_or_404(Commande, id=commande_id)
        operateur = get_object_or_404(
            Operateur, 
            id=operateur_id, 
            type_operateur__in=['LIVRAISON', 'LOGISTIQUE']
        )
        
        # Vérifier si la commande a un état "Préparée" actif.
        # C'est plus robuste que de se fier à la propriété `etat_actuel`.
        est_prete = commande.etats.filter(enum_etat__libelle='Préparée', date_fin__isnull=True).exists()
        
        if not est_prete:
            return JsonResponse({'success': False, 'message': f'La commande {commande.id_yz} n\'est pas prête pour la livraison.'}, status=400)

        # Utiliser la fonction centralisée pour changer l'état
        gerer_changement_etat_automatique(
            commande, 
            'En cours de livraison', 
            operateur=operateur,
            commentaire=commentaire
        )
        
        messages.success(request, f'La commande {commande.id_yz} a été affectée à {operateur.nom_complet} pour la livraison.')
        return JsonResponse({'success': True, 'message': 'Affectation réussie.'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Données JSON invalides.'}, status=400)
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Opérateur de livraison non trouvé.'}, status=404)
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande non trouvée.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Une erreur est survenue: {str(e)}'}, status=500)

@require_POST
@login_required
def affecter_livraison_multiple(request):
    """Affecte plusieurs commandes préparées à un opérateur de livraison."""
    try:
        data = json.loads(request.body)
        commandes_ids = data.get('commandes_ids', [])
        operateur_id = data.get('operateur_id')
        commentaire = data.get('commentaire', '')

        if not commandes_ids or not operateur_id:
            return JsonResponse({'success': False, 'message': 'Données manquantes.'}, status=400)

        operateur = get_object_or_404(
            Operateur, 
            id=operateur_id, 
            type_operateur__in=['LIVRAISON', 'LOGISTIQUE']
        )
        
        commandes_affectees_yz = []
        commandes_erreurs_yz = []

        with transaction.atomic():
            commandes_a_traiter = Commande.objects.filter(id__in=commandes_ids)
            for commande in commandes_a_traiter:
                try:
                    # Vérifier si la commande a un état "Préparée" actif.
                    est_prete = commande.etats.filter(enum_etat__libelle='Préparée', date_fin__isnull=True).exists()

                    if not est_prete:
                        commandes_erreurs_yz.append(f"{commande.id_yz} (non prête)")
                        continue

                    gerer_changement_etat_automatique(
                        commande, 
                        'En cours de livraison', 
                        operateur=operateur,
                        commentaire=commentaire
                    )
                    commandes_affectees_yz.append(commande.id) # We'll use the command ID
                except Exception as e:
                    commandes_erreurs_yz.append(f"{commande.id_yz} ({str(e)})")

        message = f"{len(commandes_affectees_yz)} commande(s) affectée(s) avec succès."
        if commandes_erreurs_yz:
            message += f" Erreurs sur les commandes : {', '.join(commandes_erreurs_yz)}."
        
        return JsonResponse({
            'success': len(commandes_erreurs_yz) == 0, 
            'message': message,
            'commandes_affectees_ids': commandes_affectees_yz
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@require_POST
@login_required
def affecter_preparation_multiple(request):
    """Affecte plusieurs commandes confirmées à un opérateur de préparation."""
    try:
        # Vérifier que l'utilisateur est admin
        try:
            operateur_admin = Operateur.objects.get(user=request.user, type_operateur='ADMIN')
        except Operateur.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Accès non autorisé.'})
        
        data = json.loads(request.body)
        commandes_ids = data.get('commande_ids', [])
        operateur_id = data.get('operateur_id')
        commentaire = data.get('commentaire', '')

        if not commandes_ids or not operateur_id:
            return JsonResponse({'success': False, 'message': 'Données manquantes.'}, status=400)

        operateur_preparation = get_object_or_404(
            Operateur, 
            id=operateur_id, 
            type_operateur='PREPARATION',
            actif=True
        )
        
        commandes_affectees_yz = []
        commandes_erreurs_yz = []

        # Vérifier si un état "À imprimer" existe
        try:
            etat_preparation, created = EnumEtatCmd.objects.get_or_create(
                libelle='À imprimer',
                defaults={'ordre': 35, 'couleur': '#F59E0B'}
            )
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur lors de la récupération de l\'état: {str(e)}'})

        with transaction.atomic():
            commandes_a_traiter = Commande.objects.filter(id__in=commandes_ids)
            for commande in commandes_a_traiter:
                try:
                    # Vérifier que la commande est confirmée
                    etat_actuel = commande.etat_actuel
                    if not etat_actuel or etat_actuel.enum_etat.libelle != 'Confirmée':
                        commandes_erreurs_yz.append(f"{commande.id_yz} (non confirmée)")
                        continue

                    # Terminer l'état actuel (Confirmée)
                    etat_actuel.terminer_etat(operateur=operateur_admin)
                    
                    # Créer le nouvel état "À imprimer"
                    from .models import EtatCommande
                    EtatCommande.objects.create(
                        commande=commande,
                        enum_etat=etat_preparation,
                        operateur=operateur_preparation,
                        commentaire=f"Affectée à la préparation par {operateur_admin.nom_complet}. {commentaire}".strip(),
                        date_debut=timezone.now()
                    )
                    
                    commandes_affectees_yz.append(commande.id_yz)
                except Exception as e:
                    commandes_erreurs_yz.append(f"{commande.id_yz} ({str(e)})")

        message = f"{len(commandes_affectees_yz)} commande(s) affectée(s) avec succès à {operateur_preparation.nom_complet} pour impression puis préparation."
        if commandes_erreurs_yz:
            message += f" Erreurs sur les commandes : {', '.join(commandes_erreurs_yz)}."
        
        return JsonResponse({
            'success': len(commandes_erreurs_yz) == 0, 
            'message': message,
            'commandes_affectees_ids': commandes_affectees_yz
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def api_panier_commande(request, commande_id):
    """API pour récupérer le contenu du panier d'une commande"""
    from django.http import JsonResponse
    from parametre.models import Operateur
    
    # Vérifier que l'utilisateur est autorisé (admin ou opérateur)
    try:
        operateur = Operateur.objects.get(user=request.user)
    except Operateur.DoesNotExist:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    if request.method == 'GET':
        try:
            # Récupérer la commande avec ses paniers
            commande = get_object_or_404(
                Commande.objects.select_related('client', 'ville').prefetch_related(
                    'paniers__article'
                ),
                pk=commande_id
            )
            
            # Préparer les données pour le template
            paniers = commande.paniers.all()
            total_articles = sum(panier.quantite for panier in paniers)
            total_montant = sum(panier.sous_total for panier in paniers)
            frais_livraison = commande.ville.frais_livraison if commande.ville else 0
            # Convertir explicitement en float pour éviter l'erreur Decimal + float
            total_final = float(total_montant) + float(frais_livraison)
            
            # Construire la liste des articles pour le JSON
            articles_data = []
            for panier in paniers:
                articles_data.append({
                    'nom': str(panier.article.nom),
                    'reference': str(panier.article.reference) if panier.article.reference else 'N/A',
                    'description': str(panier.article.description) if panier.article.description else '',
                    'prix_unitaire': float(panier.article.prix_unitaire),
                    'quantite': panier.quantite,
                    'sous_total': float(panier.sous_total)
                })
            
            return JsonResponse({
                'success': True,
                'commande': {
                    'id_yz': commande.id_yz,
                    'client_nom': str(commande.client.get_full_name),
                    'total_articles': total_articles,
                    'total_montant': float(total_montant),
                    'frais_livraison': float(frais_livraison),
                    'total_final': float(total_final)
                },
                'articles': articles_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la récupération du panier: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
def suivi_preparations(request):
    """Vue pour le suivi en temps réel des activités de préparation des commandes"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Récupérer toutes les commandes en préparation
    commandes_preparation = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats', 'operations', 'paniers__article').distinct()
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_preparation = commandes_preparation.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query) |
            Q(etats__operateur__nom__icontains=search_query) |
            Q(etats__operateur__prenom__icontains=search_query)
        ).distinct()
    
    # Tri par date de début de préparation (plus récentes en premier)
    commandes_preparation = commandes_preparation.order_by('-etats__date_debut')
    
    # Pagination
    paginator = Paginator(commandes_preparation, 25)  # 25 commandes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    this_week = today - timedelta(days=7)
    
    # Compter par période et par état
    a_imprimer_count = Commande.objects.filter(
        etats__enum_etat__libelle='À imprimer',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    en_preparation_count = Commande.objects.filter(
        etats__enum_etat__libelle='En préparation',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    preparees_aujourd_hui = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_debut__date=today
    ).distinct().count()
    
    preparees_semaine = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_debut__date__gte=this_week
    ).distinct().count()
    
    # Montant total des commandes en préparation
    montant_total = commandes_preparation.aggregate(total=Sum('total_cmd'))['total'] or 0
    
    # Récupérer les commandes par opérateur de préparation
    commandes_par_operateur = {}
    for commande in commandes_preparation:
        etat_actuel = commande.etats.filter(
            enum_etat__libelle__in=['À imprimer', 'En préparation'],
            date_fin__isnull=True
        ).first()
        
        if etat_actuel and etat_actuel.operateur:
            operateur_nom = f"{etat_actuel.operateur.prenom} {etat_actuel.operateur.nom}"
            if operateur_nom not in commandes_par_operateur:
                commandes_par_operateur[operateur_nom] = []
            commandes_par_operateur[operateur_nom].append(commande)
    
    context = {
        'commandes_preparation': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'a_imprimer_count': a_imprimer_count,
        'en_preparation_count': en_preparation_count,
        'preparees_aujourd_hui': preparees_aujourd_hui,
        'preparees_semaine': preparees_semaine,
        'montant_total': montant_total,
        'commandes_par_operateur': sorted(commandes_par_operateur.items()),
    }
    
    return render(request, 'commande/suivi_preparations.html', context)

@login_required
def commandes_livrees(request):
    """Vue pour afficher les commandes livrées avec pagination, recherche et statistiques"""
    from django.utils import timezone
    from datetime import datetime, timedelta
    
    # Récupérer toutes les commandes livrées
    commandes_livrees = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats', 'operations').distinct()
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_livrees = commandes_livrees.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query) |
            Q(etats__operateur__nom__icontains=search_query) |
            Q(etats__operateur__prenom__icontains=search_query) |
            Q(ville__nom__icontains=search_query) |
            Q(ville__region__nom_region__icontains=search_query)
        ).distinct()
    
    # Tri par date de livraison (plus récentes en premier)
    commandes_livrees = commandes_livrees.order_by('-etats__date_debut')
    
    # Pagination
    paginator = Paginator(commandes_livrees, 25)  # 25 commandes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    this_week = today - timedelta(days=7)
    this_month = today - timedelta(days=30)
    
    # Compter par période
    livrees_aujourd_hui = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée',
        etats__date_fin__isnull=True,
        etats__date_debut__date=today
    ).distinct().count()
    
    livrees_hier = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée',
        etats__date_fin__isnull=True,
        etats__date_debut__date=yesterday
    ).distinct().count()
    
    livrees_semaine = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée',
        etats__date_fin__isnull=True,
        etats__date_debut__date__gte=this_week
    ).distinct().count()
    
    livrees_mois = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée',
        etats__date_fin__isnull=True,
        etats__date_debut__date__gte=this_month
    ).distinct().count()
    
    # Montant total des commandes livrées
    montant_total = commandes_livrees.aggregate(total=Sum('total_cmd'))['total'] or 0
    
    # Total des commandes livrées
    total_livrees = commandes_livrees.count()
    
    # Récupérer les commandes par opérateur de livraison
    commandes_par_operateur = {}
    for commande in commandes_livrees:
        etat_livraison = commande.etats.filter(
            enum_etat__libelle='Livrée',
            date_fin__isnull=True
        ).first()
        
        if etat_livraison and etat_livraison.operateur:
            operateur_nom = f"{etat_livraison.operateur.prenom} {etat_livraison.operateur.nom}"
            if operateur_nom not in commandes_par_operateur:
                commandes_par_operateur[operateur_nom] = []
            commandes_par_operateur[operateur_nom].append(commande)
    
    context = {
        'commandes_livrees': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'livrees_aujourd_hui': livrees_aujourd_hui,
        'livrees_hier': livrees_hier,
        'livrees_semaine': livrees_semaine,
        'livrees_mois': livrees_mois,
        'total_livrees': total_livrees,
        'montant_total': montant_total,
        'commandes_par_operateur': sorted(commandes_par_operateur.items()),
        'page_title': 'Commandes Livrées',
        'page_subtitle': 'Suivi des commandes livrées avec succès'
    }
    
    return render(request, 'commande/livrees.html', context)
