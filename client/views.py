from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, OuterRef, Subquery
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Client
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

    if search_query:
        # Recherche flexible et variée
        search_terms = search_query.strip().split()
        
        # Construction de la requête de recherche
        search_conditions = Q()
        
        # Vérifier si la recherche correspond exactement à une ville_init
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

    # Triez par date de création par défaut
    clients = clients.order_by('-date_creation')

    # Gestion de la pagination flexible
    items_per_page = request.GET.get('items_per_page', 10)
    start_range = request.GET.get('start_range', '')
    end_range = request.GET.get('end_range', '')
    
    # Conserver une copie des clients non paginés pour les statistiques
    clients_non_pagines = clients
    
    # Gestion de la plage personnalisée
    if start_range and end_range:
        try:
            start_idx = int(start_range) - 1  # Index commence à 0
            end_idx = int(end_range)
            if start_idx >= 0 and end_idx > start_idx:
                clients = list(clients)[start_idx:end_idx]
                # Créer un paginator factice pour la plage
                paginator = Paginator(clients, len(clients))
                page_obj = paginator.get_page(1)
        except (ValueError, TypeError):
            # En cas d'erreur, utiliser la pagination normale
            items_per_page = 10
            paginator = Paginator(clients, items_per_page)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
    else:
        # Pagination normale
        page_number = request.GET.get('page', 1)
        if items_per_page == 'all':
            # Afficher tous les clients
            paginator = Paginator(clients, clients.count())
            page_obj = paginator.get_page(1)
        else:
            try:
                items_per_page = int(items_per_page)
                if items_per_page <= 0:
                    items_per_page = 10
            except (ValueError, TypeError):
                items_per_page = 10
            
            paginator = Paginator(clients, items_per_page)
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
    
    # Calculer les pourcentages
    pourcentage_avec_commandes = round((clients_avec_commandes / total_clients * 100), 1) if total_clients > 0 else 0
    pourcentage_sans_commandes = round((clients_sans_commandes / total_clients * 100), 1) if total_clients > 0 else 0

    # Vérifier si c'est une requête AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        
        # Rendre les templates partiels pour AJAX
        html_table_body = render_to_string('client/partials/_clients_table_body.html', {
            'page_obj': page_obj,
            'search_query': search_query
        }, request=request)
        
        html_pagination = render_to_string('client/partials/_clients_pagination.html', {
            'page_obj': page_obj,
            'search_query': search_query,
            'items_per_page': items_per_page,
            'start_range': start_range,
            'end_range': end_range
        }, request=request)
        
        html_pagination_info = render_to_string('client/partials/_clients_pagination_info.html', {
            'page_obj': page_obj
        }, request=request)
        
        return JsonResponse({
            'success': True,
            'html_table_body': html_table_body,
            'html_pagination': html_pagination,
            'html_pagination_info': html_pagination_info,
            'total_count': clients_non_pagines.count()
        })

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_clients': total_clients,
        'clients_avec_commandes': clients_avec_commandes,
        'clients_sans_commandes': clients_sans_commandes,
        'doublons_detectes': doublons_detectes,
        'clients_avec_cmd_erronees': clients_avec_cmd_erronees,
        'clients_avec_cmd_doublons': clients_avec_cmd_doublons,
        'derniere_sync': derniere_sync,
        'pourcentage_avec_commandes': pourcentage_avec_commandes,
        'pourcentage_sans_commandes': pourcentage_sans_commandes,
        'items_per_page': items_per_page,
        'start_range': start_range,
        'end_range': end_range,
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
    
    # Pagination flexible
    items_per_page = request.GET.get('items_per_page', '15')
    start_range = request.GET.get('start_range', '')
    end_range = request.GET.get('end_range', '')
    
    # Gestion de la pagination flexible
    if start_range and end_range and start_range.isdigit() and end_range.isdigit():
        start_range = int(start_range)
        end_range = int(end_range)
        if start_range > 0 and end_range >= start_range:
            # Pagination par plage personnalisée
            total_count = commandes_queryset.count()
            if end_range > total_count:
                end_range = total_count
            
            # Créer un paginator temporaire pour obtenir la page correspondante
            temp_paginator = Paginator(commandes_queryset, end_range - start_range + 1)
            page_number = 1
            page_obj = temp_paginator.get_page(page_number)
            
            # Ajuster les indices pour l'affichage
            page_obj.start_index = start_range
            page_obj.end_index = end_range
            page_obj.number = 1
            page_obj.has_previous = False
            page_obj.has_next = False
            page_obj.previous_page_number = None
            page_obj.next_page_number = None
            page_obj.num_pages = 1
        else:
            # Plage invalide, utiliser la pagination normale
            if isinstance(items_per_page, str) and items_per_page.isdigit():
                items_per_page = int(items_per_page)
            elif not isinstance(items_per_page, int):
                items_per_page = 15
            paginator = Paginator(commandes_queryset, items_per_page)
            page_number = request.GET.get('page', 1)
            page_obj = paginator.get_page(page_number)
    else:
        # Pagination normale
        if items_per_page == 'all':
            # Afficher toutes les commandes
            paginator = Paginator(commandes_queryset, commandes_queryset.count())
            page_number = 1
            page_obj = paginator.get_page(page_number)
        else:
            if isinstance(items_per_page, str) and items_per_page.isdigit():
                items_per_page = int(items_per_page)
            elif not isinstance(items_per_page, int):
                items_per_page = 15
            paginator = Paginator(commandes_queryset, items_per_page)
            page_number = request.GET.get('page', 1)
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
        'items_per_page': items_per_page,
        'start_range': start_range,
        'end_range': end_range,
    }
    return render(request, 'client/detail_client.html', context)


@login_required
def detail_client_ajax(request, pk):
    """Vue AJAX pour la pagination flexible des commandes du client"""
    from django.template.loader import render_to_string
    from django.http import JsonResponse
    
    client = get_object_or_404(Client, pk=pk)
    
    # Récupérer les paramètres de pagination
    search_query = request.GET.get('search', '')
    items_per_page = request.GET.get('items_per_page', '15')
    start_range = request.GET.get('start_range', '')
    end_range = request.GET.get('end_range', '')
    page = request.GET.get('page', 1)
    
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
    
    # Gestion de la pagination flexible
    if start_range and end_range and start_range.isdigit() and end_range.isdigit():
        start_range = int(start_range)
        end_range = int(end_range)
        if start_range > 0 and end_range >= start_range:
            # Pagination par plage personnalisée
            total_count = commandes_queryset.count()
            if end_range > total_count:
                end_range = total_count
            
            # Créer un paginator temporaire pour obtenir la page correspondante
            temp_paginator = Paginator(commandes_queryset, end_range - start_range + 1)
            page_obj = temp_paginator.get_page(1)
            
            # Ajuster les indices pour l'affichage
            page_obj.start_index = start_range
            page_obj.end_index = end_range
            page_obj.number = 1
            page_obj.has_previous = False
            page_obj.has_next = False
            page_obj.previous_page_number = None
            page_obj.next_page_number = None
            page_obj.num_pages = 1
        else:
            # Plage invalide, utiliser la pagination normale
            if isinstance(items_per_page, str) and items_per_page.isdigit():
                items_per_page = int(items_per_page)
            elif not isinstance(items_per_page, int):
                items_per_page = 15
            paginator = Paginator(commandes_queryset, items_per_page)
            page_obj = paginator.get_page(page)
    else:
        # Pagination normale
        if items_per_page == 'all':
            # Afficher toutes les commandes
            paginator = Paginator(commandes_queryset, commandes_queryset.count())
            page_obj = paginator.get_page(1)
        else:
            items_per_page = int(items_per_page) if items_per_page.isdigit() else 15
            paginator = Paginator(commandes_queryset, items_per_page)
            page_obj = paginator.get_page(page)
    
    # Rendre les templates partiels
    html_table_body = render_to_string('client/partials/_detail_client_commandes_table_body.html', {
        'page_obj': page_obj,
        'client': client
    }, request=request)
    
    html_pagination = render_to_string('client/partials/_detail_client_pagination.html', {
        'page_obj': page_obj,
        'search_query': search_query
    }, request=request)
    
    html_pagination_info = render_to_string('client/partials/_detail_client_pagination_info.html', {
        'page_obj': page_obj
    }, request=request)
    
    return JsonResponse({
        'success': True,
        'html_table_body': html_table_body,
        'html_pagination': html_pagination,
        'html_pagination_info': html_pagination_info,
        'current_page': page_obj.number,
        'total_count': page_obj.paginator.count,
    })

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

@login_required
def recherche_clients_ajax(request):
    """Vue AJAX pour la recherche dynamique des clients"""
    search_query = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    
    # Sous-requête pour trouver la 'ville_init' de la dernière commande de chaque client
    latest_commande_ville_init = Commande.objects.filter(
        client=OuterRef('pk')
    ).order_by('-date_creation').values('ville_init')[:1]

    # Annoter les clients avec la ville de leur dernière commande
    clients = Client.objects.annotate(
        nombre_commandes=Count('commandes', distinct=True),
        derniere_ville_init=Subquery(latest_commande_ville_init)
    ).all()

    if search_query:
        # Recherche flexible et variée
        search_terms = search_query.strip().split()
        
        # Construction de la requête de recherche
        search_conditions = Q()
        
        # Vérifier si la recherche correspond exactement à une ville_init
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

    # Triez par date de création par défaut
    clients = clients.order_by('-date_creation')

    # Gestion de la pagination flexible
    items_per_page = request.GET.get('items_per_page', 10)
    start_range = request.GET.get('start_range', '')
    end_range = request.GET.get('end_range', '')
    
    # Conserver une copie des clients non paginés pour les statistiques
    clients_non_pagines = clients
    
    # Gestion de la plage personnalisée
    if start_range and end_range:
        try:
            start_idx = int(start_range) - 1  # Index commence à 0
            end_idx = int(end_range)
            if start_idx >= 0 and end_idx > start_idx:
                clients = list(clients)[start_idx:end_idx]
                # Créer un paginator factice pour la plage
                paginator = Paginator(clients, len(clients))
                page_obj = paginator.get_page(1)
        except (ValueError, TypeError):
            # En cas d'erreur, utiliser la pagination normale
            items_per_page = 10
            paginator = Paginator(clients, items_per_page)
            page_obj = paginator.get_page(page)
    else:
        # Pagination normale
        if items_per_page == 'all':
            # Afficher tous les clients
            paginator = Paginator(clients, clients.count())
            page_obj = paginator.get_page(1)
        else:
            try:
                items_per_page = int(items_per_page)
                if items_per_page <= 0:
                    items_per_page = 10
            except (ValueError, TypeError):
                items_per_page = 10
            
            paginator = Paginator(clients, items_per_page)
            page_obj = paginator.get_page(page)

    # Rendre les templates partiels pour AJAX
    html_table_body = render_to_string('client/partials/_clients_table_body.html', {
        'page_obj': page_obj,
        'search_query': search_query
    }, request=request)
    
    html_pagination = render_to_string('client/partials/_clients_pagination.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'items_per_page': items_per_page,
        'start_range': start_range,
        'end_range': end_range
    }, request=request)
    
    html_pagination_info = render_to_string('client/partials/_clients_pagination_info.html', {
        'page_obj': page_obj
    }, request=request)

    return JsonResponse({
        'success': True,
        'html_table_body': html_table_body,
        'html_pagination': html_pagination,
        'html_pagination_info': html_pagination_info,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'total_count': clients_non_pagines.count(),
    })

@login_required
def api_paniers_client(request, client_id):
    """API pour récupérer tous les paniers d'un client"""
    try:
        client = get_object_or_404(Client, pk=client_id)
        
        # Récupérer toutes les commandes du client avec leurs paniers
        commandes = Commande.objects.filter(client=client).select_related(
            'client', 'ville'
        ).prefetch_related(
            'paniers__article',
            'etats__enum_etat'
        ).order_by('-date_cmd')
        
        # Préparer les données pour chaque commande
        commandes_data = []
        for commande in commandes:
            paniers = commande.paniers.all()
            total_articles = sum(panier.quantite for panier in paniers)
            total_montant = sum(panier.sous_total for panier in paniers)
            
            # Récupérer l'état actuel de la commande
            etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
            etat_libelle = etat_actuel.enum_etat.libelle if etat_actuel else "Non défini"
            
            # Préparer les articles de cette commande
            articles_data = []
            for panier in paniers:
                articles_data.append({
                    'nom': str(panier.article.nom),
                    'reference': str(panier.article.reference) if panier.article.reference else 'N/A',
                    'description': str(panier.article.description) if panier.article.description else '',
                    'prix_unitaire': float(panier.article.prix_unitaire),
                    'quantite': panier.quantite,
                    'sous_total': float(panier.sous_total),
                    'couleur': panier.article.couleur,
                    'pointure': panier.article.pointure,
                })
            
            commandes_data.append({
                'id': commande.id,
                'id_yz': commande.id_yz,
                'num_cmd': commande.num_cmd,
                'date_cmd': commande.date_cmd.strftime('%d/%m/%Y') if commande.date_cmd else 'N/A',
                'etat': etat_libelle,
                'total_articles': total_articles,
                'total_montant': float(total_montant),
                'articles': articles_data
            })
        
        return JsonResponse({
            'success': True,
            'client': {
                'id': client.id,
                'nom': client.get_full_name,
                'numero_tel': client.numero_tel,
                'email': client.email,
                'nombre_commandes': len(commandes_data)
            },
            'commandes': commandes_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la récupération des paniers: {str(e)}'
        }, status=500)
