from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, timedelta
import json

from commande.models import Commande, EtatCommande, EnumEtatCmd
from parametre.models import Region, Ville, Operateur
from article.models import Article


@staff_member_required
@login_required
def global_search_view(request):
    """Vue principale pour la barre de recherche globale"""
    return render(request, 'parametre/dashboard_360/barre_recherche_globale/global_search.html')


@staff_member_required
@login_required
def global_search_api(request):
    """API pour la recherche globale en temps réel"""
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
        'operateurs': [],
        'regions': [],
        'villes': [],
        'articles': [],
        'statistiques': []
    }
    
    try:
        # Recherche dans les commandes
        if category in ['all', 'commandes']:
            results['commandes'] = search_commandes(query)
        
        # Recherche dans les opérateurs
        if category in ['all', 'operateurs']:
            results['operateurs'] = search_operateurs(query)
        
        # Recherche dans les régions
        if category in ['all', 'regions']:
            results['regions'] = search_regions(query)
        
        # Recherche dans les villes
        if category in ['all', 'villes']:
            results['villes'] = search_villes(query)
        
        # Recherche dans les articles
        if category in ['all', 'articles']:
            results['articles'] = search_articles(query)
        
        # Recherche dans les statistiques
        if category in ['all', 'statistiques']:
            results['statistiques'] = search_statistiques(query)
        
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


def search_commandes(query):
    """Recherche dans les commandes"""
    commandes = []
    
    # Recherche par ID
    if query.isdigit():
        try:
            cmd = Commande.objects.get(id=int(query))
            commandes.append({
                'id': cmd.id,
                'type': 'commande',
                'title': f'Commande #{cmd.id}',
                'subtitle': f'Client: {cmd.client.nom if cmd.client else "N/A"} - {cmd.total_cmd} DH',
                'status': get_commande_status(cmd),
                'url': f'/commande/detail/{cmd.id}/',
                'icon': 'fas fa-shopping-cart',
                'priority': 1
            })
        except Commande.DoesNotExist:
            pass
    
    # Recherche par client
    commandes_client = Commande.objects.filter(
        Q(client__nom__icontains=query) |
        Q(client__prenom__icontains=query) |
        Q(client__email__icontains=query)
    )[:5]
    
    for cmd in commandes_client:
        commandes.append({
            'id': cmd.id,
            'type': 'commande',
            'title': f'Commande #{cmd.id}',
            'subtitle': f'Client: {cmd.client.nom if cmd.client else "N/A"} - {cmd.total_cmd} DH',
            'status': get_commande_status(cmd),
            'url': f'/commande/detail/{cmd.id}/',
            'icon': 'fas fa-shopping-cart',
            'priority': 2
        })
    
    # Recherche par région/ville
    commandes_geo = Commande.objects.filter(
        Q(ville__nom__icontains=query) |
        Q(ville__region__nom_region__icontains=query)
    )[:5]
    
    for cmd in commandes_geo:
        commandes.append({
            'id': cmd.id,
            'type': 'commande',
            'title': f'Commande #{cmd.id}',
            'subtitle': f'{cmd.ville.nom if cmd.ville else "N/A"} - {cmd.total_cmd} DH',
            'status': get_commande_status(cmd),
            'url': f'/commande/detail/{cmd.id}/',
            'icon': 'fas fa-shopping-cart',
            'priority': 3
        })
    
    # Recherche par montant
    if any(keyword in query.lower() for keyword in ['dh', 'montant', 'prix']):
        try:
            # Extraire le montant de la requête
            import re
            montant_match = re.search(r'(\d+)', query)
            if montant_match:
                montant = float(montant_match.group(1))
                commandes_montant = Commande.objects.filter(total_cmd__gte=montant)[:3]
                for cmd in commandes_montant:
                    commandes.append({
                        'id': cmd.id,
                        'type': 'commande',
                        'title': f'Commande #{cmd.id}',
                        'subtitle': f'Montant: {cmd.total_cmd} DH',
                        'status': get_commande_status(cmd),
                        'url': f'/commande/detail/{cmd.id}/',
                        'icon': 'fas fa-shopping-cart',
                        'priority': 4
                    })
        except:
            pass
    
    return commandes[:10]  # Limiter à 10 résultats


def search_operateurs(query):
    """Recherche dans les opérateurs"""
    operateurs = []
    
    # Recherche par nom/prénom
    operateurs_nom = Operateur.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__username__icontains=query)
    )[:5]
    
    for op in operateurs_nom:
        operateurs.append({
            'id': op.id,
            'type': 'operateur',
            'title': f'{op.user.first_name} {op.user.last_name}',
            'subtitle': f'{op.get_type_operateur_display()} - {op.region.nom_region if op.region else "N/A"}',
            'status': 'Actif' if op.actif else 'Inactif',
            'url': f'/parametre/operateurs/detail/{op.id}/',
            'icon': 'fas fa-user',
            'priority': 1
        })
    
    # Recherche par type d'opérateur
    type_keywords = {
        'preparation': 'PRÉPARATION',
        'logistique': 'LOGISTIQUE', 
        'confirmation': 'CONFIRMATION',
        'admin': 'ADMIN'
    }
    
    for keyword, type_op in type_keywords.items():
        if keyword in query.lower():
            operateurs_type = Operateur.objects.filter(type_operateur=type_op)[:3]
            for op in operateurs_type:
                operateurs.append({
                    'id': op.id,
                    'type': 'operateur',
                    'title': f'{op.user.first_name} {op.user.last_name}',
                    'subtitle': f'{op.get_type_operateur_display()} - {op.region.nom_region if op.region else "N/A"}',
                    'status': 'Actif' if op.actif else 'Inactif',
                    'url': f'/parametre/operateurs/detail/{op.id}/',
                    'icon': 'fas fa-user',
                    'priority': 2
                })
            break
    
    return operateurs[:8]


def search_regions(query):
    """Recherche dans les régions"""
    regions = []
    
    regions_match = Region.objects.filter(
        Q(nom_region__icontains=query)
    )[:5]
    
    for region in regions_match:
        # Compter les commandes de cette région
        nb_commandes = Commande.objects.filter(
            ville__region=region,
            etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée", "En préparation"],
            etats__date_fin__isnull=True
        ).count()
        
        regions.append({
            'id': region.id,
            'type': 'region',
            'title': region.nom_region,
            'subtitle': f'{nb_commandes} commandes actives',
            'status': 'Active',
            'url': f'/parametre/repartition/details-region/?region={region.nom_region}',
            'icon': 'fas fa-map',
            'priority': 1
        })
    
    return regions


def search_villes(query):
    """Recherche dans les villes"""
    villes = []
    
    villes_match = Ville.objects.filter(
        Q(nom__icontains=query) |
        Q(region__nom_region__icontains=query)
    )[:5]
    
    for ville in villes_match:
        # Compter les commandes de cette ville
        nb_commandes = Commande.objects.filter(
            ville=ville,
            etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée", "En préparation"],
            etats__date_fin__isnull=True
        ).count()
        
        villes.append({
            'id': ville.id,
            'type': 'ville',
            'title': ville.nom,
            'subtitle': f'{ville.region.nom_region} - {nb_commandes} commandes',
            'status': 'Active',
            'url': f'/parametre/repartition/details-region/?ville={ville.nom}',
            'icon': 'fas fa-map-marker-alt',
            'priority': 1
        })
    
    return villes


def search_articles(query):
    """Recherche dans les articles"""
    articles = []
    
    articles_match = Article.objects.filter(
        Q(nom__icontains=query) |
        Q(reference__icontains=query) |
        Q(description__icontains=query)
    )[:5]
    
    for article in articles_match:
        articles.append({
            'id': article.id,
            'type': 'article',
            'title': article.nom,
            'subtitle': f'Réf: {article.reference} - Stock: {article.qte_disponible}',
            'status': 'En stock' if article.qte_disponible > 0 else 'Rupture',
            'url': f'/article/detail/{article.id}/',
            'icon': 'fas fa-box',
            'priority': 1
        })
    
    return articles


def search_statistiques(query):
    """Recherche dans les statistiques"""
    statistiques = []
    
    # Recherche par mots-clés statistiques
    keywords = {
        'kpi': {'title': 'Dashboard KPIs', 'url': '/kpis/', 'icon': 'fas fa-chart-line'},
        'performance': {'title': 'Performance Opérateurs', 'url': '/kpis/#performance-operateurs', 'icon': 'fas fa-chart-bar'},
        'statistiques': {'title': 'Statistiques par Région', 'url': '/parametre/repartition/details-region/', 'icon': 'fas fa-chart-pie'},
        'export': {'title': 'Exports disponibles', 'url': '/parametre/repartition/details-region/', 'icon': 'fas fa-file-export'},
        'repartition': {'title': 'Répartition Automatique', 'url': '/parametre/repartition/automatique/', 'icon': 'fas fa-random'},
        'sav': {'title': 'Service Après-Vente', 'url': '/parametre/sav/commandes-retournees/', 'icon': 'fas fa-tools'},
        'synchronisation': {'title': 'Synchronisation', 'url': '/parametre/synchronisation/', 'icon': 'fas fa-sync'},
    }
    
    for keyword, info in keywords.items():
        if keyword in query.lower():
            statistiques.append({
                'id': keyword,
                'type': 'statistique',
                'title': info['title'],
                'subtitle': 'Accès direct aux données',
                'status': 'Disponible',
                'url': info['url'],
                'icon': info['icon'],
                'priority': 1
            })
    
    return statistiques


def get_commande_status(commande):
    """Obtenir le statut actuel d'une commande"""
    etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
    if etat_actuel:
        return etat_actuel.enum_etat.libelle
    return "Nouvelle"


@staff_member_required
@login_required
def search_suggestions_api(request):
    """API pour les suggestions de recherche"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    suggestions = []
    
    # Suggestions basées sur l'historique et les tendances
    common_searches = [
        "commandes confirmées",
        "opérateurs préparation",
        "statistiques casablanca",
        "export excel",
        "stock faible",
        "sav commandes retournées"
    ]
    
    for search in common_searches:
        if query.lower() in search.lower():
            suggestions.append({
                'text': search,
                'category': 'Recherche fréquente'
            })
    
    # Suggestions de commandes récentes
    recent_commandes = Commande.objects.order_by('-id')[:3]
    for cmd in recent_commandes:
        suggestions.append({
            'text': f"commande #{cmd.id}",
            'category': 'Commande récente'
        })
    
    # Suggestions de régions actives
    active_regions = Region.objects.annotate(
        nb_commandes=Count('villes__commandes', filter=Q(
            villes__commandes__etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée", "En préparation"],
            villes__commandes__etats__date_fin__isnull=True
        ))
    ).filter(nb_commandes__gt=0)[:3]
    
    for region in active_regions:
        suggestions.append({
            'text': f"statistiques {region.nom_region.lower()}",
            'category': 'Région active'
        })
    
    return JsonResponse({'suggestions': suggestions[:10]}) 