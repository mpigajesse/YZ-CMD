from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q, F, Min, Max
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps

from commande.models import Commande, Panier, EtatCommande, Operation, EnumEtatCmd
from article.models import Article
from client.models import Client
from parametre.models import Operateur

def format_number_fr(number, decimals=0):
    """Formate un nombre selon les standards français (espace comme séparateur de milliers)"""
    if number is None or (isinstance(number, (int, float)) and number == 0):
        return "0"
    
    if isinstance(number, (int, float)):
        if decimals == 0:
            # Pour les entiers, utiliser un format sans décimales
            return f"{number:,.0f}".replace(",", " ")
        else:
            # Pour les décimales
            return f"{number:,.{decimals}f}".replace(",", " ")
    
    # Si c'est déjà une chaîne, la retourner telle quelle
    return str(number)

def api_login_required(view_func):
    """Décorateur qui renvoie du JSON au lieu de rediriger pour les APIs"""
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'Authentification requise',
                'error': 'non_authentifie'
            }, status=401)
        return view_func(request, *args, **kwargs)
    return wrapped_view

def get_integer_fields():
    """Retourne la liste des champs qui doivent être des entiers"""
    integer_fields = [
        'delai_livraison_defaut',
        'fidelisation_commandes_min', 
        'fidelisation_periode_jours',
        'periode_analyse_standard',
        'delai_livraison_alerte',
        'stock_critique_seuil',
        'stock_ventes_minimum',
        'periode_analyse_defaut'  # Ajouté pour les selects
    ]
    return integer_fields

def validate_integer_value(nom_parametre, valeur):
    """Valide qu'une valeur est un entier pour les champs qui le requièrent"""
    integer_fields = get_integer_fields()
    
    if nom_parametre in integer_fields:
        # Vérifier que c'est un entier
        if not isinstance(valeur, int) and not (isinstance(valeur, float) and valeur.is_integer()):
            return False, f"Ce champ doit être un nombre entier (pas de décimales)"
        
        # Convertir en entier si c'est un float qui représente un entier
        if isinstance(valeur, float) and valeur.is_integer():
            valeur = int(valeur)
    
    return True, valeur

@login_required
def ventes_data(request):
    """API pour les données de l'onglet Ventes - E-commerce téléphonique Yoozak"""
    try:
        # Dates de référence
        aujourd_hui = timezone.now().date()
        debut_mois = aujourd_hui.replace(day=1)
        mois_precedent = (debut_mois - timedelta(days=1)).replace(day=1)
        debut_30j = aujourd_hui - timedelta(days=30)
        # === KPI 1: CA par Période (Commandes livrées uniquement) ===
        # CA de ce mois (du 1er du mois jusqu'à aujourd'hui) - Commandes livrées
        ca_mois_actuel = Commande.objects.filter(
            date_cmd__gte=debut_mois,
            date_cmd__lte=aujourd_hui,
            etats__enum_etat__libelle__iexact='Livrée'
        ).aggregate(total=Sum('total_cmd'))['total'] or 0
        
        # CA mois précédent (du 1er au dernier jour du mois précédent) - Commandes livrées
        fin_mois_precedent = debut_mois - timedelta(days=1)
        ca_mois_precedent = Commande.objects.filter(
            date_cmd__gte=mois_precedent,
            date_cmd__lte=fin_mois_precedent,
            etats__enum_etat__libelle__iexact='Livrée'
        ).aggregate(total=Sum('total_cmd'))['total'] or 0
        
        # Tendance CA
        if ca_mois_precedent > 0:
            tendance_ca = ((ca_mois_actuel - ca_mois_precedent) / ca_mois_precedent) * 100
        else:
            tendance_ca = 100 if ca_mois_actuel > 0 else 0
        
        # === KPI 2: Panier Moyen (Commandes livrées uniquement) ===
        panier_moyen_mois = Commande.objects.filter(
            date_cmd__gte=debut_mois,
            date_cmd__lte=aujourd_hui,
            etats__enum_etat__libelle__iexact='Livrée'
        ).aggregate(moyenne=Avg('total_cmd'))['moyenne'] or 0
        
        # Panier moyen mois précédent - Commandes livrées
        panier_moyen_precedent = Commande.objects.filter(
            date_cmd__gte=mois_precedent,
            date_cmd__lte=fin_mois_precedent,
            etats__enum_etat__libelle__iexact='Livrée'
        ).aggregate(moyenne=Avg('total_cmd'))['moyenne'] or 0
        
        # Tendance panier moyen
        if panier_moyen_precedent > 0:
            tendance_panier = ((panier_moyen_mois - panier_moyen_precedent) / panier_moyen_precedent) * 100
        else:
            tendance_panier = 100 if panier_moyen_mois > 0 else 0
        # === KPI 3: Nombre de Commandes (Commandes livrées uniquement) ===
        nb_commandes_mois = Commande.objects.filter(
            date_cmd__gte=debut_mois,
            date_cmd__lte=aujourd_hui,
            etats__enum_etat__libelle__iexact='Livrée'
        ).count()
        
        nb_commandes_mois_precedent = Commande.objects.filter(
            date_cmd__gte=mois_precedent,
            date_cmd__lte=fin_mois_precedent,
            etats__enum_etat__libelle__iexact='Livrée'
        ).count()
        
        # Tendance nombre de commandes
        if nb_commandes_mois_precedent > 0:
            tendance_commandes = ((nb_commandes_mois - nb_commandes_mois_precedent) / nb_commandes_mois_precedent) * 100
        else:
            tendance_commandes = 100 if nb_commandes_mois > 0 else 0
        
        # === KPIs Secondaires ===
        
        # Top 5 Modèles par CA (ce mois) - Basé sur les commandes livrées
        top_modeles = (Article.objects
            .filter(
                paniers__commande__date_cmd__gte=debut_mois, 
                paniers__commande__date_cmd__lte=aujourd_hui,
                paniers__commande__etats__enum_etat__libelle__iexact='Livrée',
                paniers__commande__etats__date_fin__isnull=True  # État actuel
            )
            .annotate(
                ca_total=Sum('paniers__sous_total'),
                quantite_vendue=Sum('paniers__quantite')
            )
            .order_by('-ca_total')[:5]
        )
        
        # Recherche du top modèle et top région
        top_modele = top_modeles.first() if top_modeles else None
        
        # Top Région par CA (ce mois)
        # Filtrer d'abord les commandes avec des régions valides
        top_regions = (Commande.objects
            .filter(date_cmd__gte=debut_mois, date_cmd__lte=aujourd_hui)
            .exclude(etats__enum_etat__libelle__iexact='Annulée')
            .exclude(ville__region__nom_region__isnull=True)  # Exclure les régions nulles
            .exclude(ville__region__nom_region__exact='')     # Exclure les régions vides
            .values('ville__region__nom_region')
            .annotate(
                ca_total=Sum('total_cmd'),
                nb_commandes=Count('id')
            )
            .order_by('-ca_total')[:5]
        )
        
        top_region = top_regions.first() if top_regions else None
        
        # Vérifier s'il y a des commandes sans région pour diagnostic
        commandes_sans_region = Commande.objects.filter(
            date_cmd__gte=debut_mois,
            date_cmd__lte=aujourd_hui,
            ville__region__nom_region__isnull=True
        ).exclude(etats__enum_etat__libelle__iexact='Annulée').count()
        
        # Commande maximale (ce mois) - Basée sur les commandes livrées
        commande_max = Commande.objects.filter(
            date_cmd__gte=debut_mois,
            date_cmd__lte=aujourd_hui,
            etats__enum_etat__libelle__iexact='Livrée'
        ).aggregate(max_cmd=Max('total_cmd'))['max_cmd'] or 0
        
        # Répartition par Catégorie
        ventes_par_categorie = (Article.objects
            .filter(paniers__commande__date_cmd__gte=debut_30j)
            .exclude(paniers__commande__etats__enum_etat__libelle__iexact='Annulée')
            .values('categorie')
            .annotate(
                ca_total=Sum('paniers__sous_total'),
                quantite=Sum('paniers__quantite')
            )
            .order_by('-ca_total')
        )
        
        # Répartition Géographique (Top 5 villes)
        ventes_par_ville = (Commande.objects
            .filter(date_cmd__gte=debut_30j)
            .exclude(etats__enum_etat__libelle__iexact='Annulée')
            .values('ville__nom', 'ville__region__nom_region')
            .annotate(
                ca_total=Sum('total_cmd'),
                nb_commandes=Count('id')
            )
            .order_by('-ca_total')[:5]
        )
        
        # Performance Opérateurs (Confirmation)
        performance_operateurs = []
        if Operation.objects.filter(date_operation__gte=debut_30j).exists():
            operateurs_stats = (Operation.objects
                .filter(date_operation__gte=debut_30j, type_operation__in=['APPEL', 'Appel Whatsapp'])
                .values('operateur__nom', 'operateur__prenom')
                .annotate(
                    nb_appels=Count('id'),
                    commandes_confirmees=Count('commande__etats__enum_etat__libelle', 
                                            filter=Q(commande__etats__enum_etat__libelle__iexact='Confirmée'))
                )
                .order_by('-nb_appels')[:3]
            )
            
            for stat in operateurs_stats:
                taux = (stat['commandes_confirmees'] / stat['nb_appels'] * 100) if stat['nb_appels'] > 0 else 0
                performance_operateurs.append({
                    'nom': f"{stat['operateur__prenom']} {stat['operateur__nom']}",
                    'nb_appels': stat['nb_appels'],
                    'taux_confirmation': round(taux, 1)
                })
        
        # Réponse JSON
        data = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'kpis_principaux': {
                'ca_periode': {
                    'valeur': float(ca_mois_actuel),
                    'valeur_formatee': format_number_fr(ca_mois_actuel),
                    'tendance': round(tendance_ca, 1),
                    'unite': 'DH',
                    'label': 'CA Total',
                    'sub_value': f"Ce mois vs {format_number_fr(ca_mois_precedent)} DH mois dernier"
                },
                'panier_moyen': {
                    'valeur': float(panier_moyen_mois) if panier_moyen_mois else 0,
                    'valeur_formatee': format_number_fr(panier_moyen_mois) if panier_moyen_mois else "0",
                    'tendance': round(tendance_panier, 1),
                    'unite': 'DH',
                    'label': 'Panier Moyen',
                    'sub_value': f"Ce mois vs {format_number_fr(panier_moyen_precedent)} DH mois dernier"
                },
                'nb_commandes': {
                    'valeur': nb_commandes_mois,
                    'valeur_formatee': format_number_fr(nb_commandes_mois),
                    'tendance': round(tendance_commandes, 1),
                    'unite': 'commandes',
                    'label': 'Nb Commandes',
                    'sub_value': f"Ce mois vs {format_number_fr(nb_commandes_mois_precedent)} mois dernier"
                }
            },
            'kpis_secondaires': {
                'top_modele': {
                    'nom': top_modele.nom if top_modele else 'Aucun',
                    'ca': float(top_modele.ca_total) if top_modele and top_modele.ca_total else 0,
                    'ca_formate': format_number_fr(top_modele.ca_total) if top_modele and top_modele.ca_total else "0",
                    'pourcentage': round((float(top_modele.ca_total) / ca_mois_actuel * 100), 1) if top_modele and top_modele.ca_total and ca_mois_actuel > 0 else 0
                },
                'top_region': {
                    'nom': (top_region['ville__region__nom_region'] 
                           if top_region and top_region['ville__region__nom_region'] 
                           else 'Données géographiques manquantes sur les commandes'),
                    'ca': float(top_region['ca_total']) if top_region else 0,
                    'ca_formate': (format_number_fr(top_region['ca_total']) 
                                  if top_region 
                                  else ""),
                    'pourcentage': (round((float(top_region['ca_total']) / ca_mois_actuel * 100), 1) 
                                   if top_region and ca_mois_actuel > 0 
                                   else 0),
                    'est_donnees_manquantes': not bool(top_region),
                    'affichage_simple': not bool(top_region)
                },
                'commande_max': {
                    'valeur': float(commande_max),
                    'valeur_formatee': format_number_fr(commande_max)
                },
                'top_modeles': [
                    {
                        'nom': article.nom,
                        'ca': float(article.ca_total) if article.ca_total else 0,
                        'quantite': article.quantite_vendue or 0,
                        'couleur': getattr(article, 'couleur', '#3b82f6'),
                        'reference': getattr(article, 'reference', 'N/A')
                    } for article in top_modeles
                ]
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du chargement des données Ventes'
        }, status=500)

@login_required
def evolution_ca_data(request):
    """API pour l'évolution du CA sur une période donnée"""
    try:
        # Paramètres
        periode = request.GET.get('period', '30j')
        jours_map = {'7j': 7, '30j': 30, '90j': 90}
        nb_jours = jours_map.get(periode, 30)
        
        # Dates avec timezone
        fin_date = timezone.now()
        debut_date = fin_date - timedelta(days=nb_jours)
        
        # Calcul des données réelles basées sur les commandes livrées
        commandes_par_jour = Commande.objects.filter(
            date_cmd__gte=debut_date,
            date_cmd__lte=fin_date,
            etats__enum_etat__libelle__iexact='Livrée',
            etats__date_fin__isnull=False
        ).extra(select={'date_seule': 'DATE(date_cmd)'}).values('date_seule').annotate(
            ca_jour=Sum('total_cmd')
        ).order_by('date_seule')
        
        # Construction des données de réponse
        evolution_data = []
        ca_par_jour = {}
        
        for cmd in commandes_par_jour:
            date_str = cmd['date_seule']
            if isinstance(date_str, str):
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date_obj = date_str
            ca_par_jour[date_obj] = float(cmd['ca_jour'] or 0)
          # Remplir tous les jours de la période avec les données réelles uniquement
        date_courante = debut_date.date()
        while date_courante <= fin_date.date():
            ca_jour = ca_par_jour.get(date_courante, 0)  # 0 si pas de ventes ce jour-là
            
            evolution_data.append({
                'date': date_courante.strftime('%Y-%m-%d'),
                'date_formatee': date_courante.strftime('%d/%m'),
                'ca': ca_jour,
                'ca_formate': f"{ca_jour:,.0f} DH" if ca_jour > 0 else "0 DH"
            })
            
            date_courante += timedelta(days=1)
          # Calculs de tendance basés sur les données réelles uniquement
        ca_total = sum(d['ca'] for d in evolution_data)
        ca_moyen = ca_total / len(evolution_data) if evolution_data else 0
        
        # Tendance : comparaison entre la première et la dernière semaine (si suffisamment de données)
        tendance = 0
        if len(evolution_data) >= 14:
            # Comparer première et dernière semaine
            premiere_semaine = evolution_data[:7]
            derniere_semaine = evolution_data[-7:]
            
            ca_debut = sum(d['ca'] for d in premiere_semaine) / 7
            ca_fin = sum(d['ca'] for d in derniere_semaine) / 7
            
            if ca_debut > 0:
                tendance = ((ca_fin - ca_debut) / ca_debut * 100)
        elif len(evolution_data) >= 7:
            # Si moins de 14 jours, comparer première et dernière moitié
            milieu = len(evolution_data) // 2
            premiere_moitie = evolution_data[:milieu]
            derniere_moitie = evolution_data[milieu:]
            
            ca_debut = sum(d['ca'] for d in premiere_moitie) / len(premiere_moitie) if premiere_moitie else 0
            ca_fin = sum(d['ca'] for d in derniere_moitie) / len(derniere_moitie) if derniere_moitie else 0
            
            if ca_debut > 0:
                tendance = ((ca_fin - ca_debut) / ca_debut * 100)
          # Statistiques supplémentaires pour l'analyse
        jours_avec_ventes = len([d for d in evolution_data if d['ca'] > 0])
        ca_max_jour = max([d['ca'] for d in evolution_data]) if evolution_data else 0
        ca_min_jour = min([d['ca'] for d in evolution_data if d['ca'] > 0]) if jours_avec_ventes > 0 else 0
        
        response_data = {
            'success': True,
            'periode': periode,
            'evolution': evolution_data,
            'resume': {
                'ca_total': ca_total,
                'ca_moyen': ca_moyen,
                'ca_max_jour': ca_max_jour,
                'ca_min_jour': ca_min_jour,
                'tendance': round(tendance, 2),
                'nb_jours': nb_jours,
                'jours_avec_ventes': jours_avec_ventes,
                'taux_activite': round((jours_avec_ventes / nb_jours * 100), 1) if nb_jours > 0 else 0
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du calcul de l\'évolution du CA'
        }, status=500)

@login_required
def top_modeles_data(request):
    """API pour les données du top modèles par CA"""
    try:
        # Paramètres
        limite = int(request.GET.get('limit', 10))
        periode_jours = int(request.GET.get('days', 30))
        
        # Dates
        fin_date = timezone.now()
        debut_date = fin_date - timedelta(days=periode_jours)
        
        # Calcul des ventes par article/modèle basé sur les commandes livrées
        top_modeles = Article.objects.annotate(
            ca_total=Sum(
                'paniers__sous_total',
                filter=Q(
                    paniers__commande__date_cmd__gte=debut_date,
                    paniers__commande__date_cmd__lte=fin_date,
                    paniers__commande__etats__enum_etat__libelle__iexact='Livrée',
                    paniers__commande__etats__date_fin__isnull=False
                )
            ),
            nb_ventes=Count(
                'paniers',
                filter=Q(
                    paniers__commande__date_cmd__gte=debut_date,
                    paniers__commande__date_cmd__lte=fin_date,
                    paniers__commande__etats__enum_etat__libelle__iexact='Livrée',
                    paniers__commande__etats__date_fin__isnull=False
                )
            )
        ).filter(
            ca_total__isnull=False,
            ca_total__gt=0
        ).order_by('-ca_total')[:limite]
          # Préparation des données (uniquement les données réelles)
        modeles_data = []
        couleurs = [
            '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6',
            '#ec4899', '#6b7280', '#14b8a6', '#f97316', '#84cc16'
        ]
        
        for i, article in enumerate(top_modeles):
            modeles_data.append({
                'nom': article.nom,
                'reference': article.reference,
                'ca': float(article.ca_total or 0),
                'ca_formate': f"{article.ca_total or 0:,.0f} DH",
                'nb_ventes': article.nb_ventes or 0,
                'prix_moyen': float(article.ca_total / article.nb_ventes) if article.nb_ventes > 0 else 0,
                'couleur': couleurs[i % len(couleurs)]
            })
        
        # Statistiques
        ca_total = sum(m['ca'] for m in modeles_data)
        ca_moyen = ca_total / len(modeles_data) if modeles_data else 0
        
        response_data = {
            'success': True,
            'modeles': modeles_data,
            'stats': {
                'ca_total': ca_total,
                'ca_moyen': ca_moyen,
                'nb_modeles': len(modeles_data),
                'periode_jours': periode_jours
            },
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du chargement du top modèles'
        }, status=500)

@login_required
def performance_regions_data(request):
    """API pour les données de performance par région"""
    try:
        # Période de référence (30 derniers jours par défaut)
        periode = request.GET.get('period', '30j')
        aujourd_hui = timezone.now().date()
        
        if periode == '7j':
            debut_periode = aujourd_hui - timedelta(days=7)
        elif periode == '90j':
            debut_periode = aujourd_hui - timedelta(days=90)
        else:  # 30j par défaut
            debut_periode = aujourd_hui - timedelta(days=30)
        
        # Récupérer les données par région
        regions_data = Commande.objects.filter(
            date_cmd__gte=debut_periode,
            date_cmd__lte=aujourd_hui,
            ville__isnull=False,
            ville__region__isnull=False
        ).exclude(
            etats__enum_etat__libelle__iexact='Annulée',
            etats__date_fin__isnull=True
        ).values(
            'ville__region__nom_region'
        ).annotate(
            ca_total=Sum('total_cmd'),
            nb_commandes=Count('id'),
            ca_moyen=Avg('total_cmd')
        ).order_by('-ca_total')
          # Calculer le total général pour les pourcentages
        total_ca_general = sum(region['ca_total'] or 0 for region in regions_data)
        
        # Gérer le cas où il n'y a pas de données
        if not regions_data:
            return JsonResponse({
                'success': True,
                'regions': [],
                'stats': {
                    'total_regions': 0,
                    'ca_total_general': 0,
                    'ca_total_format': '0 DH',
                    'nb_commandes_total': 0,
                    'ca_moyen_general': 0
                },
                'periode': periode,
                'message': 'Aucune donnée disponible pour cette période',
                'empty': True
            })
        
        # Formater les données pour le frontend
        regions_formattees = []
        
        for i, region in enumerate(regions_data):
            ca_total = region['ca_total'] or 0
            pourcentage = (ca_total / total_ca_general * 100) if total_ca_general > 0 else 0
            
            # Couleurs pour différencier les régions
            couleurs = [
                '#3b82f6',  # Bleu
                '#10b981',  # Vert
                '#f59e0b',  # Orange
                '#ef4444',  # Rouge
                '#8b5cf6',  # Violet
                '#06b6d4',  # Cyan
                '#84cc16',  # Lime
                '#f97316',  # Orange foncé
            ]
            
            regions_formattees.append({
                'nom_region': region['ville__region__nom_region'],
                'ca_total': float(ca_total),
                'ca_total_format': f"{ca_total/1000:.0f}K DH" if ca_total >= 1000 else f"{ca_total:.0f} DH",
                'nb_commandes': region['nb_commandes'],
                'ca_moyen': float(region['ca_moyen'] or 0),
                'pourcentage': round(pourcentage, 1),
                'couleur': couleurs[i % len(couleurs)]
            })
        
        # Limiter aux 5 premières régions pour l'affichage
        top_regions = regions_formattees[:5]
        
        # Calculer les statistiques globales
        stats_globales = {
            'total_regions': len(regions_formattees),
            'ca_total_general': float(total_ca_general),
            'ca_total_format': f"{total_ca_general/1000000:.1f}M DH" if total_ca_general >= 1000000 else f"{total_ca_general/1000:.0f}K DH",
            'nb_commandes_total': sum(region['nb_commandes'] for region in regions_formattees),
            'ca_moyen_general': float(total_ca_general / len(regions_formattees)) if regions_formattees else 0
        };
        
        response_data = {
            'success': True,
            'regions': top_regions,
            'stats': stats_globales,
            'periode': periode,
            'message': f'Données chargées pour {len(top_regions)} régions'
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du chargement des performances par région'
        }, status=500)

@login_required
def clients_data(request):
    """API pour les données de l'onglet Clients - Analyse comportementale Yoozak"""
    try:
        # Dates de référence
        aujourd_hui = timezone.now().date()
        debut_mois = aujourd_hui.replace(day=1)
        mois_precedent = (debut_mois - timedelta(days=1)).replace(day=1)
        debut_30j = aujourd_hui - timedelta(days=30)
        
        # === KPI 1: Nouveaux Clients ===
        nouveaux_clients_mois = Client.objects.filter(
            date_creation__date__gte=debut_mois,
            date_creation__date__lte=aujourd_hui
        ).count()
        
        # Nouveaux clients mois précédent
        fin_mois_precedent = debut_mois - timedelta(days=1)
        nouveaux_clients_precedent = Client.objects.filter(
            date_creation__date__gte=mois_precedent,
            date_creation__date__lte=fin_mois_precedent
        ).count()
        
        difference_nouveaux = nouveaux_clients_mois - nouveaux_clients_precedent
        
        # Plus besoin de calcul de moyenne journalière - simplification
        
        # === KPI 2: Clients Actifs (30 derniers jours) ===
        # Clients qui ont au moins une commande livrée
        clients_actifs_ids = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            etats__enum_etat__libelle__iexact='Livrée'
        ).values_list('client_id', flat=True).distinct()
        
        clients_actifs_30j = len(set(clients_actifs_ids))
        
        # Clients actifs période précédente (commandes livrées)
        debut_periode_precedente = debut_30j - timedelta(days=30)
        clients_actifs_precedent_ids = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j,
            etats__enum_etat__libelle__iexact='Livrée'
        ).values_list('client_id', flat=True).distinct()
        
        clients_actifs_precedent = len(set(clients_actifs_precedent_ids))
        difference_actifs = clients_actifs_30j - clients_actifs_precedent
        
        # Pourcentage du total
        total_clients = Client.objects.count()
        pourcentage_actifs = (clients_actifs_30j / total_clients * 100) if total_clients > 0 else 0
        
        # === KPI 3: Taux de Retour ===
        # CALCUL CORRECT - basé sur les commandes livrées uniquement
        # On ne peut retourner que ce qui a été livré !
        commandes_livrees_30j = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            etats__enum_etat__libelle__iexact='Livrée'
        ).distinct().count()
        
        # Commandes réellement retournées (avec état "Retournée")
        commandes_retournees = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            etats__enum_etat__libelle__iexact='Retournée'
        ).distinct().count()
        
        taux_retour = (commandes_retournees / commandes_livrees_30j * 100) if commandes_livrees_30j > 0 else 0
        
        # Taux retour période précédente
        commandes_livrees_precedent = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j,
            etats__enum_etat__libelle__iexact='Livrée'
        ).distinct().count()
        
        retours_precedent = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j,
            etats__enum_etat__libelle__iexact='Retournée'
        ).distinct().count()
        
        taux_retour_precedent = (retours_precedent / commandes_livrees_precedent * 100) if commandes_livrees_precedent > 0 else 0
        tendance_retour = taux_retour - taux_retour_precedent
        
        # === KPI 4: Fidélisation Client (90 jours - adapté secteur chaussures) ===
        # Période plus longue car les chaussures se rachètent moins fréquemment
        debut_90j = aujourd_hui - timedelta(days=90)
        debut_90j_precedent = debut_90j - timedelta(days=90)
        
        # Clients actifs sur 90 jours (commandes livrées uniquement)
        clients_actifs_90j_ids = Commande.objects.filter(
            date_cmd__gte=debut_90j,
            etats__enum_etat__libelle__iexact='Livrée'
        ).values_list('client_id', flat=True).distinct()
        clients_actifs_90j = len(set(clients_actifs_90j_ids))
        
        # Clients fidèles (2+ commandes livrées sur 90 jours)
        clients_fideles_90j = 0
        for client_id in clients_actifs_90j_ids:
            nb_commandes_livrees = Commande.objects.filter(
                client_id=client_id,
                date_cmd__gte=debut_90j,
                etats__enum_etat__libelle__iexact='Livrée'
            ).count()
            if nb_commandes_livrees >= 2:
                clients_fideles_90j += 1
        
        # Calcul du taux de fidélisation
        taux_fidelisation = (clients_fideles_90j / clients_actifs_90j * 100) if clients_actifs_90j > 0 else 0
        
        # Tendance fidélisation (vs période précédente 90j) - commandes livrées
        clients_actifs_90j_precedent_ids = Commande.objects.filter(
            date_cmd__gte=debut_90j_precedent,
            date_cmd__lt=debut_90j,
            etats__enum_etat__libelle__iexact='Livrée'
        ).values_list('client_id', flat=True).distinct()
        clients_actifs_90j_precedent = len(set(clients_actifs_90j_precedent_ids))
        
        clients_fideles_90j_precedent = 0
        for client_id in clients_actifs_90j_precedent_ids:
            nb_commandes_livrees_precedent = Commande.objects.filter(
                client_id=client_id,
                date_cmd__gte=debut_90j_precedent,
                date_cmd__lt=debut_90j,
                etats__enum_etat__libelle__iexact='Livrée'
            ).count()
            if nb_commandes_livrees_precedent >= 2:
                clients_fideles_90j_precedent += 1
        
        taux_fidelisation_precedent = (clients_fideles_90j_precedent / clients_actifs_90j_precedent * 100) if clients_actifs_90j_precedent > 0 else 0
        tendance_fidelisation = taux_fidelisation - taux_fidelisation_precedent
        
        # === ANALYSES DÉTAILLÉES ===
        
        # Top Clients VIP (par CA) - basé sur commandes livrées
        top_clients_data = []
        commandes_avec_ca = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            etats__enum_etat__libelle__iexact='Livrée'
        ).values('client_id').annotate(
            ca_total=Sum('total_cmd'),
            nb_commandes=Count('id')
        ).order_by('-ca_total')[:5]
        
        for client_data in commandes_avec_ca:
            try:
                client = Client.objects.get(id=client_data['client_id'])
                ca_total = float(client_data['ca_total']) if client_data['ca_total'] else 0
                # Formatage français avec espaces comme séparateurs de milliers
                ca_total_format = f"{ca_total:,.0f}".replace(',', ' ') + " DH" if ca_total > 0 else "0 DH"
                
                top_clients_data.append({
                    'nom': f"{client.prenom} {client.nom[0]}." if client.nom else "Client anonyme",
                    'ca_total': ca_total,
                    'ca_total_format': ca_total_format,
                    'nb_commandes': client_data['nb_commandes']
                })
            except Client.DoesNotExist:
                continue
          # Performance mensuelle
        # Commandes du mois en cours (livrées uniquement)
        commandes_mois_actuel = Commande.objects.filter(
            date_cmd__gte=debut_mois,
            date_cmd__lte=aujourd_hui,
            etats__enum_etat__libelle__iexact='Livrée'
        ).count()
        
        # CA moyen par client actif - CALCUL CORRECT basé sur commandes livrées
        # Utiliser le CA total de TOUS les clients actifs, pas seulement le top 5
        ca_total_tous_clients_actifs = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            client_id__in=clients_actifs_ids,
            etats__enum_etat__libelle__iexact='Livrée'
        ).aggregate(ca_total=Sum('total_cmd'))['ca_total'] or 0
        
        ca_moyen_par_client = ca_total_tous_clients_actifs / clients_actifs_30j if clients_actifs_30j > 0 else 0
        
        # Segmentation comportementale adaptée (basée sur 90 jours pour plus de pertinence) - commandes livrées
        clients_reguliers = sum(1 for client_id in clients_actifs_90j_ids 
                              if Commande.objects.filter(
                                  client_id=client_id, 
                                  date_cmd__gte=debut_90j,
                                  etats__enum_etat__libelle__iexact='Livrée'
                              ).count() >= 3)
        
        clients_nouveaux_testeurs = Client.objects.filter(
            date_creation__date__gte=debut_90j
        ).filter(
            id__in=clients_actifs_90j_ids
        ).count()
        
        clients_occasionnels = sum(1 for client_id in clients_actifs_90j_ids 
                                 if Commande.objects.filter(
                                     client_id=client_id, 
                                     date_cmd__gte=debut_90j,
                                     etats__enum_etat__libelle__iexact='Livrée'
                                 ).count() == 2)
        
        clients_vip = len(top_clients_data)
        total_clients_analyse = clients_actifs_90j
        
        # Réponse JSON structurée
        data = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'kpis_principaux': {
                'nouveaux_clients': {
                    'valeur': nouveaux_clients_mois,
                    'valeur_formatee': str(nouveaux_clients_mois),
                    'tendance': difference_nouveaux,
                    'unite': 'clients',
                    'label': 'Nouveaux Clients',
                    'sub_value': f"ce mois"
                },
                'clients_actifs': {
                    'valeur': clients_actifs_30j,
                    'valeur_formatee': f"{clients_actifs_30j:,}",
                    'tendance': difference_actifs,
                    'unite': 'clients',
                    'label': 'Clients Actifs',
                    'sub_value': f"{pourcentage_actifs:.1f}% du total clients"
                },
                'taux_retour': {
                    'valeur': round(taux_retour, 1),
                    'valeur_formatee': f"{taux_retour:.1f}",
                    'tendance': round(tendance_retour, 1),
                    'unite': '%',
                    'label': 'Taux Retour',
                    'sub_value': f"{commandes_retournees}/{commandes_livrees_30j} retournées",
                    'status': 'good' if taux_retour < 5 else 'warning' if taux_retour < 10 else 'critical'
                },                'satisfaction': {
                    'valeur': round(taux_fidelisation, 1),
                    'valeur_formatee': f"{taux_fidelisation:.1f}",
                    'tendance': round(tendance_fidelisation, 1),
                    'unite': '%',
                    'label': 'Fidélisation',
                    'sub_value': f"{clients_fideles_90j}/{clients_actifs_90j} clients fidèles (90j)",
                    'status': 'excellent' if taux_fidelisation >= 25 else 'good' if taux_fidelisation >= 15 else 'warning' if taux_fidelisation >= 8 else 'critical'
                },
                'fidelisation': {
                    'valeur': round(taux_fidelisation, 1),
                    'valeur_formatee': f"{taux_fidelisation:.1f}",
                    'tendance': round(tendance_fidelisation, 1),
                    'unite': '%',
                    'label': 'Fidélisation',
                    'sub_value': f"{clients_fideles_90j}/{clients_actifs_90j} clients fidèles (90j)"
                }
            },
            'analyses_detaillees': {
                'top_clients_vip': top_clients_data,
                'performance_mensuelle': {
                    'commandes_mois': commandes_mois_actuel,
                    'ca_par_client': round(ca_moyen_par_client, 2)
                },
                'segmentation': {
                    'acheteurs_reguliers': round((clients_reguliers / total_clients_analyse * 100), 1) if total_clients_analyse > 0 else 0,
                    'nouveaux_testeurs': round((clients_nouveaux_testeurs / total_clients_analyse * 100), 1) if total_clients_analyse > 0 else 0,
                    'clients_occasionnels': round((clients_occasionnels / total_clients_analyse * 100), 1) if total_clients_analyse > 0 else 0,
                    'vip_premium': round((clients_vip / total_clients_analyse * 100), 1) if total_clients_analyse > 0 else 0
                }
            },
            'stats_globales': {
                'total_clients': total_clients,
                'clients_actifs_30j': clients_actifs_30j,
                'taux_activite': round((clients_actifs_30j / total_clients * 100), 1) if total_clients > 0 else 0,
                'commandes_total_30j': commandes_livrees_30j,
                'panier_moyen_clients': round(ca_moyen_par_client, 2)  # Utiliser le CA moyen calculé correctement
            },
            'empty': total_clients == 0
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du chargement des données Clients',
            'empty': True
        }, status=500)

@login_required
def vue_quantitative_data(request):
    """API pour les données de l'onglet État des commandes"""
    try:
        # Obtenir la date actuelle et la période demandée
        aujourd_hui = timezone.now().date()
        period = request.GET.get('period', 'aujourd_hui')  # Par défaut aujourd'hui
        
        # Calculer la date de début selon la période
        if period == 'aujourd_hui':
            date_debut = aujourd_hui
            date_fin = aujourd_hui
            jours = 1
        elif period == 'ce_mois':
            # Premier jour du mois actuel jusqu'à aujourd'hui
            date_debut = aujourd_hui.replace(day=1)
            date_fin = aujourd_hui
            jours = (date_fin - date_debut).days + 1
        elif period == 'cette_annee':
            # Premier jour de l'année actuelle jusqu'à aujourd'hui
            date_debut = aujourd_hui.replace(month=1, day=1)
            date_fin = aujourd_hui
            jours = (date_fin - date_debut).days + 1
        elif period.startswith('custom:'):
            # Période personnalisée format: custom:YYYY-MM-DD:YYYY-MM-DD
            try:
                parts = period.split(':')
                if len(parts) == 3:
                    from datetime import datetime
                    date_debut = datetime.strptime(parts[1], '%Y-%m-%d').date()
                    date_fin = datetime.strptime(parts[2], '%Y-%m-%d').date()
                    jours = (date_fin - date_debut).days + 1
                else:
                    raise ValueError("Format de période personnalisée invalide")
            except (ValueError, IndexError) as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Format de période personnalisée invalide: {str(e)}',
                    'error': 'invalid_custom_period'
                }, status=400)
        else:
            # Fallback vers l'ancien système pour compatibilité
            period_days = {
                '7j': 7,
                '30j': 30,
                '90j': 90,
                '180j': 180,
                '365j': 365
            }
            
            jours = period_days.get(period, 30)  # Défaut à 30 jours si période inconnue
            date_debut = aujourd_hui - timedelta(days=jours)
            date_fin = aujourd_hui
        
        # Récupérer toutes les commandes dans la période avec leur état actuel (dernier état non terminé)
        # On utilise une sous-requête pour obtenir l'état le plus récent pour chaque commande
        commandes_avec_etat = Commande.objects.filter(
            date_cmd__gte=date_debut,  # Filtrer par période
            date_cmd__lte=date_fin,
            etats__date_fin__isnull=True  # États actuels (non terminés)
        ).select_related('etats__enum_etat').values(
            'id',
            'num_cmd',
            'etats__enum_etat__libelle'
        )
        
        # Initialiser les compteurs pour tous les états requis
        etats_compteurs = {
            'recue': 0,
            'affectee': 0, 
            'non_affectee': 0,
            'erronnee': 0,
            'doublon': 0,
            'en_cours_confirmation': 0,
            'confirmee': 0,
            'en_cours_preparation': 0,
            'preparee': 0,  # État intermédiaire à identifier
            'en_cours_livraison': 0,
            'livree': 0,
            'retournee': 0
        }
        
        # Mapping des libellés de la base vers nos clés standardisées
        mapping_etats = {
            'Non affectée': 'non_affectee',
            'Affectée': 'affectee',
            'En cours de confirmation': 'en_cours_confirmation',
            'Confirmée': 'confirmee',
            'Erronée': 'erronnee',
            'Doublon': 'doublon',
            'En préparation': 'en_cours_preparation',
            'En livraison': 'en_cours_livraison',
            'Livrée': 'livree',
            'Retournée': 'retournee',
            'Reçue': 'recue',  # Si cet état existe
            'Préparée': 'preparee'  # Si cet état existe
        }
        
        # Compter les commandes par état
        for commande in commandes_avec_etat:
            libelle_etat = commande['etats__enum_etat__libelle']
            if libelle_etat in mapping_etats:
                cle_etat = mapping_etats[libelle_etat]
                etats_compteurs[cle_etat] += 1
        
        # Pour les commandes sans état défini dans la période, les considérer comme "reçues"
        commandes_sans_etat = Commande.objects.filter(
            date_cmd__gte=date_debut,
            date_cmd__lte=date_fin,
            etats__isnull=True
        ).count()
        
        etats_compteurs['recue'] += commandes_sans_etat
        
        # Calculer le total des commandes
        total_commandes = sum(etats_compteurs.values())
        
        # Note: jours est déjà calculé plus haut dans la fonction
        
        # Ajouter des statistiques supplémentaires
        stats_supplementaires = {
            'commandes_en_cours': (
                etats_compteurs['affectee'] + 
                etats_compteurs['en_cours_confirmation'] + 
                etats_compteurs['en_cours_preparation'] + 
                etats_compteurs['en_cours_livraison']
            ),
            'commandes_problematiques': (
                etats_compteurs['erronnee'] + 
                etats_compteurs['doublon'] + 
                etats_compteurs['retournee']
            ),
            'commandes_completees': etats_compteurs['livree']
        }
        
        # Données de réponse
        response_data = {
            'success': True,
            'data': {
                'etats_commandes': etats_compteurs,
                'stats_supplementaires': stats_supplementaires,
                'total_commandes': total_commandes,
                'periode': {
                    'libelle': period,
                    'jours': jours,
                    'date_debut': date_debut.isoformat(),
                    'date_fin': date_fin.isoformat()
                },
                'derniere_maj': timezone.now().isoformat()
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du calcul des états de commandes : {str(e)}',
            'error': 'erreur_calcul_etats'
        }, status=500)

@login_required
def performance_operateurs_data(request):
    """
    API pour les données de l'onglet Performance Opérateurs
    Basé sur l'état ACTUEL des commandes, pas sur l'historique
    """
    try:
        export_format = request.GET.get('export')
        
        # Construire la requête des opérateurs - Focus sur CONFIRMATION uniquement
        operateurs_query = Operateur.objects.filter(type_operateur='CONFIRMATION')
        
        # Récupérer tous les opérateurs avec leurs données
        operateurs_data = []
        
        # Métriques globales
        total_commandes_affectees_global = 0
        total_commandes_confirmees_global = 0
        operateurs_actifs = 0
        
        for operateur in operateurs_query:
            # === ÉTAT ACTUEL DES COMMANDES ===
            
            # 1. Commandes ACTUELLEMENT affectées à l'opérateur
            # (ayant un état actuel "Affectée" avec cet opérateur)
            commandes_affectees = Commande.objects.filter(
                etats__operateur=operateur,
                etats__enum_etat__libelle__iexact='Affectée',
                etats__date_fin__isnull=True  # État actuel (non terminé)
            ).distinct().count()
            
            # 2. Commandes ACTUELLEMENT en cours de confirmation par l'opérateur
            # (ayant un état actuel "En cours de confirmation" avec cet opérateur)
            commandes_en_cours_confirmation = Commande.objects.filter(
                etats__operateur=operateur,
                etats__enum_etat__libelle__iexact='En cours de confirmation',
                etats__date_fin__isnull=True  # État actuel (non terminé)
            ).distinct().count()
            
            # 3. Commandes CONFIRMÉES par l'opérateur (état historique)
            # Ici on compte TOUTES les commandes que cet opérateur a confirmées
            commandes_confirmees = Commande.objects.filter(
                etats__operateur=operateur,
                etats__enum_etat__libelle__iexact='Confirmée'
            ).distinct().count()
            
            # 4. Calcul du taux de confirmation
            # Total des commandes traitées = affectées + en cours + confirmées
            total_commandes_traitees = commandes_affectees + commandes_en_cours_confirmation + commandes_confirmees
            
            if total_commandes_traitees > 0:
                taux_confirmation = (commandes_confirmees / total_commandes_traitees) * 100
            else:
                taux_confirmation = 0
            
            # 5. Actions réalisées par l'opérateur (toutes les opérations)
            total_actions = Operation.objects.filter(
                operateur=operateur
            ).count()
            
            # 6. Moyenne d'actions par confirmation
            if commandes_confirmees > 0:
                actions_par_confirmation = total_actions / commandes_confirmees
            else:
                actions_par_confirmation = 0
            
            # 6bis. Calcul du nombre moyen d'opérations par commande confirmée sur 30 jours
            date_limite_30j = timezone.now() - timedelta(days=30)
            
            # Commandes confirmées dans les 30 derniers jours
            commandes_confirmees_30j = Commande.objects.filter(
                etats__operateur=operateur,
                etats__enum_etat__libelle__iexact='Confirmée',
                etats__date_debut__gte=date_limite_30j
            ).distinct().count()
            
            # Opérations effectuées dans les 30 derniers jours
            operations_30j = Operation.objects.filter(
                operateur=operateur,
                date_operation__gte=date_limite_30j
            ).count()
            
            # Calcul du nombre moyen d'opérations par commande confirmée sur 30j
            if commandes_confirmees_30j > 0:
                operations_par_commande_30j = operations_30j / commandes_confirmees_30j
            else:
                operations_par_commande_30j = 0
            
            # 7. Calcul du panier moyen pour les commandes confirmées
            panier_stats = Commande.objects.filter(
                etats__operateur=operateur,
                etats__enum_etat__libelle__iexact='Confirmée'
            ).aggregate(
                panier_moyen=Avg('total_cmd'),
                panier_min=Min('total_cmd'),
                panier_max=Max('total_cmd')
            )
            
            panier_moyen = panier_stats['panier_moyen'] or 0
            panier_min = panier_stats['panier_min'] or 0
            panier_max = panier_stats['panier_max'] or 0
            
            # 8. Nombre d'upsells réalisés
            upsells_count = Commande.objects.filter(
                etats__operateur=operateur,
                etats__enum_etat__libelle__iexact='Confirmée',
                is_upsell=True
            ).count()
            
            # 9. Moyenne du nombre d'articles par commande confirmée
            try:
                from commande.models import Panier
                avg_articles = Commande.objects.filter(
                    etats__operateur=operateur,
                    etats__enum_etat__libelle__iexact='Confirmée'
                ).annotate(
                    nb_articles=Sum('paniers__quantite')
                ).aggregate(
                    moyenne_articles=Avg('nb_articles')
                )['moyenne_articles'] or 0
            except (ImportError, Exception):
                avg_articles = 0
            
            # Marquer comme actif si l'opérateur a des commandes à traiter ou a traité des commandes
            is_active = (commandes_affectees + commandes_en_cours_confirmation + commandes_confirmees) > 0
            if is_active:
                operateurs_actifs += 1
            
            # Accumuler pour les métriques globales
            total_commandes_affectees_global += commandes_affectees + commandes_en_cours_confirmation
            total_commandes_confirmees_global += commandes_confirmees
            
            operateurs_data.append({
                'id': operateur.id,
                'nom': operateur.nom,
                'username': operateur.user.username if operateur.user else 'N/A',
                'type': operateur.type_operateur,
                
                # État actuel des commandes
                'commands_affected': commandes_affectees,  # Actuellement affectées
                'commands_in_progress': commandes_en_cours_confirmation,  # En cours de confirmation
                'commands_confirmed': commandes_confirmees,  # Total confirmées (historique)
                
                # Métriques de performance
                'confirmation_rate': round(taux_confirmation, 1),
                'total_actions': total_actions,
                'actions_per_confirmation': round(actions_par_confirmation, 1),
                'operations_per_command_30d': round(operations_par_commande_30j, 1),  # Nouveau calcul
                
                # Métriques financières
                'average_basket': float(panier_moyen),
                'min_basket': float(panier_min),
                'max_basket': float(panier_max),
                'upsell_count': upsells_count,
                
                # Autres métriques
                'avg_articles_per_cmd': float(avg_articles),
                'is_active': is_active
            })
        
        # Calculer le taux de confirmation global
        if (total_commandes_affectees_global + total_commandes_confirmees_global) > 0:
            taux_confirmation_global = (total_commandes_confirmees_global / 
                                       (total_commandes_affectees_global + total_commandes_confirmees_global)) * 100
        else:
            taux_confirmation_global = 0
        
        # Métriques globales
        global_metrics = {
            'commands_assigned': total_commandes_affectees_global,
            'confirmations': total_commandes_confirmees_global,
            'global_confirmation_rate': round(taux_confirmation_global, 1),
            'active_operators': operateurs_actifs
        }
        
        # Trier par nombre de commandes confirmées (performance) décroissant
        operateurs_data.sort(key=lambda x: x['commands_confirmed'], reverse=True)
        
        # Si export Excel demandé
        if export_format == 'excel':
            return export_performance_operateurs_excel(operateurs_data, global_metrics, timezone.now().date(), timezone.now().date())
        
        # Réponse JSON normale
        response_data = {
            'success': True,
            'operators': operateurs_data,
            'global_metrics': global_metrics,
            'period_info': {
                'description': 'État actuel des commandes (temps réel)',
                'note': 'Les données reflètent l\'état actuel des commandes, pas un historique sur période'
            },
            'last_update': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors du calcul des performances des opérateurs : {str(e)}',
            'error': 'erreur_calcul_performance'
        }, status=500)

def export_performance_operateurs_excel(operateurs_data, global_metrics, date_debut, date_fin):
    """Export des données de performance des opérateurs en Excel (format TSV)"""
    try:
        # Création du contenu TSV avec BOM UTF-8
        content = '\ufeff'  # BOM UTF-8
        
        # En-tête du fichier
        content += f"Performance des Opérateurs de Confirmation\t\t\t\t\t\t\t\t\n"
        content += f"État actuel des commandes (temps réel)\t\t\t\t\t\t\t\t\t\n"
        content += f"Généré le: {timezone.now().strftime('%d/%m/%Y à %H:%M')}\t\t\t\t\t\t\t\t\t\n"
        content += "\t\t\t\t\t\t\t\t\t\n"
        
        # Métriques globales
        content += "MÉTRIQUES GLOBALES\t\t\t\t\t\t\t\t\t\n"
        content += f"Commandes Assignées\t{global_metrics['commands_assigned']}\t\t\t\t\t\t\t\t\n"
        content += f"Total Confirmations\t{global_metrics['confirmations']}\t\t\t\t\t\t\t\t\n"
        content += f"Taux Confirmation Global\t{global_metrics['global_confirmation_rate']}%\t\t\t\t\t\t\t\t\n"
        content += f"Opérateurs Actifs\t{global_metrics['active_operators']}\t\t\t\t\t\t\t\t\n"
        content += "\t\t\t\t\t\t\t\t\t\n"
        
        # En-têtes du tableau mis à jour
        content += "DÉTAIL PAR OPÉRATEUR\t\t\t\t\t\t\t\t\t\t\t\n"
        content += "Opérateur\tCmds Affectées\tEn Cours Confirm.\tCmds Confirmées\tTaux Confirm. (%)\tActions Totales\tActions/Confirm.\tNb Upsell\tPanier Moyen (MAD)\tPanier Max (MAD)\tPanier Min (MAD)\tMoy. Articles\n"
        
        # Données des opérateurs
        for operateur in operateurs_data:
            content += f"{operateur['nom']}\t"
            content += f"{operateur['commands_affected']}\t"
            content += f"{operateur['commands_in_progress']}\t"
            content += f"{operateur['commands_confirmed']}\t"
            content += f"{operateur['confirmation_rate']}\t"
            content += f"{operateur['total_actions']}\t"
            content += f"{operateur['actions_per_confirmation']}\t"
            content += f"{operateur['upsell_count']}\t"
            content += f"{operateur['average_basket']:.2f}\t"
            content += f"{operateur['max_basket']:.2f}\t"
            content += f"{operateur['min_basket']:.2f}\t"
            content += f"{operateur['avg_articles_per_cmd']:.1f}\n"
        
        # Configuration de la réponse HTTP
        response = HttpResponse(content, content_type='text/tab-separated-values; charset=utf-8-sig')
        
        # Nom du fichier avec date
        filename = f"performance_operateurs_etat_actuel_{timezone.now().strftime('%Y%m%d_%H%M')}.txt"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de l\'export Excel : {str(e)}',
            'error': 'erreur_export_excel'
        }, status=500)

@api_login_required
def operator_history_data(request):
    """API pour récupérer l'historique récent d'un opérateur"""
    try:
        # Paramètres de la requête
        operator_id = request.GET.get('operator_id')
        period = request.GET.get('period', 'today')
        limit = int(request.GET.get('limit', 5))
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if not operator_id:
            return JsonResponse({
                'success': False,
                'message': 'ID opérateur manquant',
                'error': 'missing_operator_id'
            }, status=400)
        
        # Vérifier que l'opérateur existe
        try:
            operateur = Operateur.objects.get(id=operator_id)
        except Operateur.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Opérateur introuvable',
                'error': 'operator_not_found'
            }, status=404)
        
        # Calculer les dates selon la période (même logique que performance_operateurs_data)
        aujourd_hui = timezone.now().date()
        
        if period == 'custom' and start_date and end_date:
            try:
                date_debut = datetime.strptime(start_date, '%Y-%m-%d').date()
                date_fin = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'message': 'Format de date invalide',
                    'error': 'invalid_date_format'
                }, status=400)
        else:
            # Périodes prédéfinies
            if period == 'today':
                date_debut = aujourd_hui
                date_fin = aujourd_hui
            elif period == 'yesterday':
                hier = aujourd_hui - timedelta(days=1)
                date_debut = hier
                date_fin = hier
            elif period == 'week':
                date_debut = aujourd_hui - timedelta(days=7)
                date_fin = aujourd_hui
            elif period == 'month':
                date_debut = aujourd_hui.replace(day=1)
                date_fin = aujourd_hui
            elif period == 'quarter':
                # Début du trimestre actuel
                mois_actuel = aujourd_hui.month
                if mois_actuel <= 3:
                    debut_trimestre = aujourd_hui.replace(month=1, day=1)
                elif mois_actuel <= 6:
                    debut_trimestre = aujourd_hui.replace(month=4, day=1)
                elif mois_actuel <= 9:
                    debut_trimestre = aujourd_hui.replace(month=7, day=1)
                else:
                    debut_trimestre = aujourd_hui.replace(month=10, day=1)
                date_debut = debut_trimestre
                date_fin = aujourd_hui
            elif period == 'year':
                date_debut = aujourd_hui.replace(month=1, day=1)
                date_fin = aujourd_hui
            else:
                # Défaut aujourd'hui
                date_debut = aujourd_hui
                date_fin = aujourd_hui
        
        # Récupérer les opérations récentes de l'opérateur
        operations = Operation.objects.filter(
            operateur=operateur,
            date_operation__date__gte=date_debut,
            date_operation__date__lte=date_fin
        ).select_related('commande').order_by('-date_operation')[:limit]
        
        # Formater les données
        history_data = []
        for operation in operations:
            history_data.append({
                'id': operation.id,
                'type_operation': operation.get_type_operation_display(),
                'commande_num': operation.commande.num_cmd,
                'date_operation': operation.date_operation.isoformat(),
                'conclusion': operation.conclusion[:100] + '...' if len(operation.conclusion) > 100 else operation.conclusion,
                'status': 'Terminé'  # Peut être étendu selon la logique métier
            })
        
        return JsonResponse({
            'success': True,
            'history': history_data,
            'operator': {
                'id': operateur.id,
                'nom': operateur.nom,
                'type': operateur.type_operateur
            },
            'period_info': {
                'start_date': date_debut.isoformat(),
                'end_date': date_fin.isoformat(),
                'period': period
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la récupération de l\'historique : {str(e)}',
            'error': 'erreur_historique'
        }, status=500)

@login_required
def dashboard(request):
    """Page principale du dashboard KPIs"""
    return render(request, 'kpis/dashboard.html')
