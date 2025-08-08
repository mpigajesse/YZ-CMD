from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json

from commande.models import Commande, EtatCommande, EnumEtatCmd
from parametre.models import Region, Ville, Operateur
from article.models import Article


@login_required
def global_search_view(request):
    """Vue principale pour la barre de recherche globale - Logistique"""
    return render(request, 'operatLogistic/global_search.html')


@login_required
def global_search_api(request):
    """API pour la recherche globale en temps réel - Logistique"""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', 'all')
    
    if not query or len(query) < 2:
        return JsonResponse({
            'success': False,
            'message': 'Requête trop courte',
            'results': []
        })
    
    results = {
        'commandes': [],
        'livraisons': [],
        'retours': [],
        'regions': [],
        'villes': [],
        'statistiques': []
    }
    
    try:
        # Recherche dans les commandes (pour logistique)
        if category in ['all', 'commandes']:
            results['commandes'] = search_commandes_logistique(query, request)
        
        # Recherche dans les livraisons
        if category in ['all', 'livraisons']:
            results['livraisons'] = search_livraisons(query, request)
        
        # Recherche dans les retours
        if category in ['all', 'retours']:
            results['retours'] = search_retours(query, request)
        
        # Recherche dans les régions
        if category in ['all', 'regions']:
            results['regions'] = search_regions_logistique(query, request)
        
        # Recherche dans les villes
        if category in ['all', 'villes']:
            results['villes'] = search_villes_logistique(query, request)
        
        # Recherche dans les statistiques
        if category in ['all', 'statistiques']:
            results['statistiques'] = search_statistiques_logistique(query)
        
        return JsonResponse({
            'success': True,
            'query': query,
            'results': results,
            'total_results': sum(len(v) for v in results.values())
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la recherche: {str(e)}',
            'results': []
        })


def search_commandes_logistique(query, request=None):
    """Recherche dans les commandes pour logistique"""
    commandes = []
    
    # Recherche par ID numérique
    if query.isdigit():
        try:
            cmd = Commande.objects.get(id=int(query))
            # Pour la recherche par ID, être plus permissif
            commandes.append({
                'id': cmd.id,
                'type': 'commande',
                'title': f'Commande #{cmd.id}',
                'subtitle': f'Client: {cmd.client.nom if cmd.client else "N/A"} - {cmd.total_cmd} DH',
                'status': get_commande_status(cmd),
                'url': f'/operateur-logistique/commande/{cmd.id}/',
                'icon': 'fas fa-shopping-cart',
                'priority': 1
            })
        except Commande.DoesNotExist:
            pass
    
    # Recherche par numéro externe
    try:
        cmd_externe = Commande.objects.get(num_cmd__icontains=query)
        commandes.append({
            'id': cmd_externe.id,
            'type': 'commande',
            'title': f'Commande #{cmd_externe.id} ({cmd_externe.num_cmd})',
            'subtitle': f'Client: {cmd_externe.client.nom if cmd_externe.client else "N/A"} - {cmd_externe.total_cmd} DH',
            'status': get_commande_status(cmd_externe),
            'url': f'/operateur-logistique/commande/{cmd_externe.id}/',
            'icon': 'fas fa-shopping-cart',
            'priority': 1
        })
    except Commande.DoesNotExist:
        pass
    
    # Recherche par client (exclure les recherches déjà faites par numéro externe)
    commandes_client = Commande.objects.filter(
        Q(client__nom__icontains=query) |
        Q(client__prenom__icontains=query) |
        Q(client__email__icontains=query)
    ).exclude(
        num_cmd__icontains=query
    )[:10]
    
    for cmd in commandes_client:
        # Pour la recherche par client, être plus permissif
        commandes.append({
            'id': cmd.id,
            'type': 'commande',
            'title': f'Commande #{cmd.id} ({cmd.num_cmd})',
            'subtitle': f'Client: {cmd.client.nom if cmd.client else "N/A"} - {cmd.total_cmd} DH',
            'status': get_commande_status(cmd),
            'url': f'/operateur-logistique/commande/{cmd.id}/',
            'icon': 'fas fa-shopping-cart',
            'priority': 2
        })
    
    # Recherche par région/ville/ville_init (exclure les recherches déjà faites)
    commandes_geo = Commande.objects.filter(
        Q(ville__nom__icontains=query) |
        Q(ville__region__nom_region__icontains=query) |
        Q(ville_init__icontains=query)
    ).exclude(
        Q(num_cmd__icontains=query) |
        Q(client__nom__icontains=query) |
        Q(client__prenom__icontains=query) |
        Q(client__email__icontains=query)
    )[:10]
    
    for cmd in commandes_geo:
        # Pour la recherche par géographie, être plus permissif
        ville_display = cmd.ville.nom if cmd.ville else "N/A"
        if cmd.ville_init and cmd.ville_init != (cmd.ville.nom if cmd.ville else ""):
            ville_display = f"{cmd.ville_init} → {ville_display}"
        
        commandes.append({
            'id': cmd.id,
            'type': 'commande',
            'title': f'Commande #{cmd.id} ({cmd.num_cmd})',
            'subtitle': f'{ville_display} - {cmd.total_cmd} DH',
            'status': get_commande_status(cmd),
            'url': f'/operateur-logistique/commande/{cmd.id}/',
            'icon': 'fas fa-shopping-cart',
            'priority': 3
        })
    
    # Dédupliquer les résultats par ID de commande
    commandes_uniques = []
    ids_vus = set()
    
    for cmd in commandes:
        if cmd['id'] not in ids_vus:
            commandes_uniques.append(cmd)
            ids_vus.add(cmd['id'])
    
    return commandes_uniques[:10]


def search_livraisons(query, request=None):
    """Recherche dans les livraisons"""
    livraisons = []
    
    # Recherche par mots-clés de livraison
    if any(keyword in query.lower() for keyword in ['livraison', 'livrer', 'livre']):
        livraisons.append({
            'id': 'commandes-a-livrer',
            'type': 'livraison',
            'title': 'Commandes à Livrer',
            'subtitle': 'Gérer les commandes prêtes pour livraison',
            'status': 'En cours',
            'url': '/operateur-logistique/commandes/',
            'icon': 'fas fa-truck',
            'priority': 1
        })
    
    # Recherche par commandes préparées (prêtes pour livraison)
    commandes_preparees = Commande.objects.filter(
        etats__enum_etat__libelle__in=["Préparée", "En livraison", "Confirmée"],
        etats__date_fin__isnull=True
    )[:5]
    
    for cmd in commandes_preparees:
        # Pour les livraisons, être plus permissif
        livraisons.append({
            'id': cmd.id,
            'type': 'livraison',
            'title': f'Livraison Commande #{cmd.id} ({cmd.num_cmd})',
            'subtitle': f'Client: {cmd.client.nom if cmd.client else "N/A"} - {get_commande_status(cmd)}',
            'status': get_commande_status(cmd),
            'url': f'/operateur-logistique/commande/{cmd.id}/',
            'icon': 'fas fa-truck',
            'priority': 2
        })
    
    return livraisons


def search_retours(query, request=None):
    """Recherche dans les retours"""
    retours = []
    
    # Recherche par mots-clés de retour
    if any(keyword in query.lower() for keyword in ['retour', 'retourner', 'sav']):
        retours.append({
            'id': 'retours-sav',
            'type': 'retour',
            'title': 'Retours SAV',
            'subtitle': 'Gérer les retours et SAV',
            'status': 'Actif',
            'url': '/operateur-logistique/sav/retournees/',
            'icon': 'fas fa-undo',
            'priority': 1
        })
    
    # Recherche par commandes retournées
    commandes_retournees = Commande.objects.filter(
        etats__enum_etat__libelle__in=["Retournée", "En SAV", "Annulée"],
        etats__date_fin__isnull=True
    )[:5]
    
    for cmd in commandes_retournees:
        # Pour les retours, être plus permissif
        retours.append({
            'id': cmd.id,
            'type': 'retour',
            'title': f'Retour Commande #{cmd.id}',
            'subtitle': f'Client: {cmd.client.nom if cmd.client else "N/A"} - {get_commande_status(cmd)}',
            'status': get_commande_status(cmd),
            'url': f'/operateur-logistique/commande/{cmd.id}/',
            'icon': 'fas fa-undo',
            'priority': 2
        })
    
    return retours


def search_regions_logistique(query, request=None):
    """Recherche dans les régions pour logistique"""
    regions = []
    
    regions_match = Region.objects.filter(
        Q(nom_region__icontains=query)
    )[:5]
    
    for region in regions_match:
        # Compter les commandes à livrer de cette région (plus inclusif)
        commandes_region = Commande.objects.filter(
            ville__region=region,
            etats__enum_etat__libelle__in=["Préparée", "En livraison", "Confirmée"],
            etats__date_fin__isnull=True
        )
        
        # Compter toutes les commandes de la région
        nb_commandes = commandes_region.count()
        
        regions.append({
            'id': region.id,
            'type': 'region',
            'title': region.nom_region,
            'subtitle': f'{nb_commandes} commandes à livrer',
            'status': 'Active',
            'url': f'/operateur-logistique/commandes/?region={region.nom_region}',
            'icon': 'fas fa-map',
            'priority': 1
        })
    
    return regions


def search_villes_logistique(query, request=None):
    """Recherche dans les villes pour logistique"""
    villes = []
    
    villes_match = Ville.objects.filter(
        Q(nom__icontains=query) |
        Q(region__nom_region__icontains=query)
    )[:5]
    
    # Ajouter aussi les villes initiales qui correspondent
    villes_init_match = Commande.objects.filter(
        ville_init__icontains=query
    ).values_list('ville_init', flat=True).distinct()[:5]
    
    for ville in villes_match:
        # Compter les commandes à livrer de cette ville (plus inclusif)
        commandes_ville = Commande.objects.filter(
            ville=ville,
            etats__enum_etat__libelle__in=["Préparée", "En livraison", "Confirmée"],
            etats__date_fin__isnull=True
        )
        
        # Compter toutes les commandes de la ville
        nb_commandes = commandes_ville.count()
        
        villes.append({
            'id': ville.id,
            'type': 'ville',
            'title': ville.nom,
            'subtitle': f'{ville.region.nom_region} - {nb_commandes} commandes à livrer',
            'status': 'Active',
            'url': f'/operateur-logistique/commandes/?ville={ville.nom}',
            'icon': 'fas fa-map-marker-alt',
            'priority': 1
        })
    
    # Ajouter les villes initiales trouvées
    for ville_init in villes_init_match:
        if ville_init:
            # Compter les commandes avec cette ville initiale
            nb_commandes_init = Commande.objects.filter(
                ville_init=ville_init,
                etats__enum_etat__libelle__in=["Préparée", "En livraison", "Confirmée"],
                etats__date_fin__isnull=True
            ).count()
            
            villes.append({
                'id': f'init_{ville_init}',
                'type': 'ville_init',
                'title': f'{ville_init} (Ville Initiale)',
                'subtitle': f'{nb_commandes_init} commandes à livrer',
                'status': 'Active',
                'url': f'/operateur-logistique/commandes/?ville_init={ville_init}',
                'icon': 'fas fa-map-marker-alt',
                'priority': 1
            })
    
    return villes


def search_statistiques_logistique(query):
    """Recherche dans les statistiques pour logistique"""
    statistiques = []
    
    # Recherche par mots-clés spécifiques à la logistique
    keywords = {
        'livraison': {'title': 'Gestion Livraisons', 'url': '/operateur-logistique/commandes/', 'icon': 'fas fa-truck', 'id': 'gestion-livraisons'},
        'retour': {'title': 'Gestion Retours', 'url': '/operateur-logistique/sav/retournees/', 'icon': 'fas fa-undo', 'id': 'gestion-retours'},
        'sav': {'title': 'Service Après-Vente', 'url': '/operateur-logistique/sav/retournees/', 'icon': 'fas fa-tools', 'id': 'service-apres-vente'},
        'statistiques': {'title': 'Statistiques Logistique', 'url': '/operateur-logistique/commandes/', 'icon': 'fas fa-chart-bar', 'id': 'statistiques-logistique'},
        'rapport': {'title': 'Rapports Logistique', 'url': '/operateur-logistique/commandes/', 'icon': 'fas fa-file-alt', 'id': 'rapports-logistique'},
        'suivi': {'title': 'Suivi Livraisons', 'url': '/operateur-logistique/commandes/', 'icon': 'fas fa-route', 'id': 'suivi-livraisons'},
    }
    
    for keyword, info in keywords.items():
        if keyword in query.lower():
            statistiques.append({
                'id': info['id'],
                'type': 'statistique',
                'title': info['title'],
                'subtitle': 'Accès direct aux données de logistique',
                'status': 'Disponible',
                'url': info['url'],
                'icon': info['icon'],
                'priority': 1
            })
    
    return statistiques


def is_commande_for_logistique(commande, request=None):
    """Vérifier si une commande est éligible pour la logistique"""
    etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
    
    if not etat_actuel:
        return False
    
    # États éligibles pour la logistique (plus inclusifs)
    etats_logistique = [
        "Nouvelle", "Confirmée", "Préparée", "En livraison", 
        "Livrée", "Retournée", "En SAV", "Annulée"
    ]
    
    if etat_actuel.enum_etat.libelle not in etats_logistique:
        return False
    
    # Si on a accès à la requête, vérifier l'affectation à l'opérateur
    if request and hasattr(request, 'user'):
        # Vérifier si la commande est affectée à l'opérateur logistique actuel
        if hasattr(commande, 'operateur_logistique') and commande.operateur_logistique:
            return commande.operateur_logistique == request.user
        else:
            # Si pas d'opérateur logistique assigné, inclure dans la recherche
            # Pour tous les états logistiques
            return True
    
    return True


def get_commande_status(commande):
    """Obtenir le statut actuel d'une commande"""
    etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
    if etat_actuel:
        return etat_actuel.enum_etat.libelle
    return "Nouvelle"


@login_required
def search_suggestions_api(request):
    """API pour les suggestions de recherche - Logistique"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    suggestions = []
    
    # Suggestions basées sur l'historique de logistique
    common_searches = [
        "livraisons actives",
        "commandes à livrer",
        "retours sav",
        "suivi livraison",
        "statistiques logistique",
        "rapports livraison"
    ]
    
    for search in common_searches:
        if query.lower() in search.lower():
            suggestions.append({
                'text': search,
                'category': 'Recherche fréquente'
            })
    
    # Suggestions de commandes prêtes pour livraison
    recent_commandes = Commande.objects.filter(
        etats__enum_etat__libelle="Préparée",
        etats__date_fin__isnull=True
    ).order_by('-id')[:3]
    
    for cmd in recent_commandes:
        suggestions.append({
            'text': f"livraison #{cmd.id}",
            'category': 'Commande à livrer'
        })
    
    # Suggestions de commandes en retour
    commandes_retour = Commande.objects.filter(
        etats__enum_etat__libelle__in=["Retournée", "En SAV"],
        etats__date_fin__isnull=True
    ).order_by('-id')[:3]
    
    for cmd in commandes_retour:
        suggestions.append({
            'text': f"retour #{cmd.id}",
            'category': 'Commande en retour'
        })
    
    return JsonResponse({'suggestions': suggestions[:10]})
