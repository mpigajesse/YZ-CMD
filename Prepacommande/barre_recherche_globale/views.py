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
from commande.models import Panier


@login_required
def global_search_view(request):
    """Vue principale pour la barre de recherche globale - Préparation"""
    return render(request, 'Prepacommande/global_search.html')


@login_required
def global_search_api(request):
    """API de recherche globale pour les opérateurs de préparation"""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', 'all')
    
    if len(query) < 2:
        return JsonResponse({
            'success': False,
            'message': 'Requête trop courte',
            'results': []
        })
    
    results = {
        'commandes': [],
        'articles_panier': [],
        'exports': [],
        'fonctionnalites': [],
        'profile': []
    }
    
    try:
        # Recherche dans les commandes
        if category in ['all', 'commandes']:
            results['commandes'] = search_commandes_preparation(query, request)
        
        # Recherche dans les articles du panier des commandes en préparation
        if category in ['all', 'articles_panier']:
            results['articles_panier'] = search_articles_panier_preparation(query)
        
        # Recherche dans les exports et rapports
        if category in ['all', 'exports']:
            results['exports'] = search_exports_preparation(query)
        
        # Recherche dans les fonctionnalités
        if category in ['all', 'fonctionnalites']:
            results['fonctionnalites'] = search_fonctionnalites_preparation(query)
        
        # Recherche dans le profil
        if category in ['all', 'profile']:
            results['profile'] = search_profile_preparation(query)
        
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
    
    # Recherche par client
    commandes_client = Commande.objects.filter(
        Q(client__nom__icontains=query) |
        Q(client__prenom__icontains=query) |
        Q(client__email__icontains=query)
    ).exclude(
        num_cmd__icontains=query
    )[:10]
    
    for cmd in commandes_client:
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
    
    # Recherche par région/ville
    commandes_geo = Commande.objects.filter(
        Q(ville__nom__icontains=query) |
        Q(ville__region__nom_region__icontains=query) |
        Q(ville_init__icontains=query)
    ).exclude(
        Q(num_cmd__icontains=query) |
        Q(client__nom__icontains=query) |
        Q(client__prenom__icontains=query)
    )[:10]
    
    for cmd in commandes_geo:
        commandes.append({
            'id': cmd.id,
            'type': 'commande',
            'title': f'Commande #{cmd.id} ({cmd.num_cmd})',
            'subtitle': f'Client: {cmd.client.nom if cmd.client else "N/A"} - {cmd.total_cmd} DH',
            'status': get_commande_status(cmd),
            'url': reverse('Prepacommande:detail_prepa', kwargs={'pk': cmd.id}),
            'icon': 'fas fa-shopping-cart',
            'priority': 3
        })
    
    # Éliminer les doublons
    commandes_uniques = []
    seen_ids = set()
    for cmd in commandes:
        if cmd['id'] not in seen_ids:
            commandes_uniques.append(cmd)
            seen_ids.add(cmd['id'])
    
    return commandes_uniques[:10]


def search_exports_preparation(query):
    """Recherche dans les exports et rapports"""
    exports = []
    
    # Recherche par mots-clés d'export
    keywords = {
        'export': {'title': 'Exports Consolidés', 'url': reverse('Prepacommande:export_commandes_consolidees_csv'), 'icon': 'fas fa-file-export'},
        'csv': {'title': 'Export CSV Consolidé', 'url': reverse('Prepacommande:export_commandes_consolidees_csv'), 'icon': 'fas fa-file-csv'},
        'excel': {'title': 'Export Excel Consolidé', 'url': reverse('Prepacommande:export_commandes_consolidees_excel'), 'icon': 'fas fa-file-excel'},
        'rapport': {'title': 'Rapports Consolidés', 'url': reverse('Prepacommande:export_commandes_consolidees_excel'), 'icon': 'fas fa-chart-bar'},
        'consolide': {'title': 'Données Consolidées', 'url': reverse('Prepacommande:export_commandes_consolidees_csv'), 'icon': 'fas fa-database'},
    }
    
    for keyword, info in keywords.items():
        if keyword in query.lower():
            exports.append({
                'id': keyword,
                'type': 'export',
                'title': info['title'],
                'subtitle': 'Télécharger les données consolidées',
                'status': 'Disponible',
                'url': info['url'],
                'icon': info['icon'],
                'priority': 1
            })
    
    return exports


def search_fonctionnalites_preparation(query):
    """Recherche dans les fonctionnalités de préparation"""
    fonctionnalites = []
    
    # Recherche par mots-clés de fonctionnalités
    keywords = {
        'preparation': {'title': 'Commandes en Préparation', 'url': reverse('Prepacommande:commandes_en_preparation'), 'icon': 'fas fa-boxes'},
        'confirmee': {'title': 'Commandes Confirmées', 'url': reverse('Prepacommande:liste_prepa'), 'icon': 'fas fa-check-circle'},
        'livree': {'title': 'Commandes Livrées Partiellement', 'url': reverse('Prepacommande:commandes_livrees_partiellement'), 'icon': 'fas fa-truck'},
        'retournee': {'title': 'Commandes Retournées', 'url': reverse('Prepacommande:commandes_retournees'), 'icon': 'fas fa-undo'},
        'ticket': {'title': 'Impression Tickets', 'url': reverse('Prepacommande:imprimer_tickets_preparation'), 'icon': 'fas fa-print'},
        'statistiques': {'title': 'Statistiques Préparation', 'url': reverse('Prepacommande:home'), 'icon': 'fas fa-chart-bar'},
        'dashboard': {'title': 'Tableau de Bord', 'url': reverse('Prepacommande:home'), 'icon': 'fas fa-tachometer-alt'},
    }
    
    for keyword, info in keywords.items():
        if keyword in query.lower():
            fonctionnalites.append({
                'id': keyword,
                'type': 'fonctionnalite',
                'title': info['title'],
                'subtitle': 'Accès direct aux fonctionnalités',
                'status': 'Disponible',
                'url': info['url'],
                'icon': info['icon'],
                'priority': 1
            })
    
    return fonctionnalites


def search_profile_preparation(query):
    """Recherche dans les fonctionnalités de profil"""
    profile = []
    
    # Recherche par mots-clés de profil
    keywords = {
        'profile': {'title': 'Mon Profil', 'url': reverse('Prepacommande:profile'), 'icon': 'fas fa-user'},
        'profil': {'title': 'Mon Profil', 'url': reverse('Prepacommande:profile'), 'icon': 'fas fa-user'},
        'modifier': {'title': 'Modifier Profil', 'url': reverse('Prepacommande:modifier_profile'), 'icon': 'fas fa-user-edit'},
        'mot de passe': {'title': 'Changer Mot de Passe', 'url': reverse('Prepacommande:changer_mot_de_passe'), 'icon': 'fas fa-key'},
        'password': {'title': 'Changer Mot de Passe', 'url': reverse('Prepacommande:changer_mot_de_passe'), 'icon': 'fas fa-key'},
    }
    
    for keyword, info in keywords.items():
        if keyword in query.lower():
            profile.append({
                'id': keyword,
                'type': 'profile',
                'title': info['title'],
                'subtitle': 'Gestion du compte utilisateur',
                'status': 'Disponible',
                'url': info['url'],
                'icon': info['icon'],
                'priority': 1
            })
    
    return profile


def search_articles_panier_preparation(query):
    """Recherche dans les articles du panier des commandes en préparation"""
    articles_panier = []
    
    # Rechercher dans les commandes avec états : En préparation, Collectée, Emballée
    commandes_preparation = Commande.objects.filter(
        etats__enum_etat__libelle__in=["En préparation", "Collectée", "Emballée"],
        etats__date_fin__isnull=True
    ).distinct()
    
    # Rechercher les articles du panier qui correspondent à la requête
    paniers_match = Panier.objects.filter(
        commande__in=commandes_preparation,
        article__nom__icontains=query
    ).select_related('article', 'commande')[:10]
    
    for panier in paniers_match:
        # Obtenir l'état actuel de la commande
        etat_actuel = panier.commande.etats.filter(date_fin__isnull=True).first()
        etat_libelle = etat_actuel.enum_etat.libelle if etat_actuel else "N/A"
        
        articles_panier.append({
            'id': f"panier_{panier.id}",
            'type': 'article_panier',
            'title': panier.article.nom,
            'subtitle': f'Commande #{panier.commande.id} - Qté: {panier.quantite} - État: {etat_libelle}',
            'status': etat_libelle,
            'url': reverse('Prepacommande:detail_prepa', kwargs={'pk': panier.commande.id}),
            'icon': 'fas fa-shopping-basket',
            'priority': 1
        })
    
    # Rechercher aussi par référence d'article
    paniers_ref = Panier.objects.filter(
        commande__in=commandes_preparation,
        article__reference__icontains=query
    ).select_related('article', 'commande').exclude(
        article__nom__icontains=query
    )[:5]
    
    for panier in paniers_ref:
        etat_actuel = panier.commande.etats.filter(date_fin__isnull=True).first()
        etat_libelle = etat_actuel.enum_etat.libelle if etat_actuel else "N/A"
        
        articles_panier.append({
            'id': f"panier_ref_{panier.id}",
            'type': 'article_panier',
            'title': f"{panier.article.nom} (Réf: {panier.article.reference})",
            'subtitle': f'Commande #{panier.commande.id} - Qté: {panier.quantite} - État: {etat_libelle}',
            'status': etat_libelle,
            'url': reverse('Prepacommande:detail_prepa', kwargs={'pk': panier.commande.id}),
            'icon': 'fas fa-shopping-basket',
            'priority': 2
        })
    
    # Rechercher par référence de variante
    paniers_ref_variante = Panier.objects.filter(
        commande__in=commandes_preparation,
        variante__reference_variante__icontains=query
    ).select_related('article', 'commande', 'variante').exclude(
        Q(article__nom__icontains=query) | Q(article__reference__icontains=query)
    )[:3]
    
    for panier in paniers_ref_variante:
        etat_actuel = panier.commande.etats.filter(date_fin__isnull=True).first()
        etat_libelle = etat_actuel.enum_etat.libelle if etat_actuel else "N/A"
        
        variante_info = ""
        if panier.variante:
            if panier.variante.couleur and panier.variante.pointure:
                variante_info = f" - {panier.variante.couleur.nom} {panier.variante.pointure.pointure}"
            elif panier.variante.couleur:
                variante_info = f" - {panier.variante.couleur.nom}"
            elif panier.variante.pointure:
                variante_info = f" - {panier.variante.pointure.pointure}"
        
        articles_panier.append({
            'id': f"panier_ref_var_{panier.id}",
            'type': 'article_panier',
            'title': f"{panier.article.nom}{variante_info} (Réf: {panier.variante.reference_variante})",
            'subtitle': f'Commande #{panier.commande.id} - Qté: {panier.quantite} - État: {etat_libelle}',
            'status': etat_libelle,
            'url': reverse('Prepacommande:detail_prepa', kwargs={'pk': panier.commande.id}),
            'icon': 'fas fa-shopping-basket',
            'priority': 2
        })
    
    # Rechercher par couleur/pointure si c'est une variante
    paniers_variante = Panier.objects.filter(
        commande__in=commandes_preparation,
        variante__couleur__nom__icontains=query
    ).select_related('article', 'commande', 'variante__couleur', 'variante__pointure').exclude(
        Q(article__nom__icontains=query) | Q(article__reference__icontains=query) | Q(variante__reference_variante__icontains=query)
    )[:5]
    
    for panier in paniers_variante:
        etat_actuel = panier.commande.etats.filter(date_fin__isnull=True).first()
        etat_libelle = etat_actuel.enum_etat.libelle if etat_actuel else "N/A"
        
        variante_info = f" - {panier.variante.couleur.nom}" if panier.variante and panier.variante.couleur else ""
        
        articles_panier.append({
            'id': f"panier_var_{panier.id}",
            'type': 'article_panier',
            'title': f"{panier.article.nom}{variante_info}",
            'subtitle': f'Commande #{panier.commande.id} - Qté: {panier.quantite} - État: {etat_libelle}',
            'status': etat_libelle,
            'url': reverse('Prepacommande:detail_prepa', kwargs={'pk': panier.commande.id}),
            'icon': 'fas fa-shopping-basket',
            'priority': 3
        })
    
    # Rechercher aussi par pointure si c'est une variante
    paniers_pointure = Panier.objects.filter(
        commande__in=commandes_preparation,
        variante__pointure__pointure__icontains=query
    ).select_related('article', 'commande', 'variante__couleur', 'variante__pointure').exclude(
        Q(article__nom__icontains=query) | Q(article__reference__icontains=query) | Q(variante__couleur__nom__icontains=query) | Q(variante__reference_variante__icontains=query)
    )[:3]
    
    for panier in paniers_pointure:
        etat_actuel = panier.commande.etats.filter(date_fin__isnull=True).first()
        etat_libelle = etat_actuel.enum_etat.libelle if etat_actuel else "N/A"
        
        variante_info = f" - {panier.variante.pointure.pointure}" if panier.variante and panier.variante.pointure else ""
        
        articles_panier.append({
            'id': f"panier_pointure_{panier.id}",
            'type': 'article_panier',
            'title': f"{panier.article.nom}{variante_info}",
            'subtitle': f'Commande #{panier.commande.id} - Qté: {panier.quantite} - État: {etat_libelle}',
            'status': etat_libelle,
            'url': reverse('Prepacommande:detail_prepa', kwargs={'pk': panier.commande.id}),
            'icon': 'fas fa-shopping-basket',
            'priority': 4
        })
    
    # Éliminer les doublons
    articles_uniques = []
    seen_ids = set()
    for article in articles_panier:
        if article['id'] not in seen_ids:
            articles_uniques.append(article)
            seen_ids.add(article['id'])
    
    return articles_uniques[:10]


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
    
    # Suggestions basées sur les fonctionnalités disponibles
    common_searches = [
        "commandes confirmées",
        "commandes en préparation",
        "commandes livrées partiellement",
        "commandes retournées",
        "impression tickets",
        "export csv",
        "export excel",
        "statistiques préparation",
        "tableau de bord",
        "mon profil",
        "changer mot de passe",
        "articles panier",
        "rechercher articles"
    ]
    
    for search in common_searches:
        if query.lower() in search.lower():
            suggestions.append({
                'text': search,
                'category': 'Fonctionnalité disponible'
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
    
    # Suggestions d'exports populaires
    export_suggestions = [
        "export commandes consolidées",
        "export csv consolidé",
        "export excel consolidé",
        "rapport consolidé"
    ]
    
    for export in export_suggestions:
        if query.lower() in export.lower():
            suggestions.append({
                'text': export,
                'category': 'Export disponible'
            })
    
    # Suggestions d'articles populaires dans les paniers
    if len(query) >= 3:
        articles_populaires = Panier.objects.filter(
            commande__etats__enum_etat__libelle__in=["En préparation", "Collectée", "Emballée"],
            commande__etats__date_fin__isnull=True,
            article__nom__icontains=query
        ).values('article__nom').annotate(
            count=Count('id')
        ).order_by('-count')[:3]
        
        for article in articles_populaires:
            suggestions.append({
                'text': f"article {article['article__nom']}",
                'category': 'Article dans panier'
            })
    
    return JsonResponse({'suggestions': suggestions[:10]})
