from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.urls import reverse
from datetime import datetime, timedelta
import json

from commande.models import Commande, EtatCommande, EnumEtatCmd
from parametre.models import Region, Ville, Operateur
from article.models import Article


@login_required
def global_search_view(request):
    """Vue principale pour la barre de recherche globale - Préparation"""
    return render(request, 'Prepacommande/global_search.html')


@login_required
def global_search_api(request):
    """API pour la recherche globale en temps réel - Préparation"""
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
        'articles': [],
        'stock': [],
        'regions': [],
        'villes': [],
        'statistiques': []
    }
    
    try:
        # Recherche dans les commandes (pour préparation)
        if category in ['all', 'commandes']:
            results['commandes'] = search_commandes_preparation(query, request)
        
        # Recherche dans les articles
        if category in ['all', 'articles']:
            results['articles'] = search_articles_preparation(query)
        
        # Recherche dans le stock
        if category in ['all', 'stock']:
            results['stock'] = search_stock_preparation(query)
        
        # Recherche dans les régions
        if category in ['all', 'regions']:
            results['regions'] = search_regions_preparation(query, request)
        
        # Recherche dans les villes
        if category in ['all', 'villes']:
            results['villes'] = search_villes_preparation(query, request)
        
        # Recherche dans les statistiques
        if category in ['all', 'statistiques']:
            results['statistiques'] = search_statistiques_preparation(query)
        
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


def search_commandes_preparation(query, request=None):
    """Recherche dans les commandes pour préparation"""
    commandes = []
    
    # Recherche par ID numérique
    if query.isdigit():
        try:
            cmd = Commande.objects.get(id=int(query))
            # Pour la recherche par ID, être plus permissif
            commandes.append({
                'id': cmd.id,
                'type': 'commande',
                'title': f'Commande #{cmd.id} ({cmd.num_cmd})',
                'subtitle': f'Client: {cmd.client.nom if cmd.client else "N/A"} - {cmd.total_cmd} DH',
                'status': get_commande_status(cmd),
                'url': reverse('Prepacommande:detail_prepa', kwargs={'pk': cmd.id}),
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
            'url': reverse('Prepacommande:detail_prepa', kwargs={'pk': cmd_externe.id}),
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
            'url': reverse('Prepacommande:detail_prepa', kwargs={'pk': cmd.id}),
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
            'url': reverse('Prepacommande:detail_prepa', kwargs={'pk': cmd.id}),
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


def search_articles_preparation(query):
    """Recherche dans les articles pour préparation"""
    articles = []
    
    articles_match = Article.objects.filter(
        Q(nom__icontains=query) |
        Q(reference__icontains=query) |
        Q(description__icontains=query)
    )[:8]
    
    for article in articles_match:
        articles.append({
            'id': article.id,
            'type': 'article',
            'title': article.nom,
            'subtitle': f'Réf: {article.reference} - Stock: {article.qte_disponible}',
            'status': 'En stock' if article.qte_disponible > 0 else 'Rupture',
            'url': reverse('Prepacommande:detail_article', kwargs={'article_id': article.id}),
            'icon': 'fas fa-box',
            'priority': 1
        })
    
    return articles


def search_stock_preparation(query):
    """Recherche dans le stock pour préparation"""
    stock_items = []
    
    # Recherche par nom d'article
    articles_stock = Article.objects.filter(
        Q(nom__icontains=query) |
        Q(reference__icontains=query)
    )[:5]
    
    for article in articles_stock:
        stock_items.append({
            'id': article.id,
            'type': 'stock',
            'title': f'Stock {article.nom}',
            'subtitle': f'Réf: {article.reference} - Quantité: {article.qte_disponible}',
            'status': 'En stock' if article.qte_disponible > 0 else 'Rupture',
            'url': f'/operateur-preparation/stock/article/{article.id}/',
            'icon': 'fas fa-warehouse',
            'priority': 1
        })
    
    # Recherche par mots-clés stock
    if any(keyword in query.lower() for keyword in ['stock', 'inventaire', 'quantité', 'rupture']):
        stock_items.append({
            'id': 'stock-general',
            'type': 'stock',
            'title': 'Gestion du Stock',
            'subtitle': 'Voir tous les articles en stock',
            'status': 'Disponible',
            'url': '/operateur-preparation/stock/articles/',
            'icon': 'fas fa-warehouse',
            'priority': 2
        })
    
    return stock_items


def search_regions_preparation(query, request=None):
    """Recherche dans les régions pour préparation"""
    regions = []
    
    regions_match = Region.objects.filter(
        Q(nom_region__icontains=query)
    )[:5]
    
    for region in regions_match:
        # Compter les commandes à préparer de cette région (plus inclusif)
        nb_commandes = Commande.objects.filter(
            ville__region=region,
            etats__enum_etat__libelle__in=["Confirmée", "En préparation", "Préparée"],
            etats__date_fin__isnull=True
        ).count()
        
        regions.append({
            'id': region.id,
            'type': 'region',
            'title': region.nom_region,
            'subtitle': f'{nb_commandes} commandes à préparer',
            'status': 'Active',
            'url': f'/operateur-preparation/en-preparation/?region={region.nom_region}',
            'icon': 'fas fa-map',
            'priority': 1
        })
    
    return regions


def search_villes_preparation(query, request=None):
    """Recherche dans les villes pour préparation"""
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
        # Compter les commandes à préparer de cette ville (plus inclusif)
        nb_commandes = Commande.objects.filter(
            ville=ville,
            etats__enum_etat__libelle__in=["Confirmée", "En préparation", "Préparée"],
            etats__date_fin__isnull=True
        ).count()
        
        villes.append({
            'id': ville.id,
            'type': 'ville',
            'title': ville.nom,
            'subtitle': f'{ville.region.nom_region} - {nb_commandes} commandes à préparer',
            'status': 'Active',
            'url': f'/operateur-preparation/en-preparation/?ville={ville.nom}',
            'icon': 'fas fa-map-marker-alt',
            'priority': 1
        })
    
    # Ajouter les villes initiales trouvées
    for ville_init in villes_init_match:
        if ville_init:
            # Compter les commandes avec cette ville initiale
            nb_commandes_init = Commande.objects.filter(
                ville_init=ville_init,
                etats__enum_etat__libelle__in=["Confirmée", "En préparation", "Préparée"],
                etats__date_fin__isnull=True
            ).count()
            
            villes.append({
                'id': f'init_{ville_init}',
                'type': 'ville_init',
                'title': f'{ville_init} (Ville Initiale)',
                'subtitle': f'{nb_commandes_init} commandes à préparer',
                'status': 'Active',
                'url': f'/operateur-preparation/en-preparation/?ville_init={ville_init}',
                'icon': 'fas fa-map-marker-alt',
                'priority': 1
            })
    
    return villes


def search_statistiques_preparation(query):
    """Recherche dans les statistiques pour préparation"""
    statistiques = []
    
    # Recherche par mots-clés spécifiques à la préparation
    keywords = {
        'preparation': {'title': 'Commandes en Préparation', 'url': reverse('Prepacommande:commandes_en_preparation'), 'icon': 'fas fa-boxes'},
        'confirmee': {'title': 'Commandes Confirmées', 'url': reverse('Prepacommande:liste_prepa'), 'icon': 'fas fa-check-circle'},
        'stock': {'title': 'Gestion du Stock', 'url': reverse('Prepacommande:liste_articles'), 'icon': 'fas fa-warehouse'},
        'inventaire': {'title': 'Inventaire', 'url': reverse('Prepacommande:alertes_stock'), 'icon': 'fas fa-clipboard-list'},
        'statistiques': {'title': 'Statistiques Préparation', 'url': reverse('Prepacommande:home'), 'icon': 'fas fa-chart-bar'},
        'rapport': {'title': 'Rapports Préparation', 'url': reverse('Prepacommande:home'), 'icon': 'fas fa-file-alt'},
    }
    
    for keyword, info in keywords.items():
        if keyword in query.lower():
            statistiques.append({
                'id': keyword,
                'type': 'statistique',
                'title': info['title'],
                'subtitle': 'Accès direct aux données de préparation',
                'status': 'Disponible',
                'url': info['url'],
                'icon': info['icon'],
                'priority': 1
            })
    
    return statistiques


def is_commande_for_preparation(commande, request=None):
    """Vérifier si une commande est éligible pour la préparation"""
    etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
    if etat_actuel:
        etats_preparation = ["Confirmée", "En préparation", "Préparée", "Nouvelle", "Annulée"]
        return etat_actuel.enum_etat.libelle in etats_preparation
    return False


def get_commande_status(commande):
    """Obtenir le statut actuel d'une commande"""
    etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
    if etat_actuel:
        return etat_actuel.enum_etat.libelle
    return "Nouvelle"


@login_required
def search_suggestions_api(request):
    """API pour les suggestions de recherche - Préparation"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'suggestions': []})
    
    suggestions = []
    
    # Suggestions basées sur l'historique de préparation
    common_searches = [
        "commandes confirmées",
        "commandes en préparation",
        "stock faible",
        "articles rupture",
        "inventaire",
        "statistiques préparation"
    ]
    
    for search in common_searches:
        if query.lower() in search.lower():
            suggestions.append({
                'text': search,
                'category': 'Recherche fréquente'
            })
    
    # Suggestions de commandes récentes à préparer
    recent_commandes = Commande.objects.filter(
        etats__enum_etat__libelle="Confirmée",
        etats__date_fin__isnull=True
    ).order_by('-id')[:3]
    
    for cmd in recent_commandes:
        suggestions.append({
            'text': f"commande #{cmd.id}",
            'category': 'Commande à préparer'
        })
    
    # Suggestions d'articles en rupture
    articles_rupture = Article.objects.filter(qte_disponible=0)[:3]
    for article in articles_rupture:
        suggestions.append({
            'text': f"stock {article.nom}",
            'category': 'Article en rupture'
        })
    
    return JsonResponse({'suggestions': suggestions[:10]})
