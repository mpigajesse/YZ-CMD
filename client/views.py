from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, OuterRef, Subquery
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from .models import Client
from parametre.models import Ville, Region
from commande.models import Commande

# Create your views here.

@login_required
def liste_clients(request):
    from synchronisation.models import SyncLog
    
    # Sous-requête pour trouver la 'ville_init' de la dernière commande de chaque client
    latest_commande_ville_init = Commande.objects.filter(
        client=OuterRef('pk')
    ).order_by('-date_creation').values('ville_init')[:1]

    # Annoter les clients avec la ville de leur dernière commande
    clients = Client.objects.annotate(
        nombre_commandes=Count('commandes', distinct=True),
        derniere_ville_init=Subquery(latest_commande_ville_init)
    ).all()
    search_query = request.GET.get('search', '')

    # Filtres
    ville_filter = request.GET.get('ville_filter', '')
    ville_init_filter = request.GET.get('ville_init_filter', '')
    region_filter = request.GET.get('region_filter', '')

    if search_query:
        # Recherche flexible et variée
        search_terms = search_query.strip().split()
        
        # Construction de la requête de recherche
        search_conditions = Q()
        
        # Vérifier si la recherche correspond exactement à une ville_init
        # Si oui, on filtre directement sur derniere_ville_init pour être cohérent avec le filtre
        exact_ville_init_match = Commande.objects.filter(
            ville_init__iexact=search_query
        ).exists()
        
        if exact_ville_init_match:
            # Si la recherche correspond exactement à une ville_init, on filtre directement
            search_conditions = Q(derniere_ville_init__iexact=search_query)
        else:
            # Sinon, on utilise la recherche normale par termes
            term_conditions = Q()
            for term in search_terms:
                term_conditions |= (
                # Recherche dans les données du client
                Q(nom__icontains=term) |
                Q(prenom__icontains=term) |
                Q(numero_tel__icontains=term) |
                Q(email__icontains=term) |
                Q(adresse__icontains=term) |
                Q(id__icontains=term) |  # Recherche par ID client
                    Q(derniere_ville_init__icontains=term) |
                
                # Recherche dans les commandes associées
                Q(commandes__id_yz__icontains=term) |
                Q(commandes__num_cmd__icontains=term) |
                Q(commandes__total_cmd__icontains=term) |
                    
                
                # Recherche dans les villes des commandes
                Q(commandes__ville__nom__icontains=term) |
                Q(commandes__ville_init__icontains=term) |
                    Q(commandes__ville__region__nom_region__icontains=term) |
                
                # Recherche dans les états des commandes
                Q(commandes__etats__enum_etat__libelle__icontains=term) |
                
                # Recherche dans les produits des commandes
                Q(commandes__produit_init__icontains=term)
            )
            search_conditions &= term_conditions
        
        # Recherche globale si un seul terme (pour retrouver "Dupont Jean" avec "Jean Dupont")
        if not exact_ville_init_match and len(search_terms) == 1:
            global_term = search_query.strip()
            search_conditions |= (
                Q(nom__icontains=global_term) |
                Q(prenom__icontains=global_term) |
                Q(numero_tel__icontains=global_term) |
                Q(email__icontains=global_term) |
                Q(adresse__icontains=global_term) |
                Q(commandes__id_yz__icontains=global_term) |
                Q(commandes__num_cmd__icontains=global_term) |
                Q(commandes__ville__nom__icontains=global_term) |
                Q(commandes__ville_init__icontains=global_term) |
                Q(commandes__etats__enum_etat__libelle__icontains=global_term)
            )
        
        clients = clients.filter(search_conditions).distinct()

    # Filtres spécifiques - indépendants les uns des autres
    if ville_filter:
        try:
            # On récupère l'objet Ville pour pouvoir utiliser son nom dans la recherche
            ville_obj = Ville.objects.get(id=ville_filter)
            
            # Récupérer les IDs des clients qui ont au moins une commande avec cette ville
            client_ids_with_ville = Commande.objects.filter(
                Q(ville_id=ville_filter) |
                Q(ville_init__iexact=ville_obj.nom)
            ).values_list('client_id', flat=True).distinct()
            
            # Filtrer les clients par ces IDs
            clients = clients.filter(id__in=client_ids_with_ville)
        except Ville.DoesNotExist:
            # Si l'ID de la ville fourni n'est pas valide, on ignore simplement le filtre
            pass
    
    # Filtre par ville initiale - indépendant des autres filtres
    if ville_init_filter:
        # Récupérer les IDs des clients qui ont au moins une commande avec cette ville_init
        client_ids_with_ville_init = Commande.objects.filter(
            ville_init__iexact=ville_init_filter
        ).values_list('client_id', flat=True).distinct()
        
        # Filtrer les clients par ces IDs
        clients = clients.filter(id__in=client_ids_with_ville_init)
        
        # Assurons-nous également que la dernière ville_init correspond au filtre
        # pour que l'affichage soit cohérent avec la valeur affichée dans le tableau
        clients = clients.filter(derniere_ville_init=ville_init_filter)
    
    if region_filter:
        # Récupérer les IDs des clients qui ont au moins une commande dans cette région
        client_ids_with_region = Commande.objects.filter(
            ville__region_id=region_filter
        ).values_list('client_id', flat=True).distinct()
        
        # Filtrer les clients par ces IDs
        clients = clients.filter(id__in=client_ids_with_region)
    
    # Triez par date de création par défaut
    clients = clients.order_by('-date_creation')

    paginator = Paginator(clients, 10)  # 10 clients par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Statistiques vérifiées
    total_clients = Client.objects.count()
    clients_avec_commandes = Client.objects.filter(commandes__isnull=False).distinct().count()
    clients_sans_commandes = total_clients - clients_avec_commandes
    
    # NOUVELLES STATISTIQUES POUR LES COMMANDES
    # Compter les clients distincts avec des commandes erronées (état actuel)
    clients_avec_cmd_erronees = Client.objects.filter(
        commandes__etats__enum_etat__libelle__iexact='Erronée',
        commandes__etats__date_fin__isnull=True
    ).distinct().count()

    # Compter les clients distincts avec des commandes doublons (état actuel)
    clients_avec_cmd_doublons = Client.objects.filter(
        commandes__etats__enum_etat__libelle__iexact='Doublon',
        commandes__etats__date_fin__isnull=True
    ).distinct().count()

    # Vérifier les doublons potentiels de clients (basé sur le numéro de tel)
    doublons_detectes = Client.objects.values('numero_tel').annotate(
        count=Count('id')
    ).filter(count__gt=1).count()
    
    # Dernière synchronisation
    derniere_sync = SyncLog.objects.filter(status__in=['success', 'partial']).first()
    
    # Récupérer les listes pour les filtres
    villes = Ville.objects.all().order_by('nom')
    regions = Region.objects.all().order_by('nom_region')
    
    # Récupérer les villes uniques du champ ville_init pour le filtre
    villes_init = Commande.objects.exclude(ville_init__isnull=True).exclude(ville_init='').values_list('ville_init', flat=True).distinct().order_by('ville_init')
    
    # Calculer les pourcentages
    pourcentage_avec_commandes = round((clients_avec_commandes / total_clients * 100), 1) if total_clients > 0 else 0
    pourcentage_sans_commandes = round((clients_sans_commandes / total_clients * 100), 1) if total_clients > 0 else 0

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'ville_filter': ville_filter,
        'ville_init_filter': ville_init_filter,
        'region_filter': region_filter,
        'villes': villes,
        'villes_init': villes_init,
        'regions': regions,
        'total_clients': total_clients,
        'clients_avec_commandes': clients_avec_commandes,
        'clients_sans_commandes': clients_sans_commandes,
        'doublons_detectes': doublons_detectes,
        'clients_avec_cmd_erronees': clients_avec_cmd_erronees,
        'clients_avec_cmd_doublons': clients_avec_cmd_doublons,
        'derniere_sync': derniere_sync,
        'pourcentage_avec_commandes': pourcentage_avec_commandes,
        'pourcentage_sans_commandes': pourcentage_sans_commandes,
    }
    return render(request, 'client/liste_clients.html', context)

@login_required
def detail_client(request, pk):
    from django.db.models import Q, Count
    from django.core.paginator import Paginator
    
    client = get_object_or_404(Client, pk=pk)
    
    # Récupérer le terme de recherche
    search_query = request.GET.get('search', '')
    
    # Récupérer toutes les commandes du client
    commandes_queryset = client.commandes.all().order_by('-date_cmd', '-date_creation')
    
    # Appliquer la recherche si nécessaire
    if search_query:
        commandes_queryset = commandes_queryset.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(ville__nom__icontains=search_query) |
            Q(ville_init__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(commandes_queryset, 15)  # 15 commandes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculer les statistiques sur toutes les commandes du client (pas seulement la page actuelle)
    toutes_commandes = client.commandes.all()
    total_commandes = toutes_commandes.count()
    
    # Commandes confirmées
    commandes_confirmees = toutes_commandes.filter(
        etats__enum_etat__libelle__icontains='confirmée'
    ).distinct().count()
    
    # Commandes annulées
    commandes_annulees = toutes_commandes.filter(
        etats__enum_etat__libelle__icontains='annulée'
    ).distinct().count()
    
    # Montant total
    montant_total = sum(commande.total_cmd for commande in toutes_commandes)
    
    # Statistiques par état (toutes les commandes, même sans état défini)
    etats_stats = toutes_commandes.values(
        'etats__enum_etat__libelle',
        'etats__enum_etat__couleur'
    ).annotate(
        count=Count('id', distinct=True)
    ).filter(
        etats__date_fin__isnull=True  # État actuel seulement
    ).order_by('-count')
    
    # Ajouter les commandes sans état défini aux statistiques
    commandes_sans_etat = toutes_commandes.filter(etats__isnull=True).count()
    if commandes_sans_etat > 0:
        etats_stats = list(etats_stats) + [{
            'etats__enum_etat__libelle': 'Non défini',
            'etats__enum_etat__couleur': '#6B7280',
            'count': commandes_sans_etat
        }]
    
    context = {
        'client': client,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_commandes': total_commandes,
        'commandes_confirmees': commandes_confirmees,
        'commandes_annulees': commandes_annulees,
        'montant_total': montant_total,
        'etats_stats': etats_stats,
    }
    return render(request, 'client/detail_client.html', context)

@login_required
def creer_client(request):
    if request.method == 'POST':
        numero_tel = request.POST.get('numero_tel')
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        adresse = request.POST.get('adresse')

        if not numero_tel:
            messages.error(request, "Le numéro de téléphone est obligatoire.")
        elif Client.objects.filter(numero_tel=numero_tel).exists():
            messages.error(request, f"Un client avec le numéro {numero_tel} existe déjà.")
        else:
            Client.objects.create(
                numero_tel=numero_tel,
                nom=nom,
                prenom=prenom,
                email=email,
                adresse=adresse
            )
            messages.success(request, "Client créé avec succès.")
            return redirect('client:liste')

    return render(request, 'client/creer_client.html')

@login_required
def modifier_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.numero_tel = request.POST.get('numero_tel')
        client.nom = request.POST.get('nom')
        client.prenom = request.POST.get('prenom')
        client.email = request.POST.get('email')
        client.adresse = request.POST.get('adresse')

        # Vérifier si le numéro de téléphone est déjà pris par un autre client
        if Client.objects.filter(numero_tel=client.numero_tel).exclude(pk=client.pk).exists():
            messages.error(request, f"Un autre client utilise déjà le numéro {client.numero_tel}.")
        else:
            client.save()
            messages.success(request, "Client modifié avec succès.")
            return redirect('client:detail', pk=client.pk)

    context = {
        'client': client
    }
    return render(request, 'client/modifier_client.html', context)

@login_required
def supprimer_client(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
        messages.success(request, "Client supprimé avec succès.")
        return redirect('client:liste')
    
    # Pour la modale de confirmation, on pourrait rendre un template simple ou gérer via JS
    return render(request, 'composant_generale/modal_confirmation_suppression.html', {
        'item_id': pk,
        'item_name': f"Client {client.get_full_name()}",
        'delete_url': request.path, # L'URL de suppression est la page actuelle
        'redirect_url': '/client/liste/',
    })

@require_POST
@login_required
def supprimer_clients_masse(request):
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucun client sélectionné pour la suppression.")
        return redirect('client:liste')

    try:
        count = Client.objects.filter(pk__in=selected_ids).delete()[0]
        messages.success(request, f"{count} client(s) supprimé(s) avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('client:liste')
