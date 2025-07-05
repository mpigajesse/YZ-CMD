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
from .models import KPIConfiguration  # Assurez-vous d'importer votre modèle de configuration

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
def vue_generale_data(request):
    """API pour les données de l'onglet Vue Générale"""
    try:
        # Dates de référence
        aujourd_hui = timezone.now().date()
        debut_mois = aujourd_hui.replace(day=1)
        mois_precedent = (debut_mois - timedelta(days=1)).replace(day=1)
        debut_30j = aujourd_hui - timedelta(days=30)  # Défini ici pour être utilisé partout
        
        # === KPI 1: Chiffre d'Affaires du Mois ===
        ca_mois_actuel = Commande.objects.filter(
            date_cmd__gte=debut_mois,
            date_cmd__lte=aujourd_hui
        ).exclude(
            etats__enum_etat__libelle__iexact='Annulée',
            etats__date_fin__isnull=True
        ).aggregate(total=Sum('total_cmd'))['total'] or 0
        
        # CA mois précédent pour comparaison
        ca_mois_precedent = Commande.objects.filter(
            date_cmd__gte=mois_precedent,
            date_cmd__lt=debut_mois
        ).exclude(
            etats__enum_etat__libelle__iexact='Annulée',
            etats__date_fin__isnull=True
        ).aggregate(total=Sum('total_cmd'))['total'] or 0
        
        # Calcul de la tendance CA
        if ca_mois_precedent > 0:
            tendance_ca = ((ca_mois_actuel - ca_mois_precedent) / ca_mois_precedent) * 100
        else:
            tendance_ca = 100 if ca_mois_actuel > 0 else 0
        
        # === KPI 2: Commandes du Jour ===
        commandes_jour = Commande.objects.filter(
            date_cmd=aujourd_hui
        ).count()
        
        # Commandes hier pour comparaison
        hier = aujourd_hui - timedelta(days=1)
        commandes_hier = Commande.objects.filter(
            date_cmd=hier
        ).count()
        
        difference_commandes = commandes_jour - commandes_hier
        
        # === KPI 3: Stock Critique (Articles Populaires en Rupture) ===
        # Stratégie intelligente : identifier les articles les plus vendus avec stock faible
        
        # 1. Identifier les articles avec de bonnes ventes sur les 30 derniers jours
        articles_populaires = Article.objects.annotate(
            ventes_recentes=Count(
                'paniers__commande',
                filter=Q(
                    paniers__commande__date_cmd__gte=debut_30j,
                    paniers__commande__date_cmd__lte=aujourd_hui
                ) & ~Q(
                    paniers__commande__etats__enum_etat__libelle__iexact='Annulée'
                )
            )
        ).filter(
            actif=True,
            ventes_recentes__gte=2  # Au moins 2 ventes dans les 30 derniers jours
        )
        
        # 2. Parmi ces articles populaires, identifier ceux en stock critique
        seuil_critique = 5  # Stock critique si < 5 unités pour un article populaire
        articles_critiques = articles_populaires.filter(
            qte_disponible__lt=seuil_critique
        ).count()
        
        # Total des articles populaires (pour calculer le pourcentage)
        total_articles_populaires = articles_populaires.count()
        
        # 3. Calcul de la tendance basée sur le pourcentage d'articles critiques
        if total_articles_populaires > 0:
            pourcentage_critique = (articles_critiques / total_articles_populaires) * 100
            # Logique business : moins de 10% = bon, 10-25% = attention, plus de 25% = critique
            if pourcentage_critique < 10:
                tendance_stock = -1  # Amélioration (moins d'articles critiques)
            elif pourcentage_critique > 25:
                tendance_stock = 2   # Dégradation (beaucoup d'articles critiques)
            else:
                tendance_stock = 0   # Stable
        else:
            tendance_stock = 0
            pourcentage_critique = 0          # === KPI 4: Taux de Conversion Téléphonique ===
        # Opérations de confirmation des 30 derniers jours
        operations_total = Operation.objects.filter(
            date_operation__gte=debut_30j,
            type_operation__in=['APPEL', 'Appel Whatsapp']
        ).count()
        
        # Commandes confirmées suite à appels (ayant eu état "Confirmée")
        commandes_confirmees = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            etats__enum_etat__libelle__iexact='Confirmée'
        ).distinct().count()
        
        if operations_total > 0:
            taux_conversion = (commandes_confirmees / operations_total) * 100
        else:
            taux_conversion = 0
        
        # Calcul tendance taux conversion (vs période précédente)
        debut_periode_precedente = debut_30j - timedelta(days=30)
        operations_precedentes = Operation.objects.filter(
            date_operation__gte=debut_periode_precedente,
            date_operation__lt=debut_30j,
            type_operation__in=['APPEL', 'Appel Whatsapp']
        ).count()
        
        commandes_confirmees_precedentes = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j,
            etats__enum_etat__libelle__iexact='Confirmée'
        ).distinct().count()
        
        if operations_precedentes > 0:
            taux_conversion_precedent = (commandes_confirmees_precedentes / operations_precedentes) * 100
            tendance_conversion = taux_conversion - taux_conversion_precedent
        else:
            tendance_conversion = 0        # === KPIs Secondaires ===        # Panier Moyen (30 derniers jours)
        panier_moyen = Commande.objects.filter(
            date_cmd__gte=debut_30j
        ).exclude(
            etats__enum_etat__libelle__iexact='Annulée',
            etats__date_fin__isnull=True
        ).aggregate(moyenne=Avg('total_cmd'))['moyenne'] or 0
        
        # Panier moyen période précédente pour calculer la tendance
        panier_moyen_precedent = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j
        ).exclude(
            etats__enum_etat__libelle__iexact='Annulée',
            etats__date_fin__isnull=True
        ).aggregate(moyenne=Avg('total_cmd'))['moyenne'] or 0
        
        # Tendance panier moyen
        if panier_moyen_precedent > 0:
            tendance_panier = ((panier_moyen - panier_moyen_precedent) / panier_moyen_precedent) * 100
        else:
            tendance_panier = 100 if panier_moyen > 0 else 0
          # === Délai Livraison Moyen (basé sur les vraies données) ===
        # Calculer le délai moyen pour les commandes livrées récemment
        
        # 1. Récupérer les commandes livrées avec leur date de livraison
        commandes_livrees_avec_delai = Commande.objects.filter(
            date_cmd__gte=debut_30j,  # Commandes des 30 derniers jours
            etats__enum_etat__libelle__iexact='Livrée'
        ).annotate(
            date_livraison=Min(
                'etats__date_debut',
                filter=Q(etats__enum_etat__libelle__iexact='Livrée')
            )
        ).filter(
            date_livraison__isnull=False  # S'assurer qu'on a une date de livraison
        )
        
        # 2. Calculer le délai pour chaque commande
        delais = []
        for commande in commandes_livrees_avec_delai:
            if commande.date_livraison:
                # Convertir date_cmd en datetime pour le calcul
                date_cmd_dt = timezone.make_aware(
                    datetime.combine(commande.date_cmd, datetime.min.time())
                )
                delai_jours = (commande.date_livraison - date_cmd_dt).days
                if delai_jours >= 0:  # Éviter les délais négatifs (données incohérentes)
                    delais.append(delai_jours)
        
        # 3. Calculer la moyenne des délais
        if delais:
            delai_moyen = sum(delais) / len(delais)
            nb_livraisons = len(delais)
              # Calcul de la tendance (vs période précédente)
            commandes_precedentes = Commande.objects.filter(
                date_cmd__gte=debut_periode_precedente,
                date_cmd__lt=debut_30j,
                etats__enum_etat__libelle__iexact='Livrée'
            ).annotate(
                date_livraison=Min(
                    'etats__date_debut',
                    filter=Q(etats__enum_etat__libelle__iexact='Livrée')
                )
            ).filter(date_livraison__isnull=False)
            
            delais_precedents = []
            for cmd in commandes_precedentes:
                if cmd.date_livraison:
                    date_cmd_dt = timezone.make_aware(
                        datetime.combine(cmd.date_cmd, datetime.min.time())
                    )
                    delai = (cmd.date_livraison - date_cmd_dt).days
                    if delai >= 0:
                        delais_precedents.append(delai)
            
            if delais_precedents:
                delai_moyen_precedent = sum(delais_precedents) / len(delais_precedents)
                tendance_delai = delai_moyen - delai_moyen_precedent
            else:
                tendance_delai = 0
        else:
            # Aucune donnée disponible : utiliser une valeur par défaut réaliste
            delai_moyen = 3.0  # 3 jours par défaut pour le e-commerce
            nb_livraisons = 0
            tendance_delai = 0
          # === Satisfaction Client (basée sur le taux de retour) ===
        # Commandes livrées avec succès
        commandes_livrees = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            etats__enum_etat__libelle__iexact='Livrée'
        ).distinct().count()
        
        # Commandes retournées (signe d'insatisfaction)
        commandes_retournees = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            etats__enum_etat__libelle__iexact='Retournée'
        ).distinct().count()
          # Calcul satisfaction intelligente (sur 5)
        if commandes_livrees > 0:
            taux_retour = (commandes_retournees / commandes_livrees) * 100
            # Satisfaction basée sur le taux de retour avec une échelle plus réaliste
            # Formule : Satisfaction = 5 - (taux_retour * facteur_impact)
            # Échelle e-commerce réaliste :
            # 0-5% retours = Excellent (4.5-5.0)
            # 5-10% retours = Très bon (4.0-4.5) 
            # 10-15% retours = Bon (3.25-4.0)
            # 15-25% retours = Moyen (2.5-3.25)
            # >25% retours = Mauvais (<2.5)
            facteur_impact = 0.15  # Chaque % de retour enlève 0.15 point (plus strict)
            satisfaction = max(1.0, 5.0 - (taux_retour * facteur_impact))
            
            # Calcul tendance (vs période précédente)
            commandes_livrees_precedentes = Commande.objects.filter(
                date_cmd__gte=debut_periode_precedente,
                date_cmd__lt=debut_30j,
                etats__enum_etat__libelle__iexact='Livrée'
            ).distinct().count()
            
            commandes_retournees_precedentes = Commande.objects.filter(
                date_cmd__gte=debut_periode_precedente,
                date_cmd__lt=debut_30j,
                etats__enum_etat__libelle__iexact='Retournée'
            ).distinct().count()
            
            if commandes_livrees_precedentes > 0:
                taux_retour_precedent = (commandes_retournees_precedentes / commandes_livrees_precedentes) * 100
                satisfaction_precedente = max(1.0, 5.0 - (taux_retour_precedent * facteur_impact))
                tendance_satisfaction = satisfaction - satisfaction_precedente
            else:
                tendance_satisfaction = 0
        else:
            satisfaction = 5.0  # Aucune donnée = parfait par défaut
            taux_retour = 0
            tendance_satisfaction = 0
          # Taux de Confirmation (commandes confirmées / commandes affectées)
        commandes_affectees_30j_total = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            etats__enum_etat__libelle__iexact='Affectée'
        ).distinct().count()
        
        commandes_confirmees_30j_total = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            etats__enum_etat__libelle__iexact='Confirmée'
        ).distinct().count()
        
        if commandes_affectees_30j_total > 0:
            taux_confirmation = (commandes_confirmees_30j_total / commandes_affectees_30j_total) * 100
        else:
            taux_confirmation = 0
        
        # Taux de confirmation période précédente
        commandes_affectees_precedent_total = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j,
            etats__enum_etat__libelle__iexact='Affectée'
        ).distinct().count()
        
        commandes_confirmees_precedent_total = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j,
            etats__enum_etat__libelle__iexact='Confirmée'
        ).distinct().count()
        
        if commandes_affectees_precedent_total > 0:
            taux_confirmation_precedent = (commandes_confirmees_precedent_total / commandes_affectees_precedent_total) * 100
            tendance_taux_confirmation = taux_confirmation - taux_confirmation_precedent
        else:
            tendance_taux_confirmation = taux_confirmation if taux_confirmation > 0 else 0
        
        # === Données géographiques (Performance par Région) ===
        # Top 5 villes par CA - 30 derniers jours
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
        
        # Réponse JSON
        data = {
            'success': True,
            'timestamp': timezone.now().isoformat(),
            'kpis_principaux': {                'ca_mois': {
                    'valeur': float(ca_mois_actuel),
                    'valeur_formatee': f"{ca_mois_actuel:,.0f}",
                    'tendance': round(tendance_ca, 1),
                    'unite': 'DH',
                    'label': "Chiffre d'Affaires",
                    'sub_value': f"vs mois dernier ({ca_mois_precedent:,.0f} DH)"
                },
                'commandes_jour': {
                    'valeur': commandes_jour,
                    'valeur_formatee': str(commandes_jour),
                    'tendance': difference_commandes,
                    'unite': 'commandes',
                    'label': 'Commandes du Jour',
                    'sub_value': f"vs hier ({commandes_hier} commandes)"
                },                'stock_critique': {
                    'valeur': articles_critiques,
                    'valeur_formatee': str(articles_critiques),
                    'total_articles': total_articles_populaires,
                    'pourcentage_critique': round(pourcentage_critique, 1),
                    'tendance': tendance_stock,
                    'unite': 'articles',
                    'label': 'Stock Critique',
                    'status': 'critical' if articles_critiques > 3 else 'warning' if articles_critiques > 0 else 'good',
                    'sub_value': f"sur {total_articles_populaires} articles populaires ({pourcentage_critique:.1f}%)"
                },
                'taux_conversion': {
                    'valeur': round(taux_conversion, 1),
                    'valeur_formatee': f"{taux_conversion:.1f}",
                    'tendance': round(tendance_conversion, 1),
                    'unite': '%',
                    'label': 'Taux Conversion',
                    'sub_value': f"{commandes_confirmees}/{operations_total} appels confirmés"
                }},
            'kpis_secondaires': {
                    'panier_moyen': {
                    'valeur': float(panier_moyen) if panier_moyen else 0,
                    'valeur_formatee': f"{panier_moyen:.0f}" if panier_moyen else "0",
                    'tendance': round(tendance_panier, 1),
                    'unite': 'DH',
                    'label': 'Panier Moyen',
                    'sub_value': 'ce mois'
                },'delai_livraison': {
                    'valeur': round(delai_moyen, 1),
                    'valeur_formatee': f"{delai_moyen:.1f}",
                    'tendance': round(tendance_delai, 1),
                    'nb_livraisons': nb_livraisons,
                    'unite': 'jours',
                    'label': 'Délai Livraison',
                    'status': 'excellent' if delai_moyen <= 2 else 'good' if delai_moyen <= 3 else 'warning' if delai_moyen <= 5 else 'critical',
                    'sub_value': f"moyenne sur {nb_livraisons} livraisons"
                },                'taux_retour': {
                    'valeur': round(taux_retour, 1),
                    'valeur_formatee': f"{taux_retour:.1f}",
                    'tendance': round(tendance_satisfaction * -1, 2),  # Inverser la tendance car moins de retour = mieux
                    'taux_retour': round(taux_retour, 1),
                    'commandes_livrees': commandes_livrees,
                    'commandes_retournees': commandes_retournees,
                    'unite': '%',
                    'label': 'Taux Retour',
                    'status': 'excellent' if taux_retour <= 5 else 'good' if taux_retour <= 10 else 'warning' if taux_retour <= 15 else 'critical',
                    'sub_value': f"{commandes_retournees}/{commandes_livrees} retours"
                },                'taux_confirmation': {
                    'valeur': round(taux_confirmation, 1),
                    'valeur_formatee': f"{taux_confirmation:.1f}",
                    'tendance': round(tendance_taux_confirmation, 1),
                    'unite': '%',
                    'label': 'Taux Confirmation',
                    'status': 'excellent' if taux_confirmation >= 80 else 'good' if taux_confirmation >= 70 else 'warning' if taux_confirmation >= 60 else 'critical',
                    'sub_value': f'{commandes_confirmees_30j_total}/{commandes_affectees_30j_total} confirmées'
                },
                'ventes_geographique': [
                    {
                        'ville': ville['ville__nom'] or 'Inconnue',
                        'region': ville['ville__region__nom_region'] or 'Inconnue',
                        'ca': float(ville['ca_total']) if ville['ca_total'] else 0,
                        'commandes': ville['nb_commandes'] or 0
                    } for ville in ventes_par_ville
                ]
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du chargement des données KPIs'
        }, status=500)

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
def documentation(request):
    """Page de documentation KPIs"""
    return render(request, 'kpis/documentation.html')

@login_required
def configurations(request):
    """Page de configuration des paramètres KPIs"""
    return render(request, 'kpis/configurations.html')

@login_required
def presentation_parametres(request):
    """Page de présentation détaillée des paramètres KPIs"""
    return render(request, 'kpis/presentation_parametres.html')

@api_login_required
def get_configurations(request):
    """API pour récupérer toutes les configurations KPIs"""
    try:
        configs = KPIConfiguration.objects.all().order_by('categorie', 'nom_parametre')
        
        # Configurations par défaut au cas où la BD serait vide
        default_configs = {
            'seuils': [
                {
                    'id': 'default_stock_critique_seuil',
                    'nom_parametre': 'stock_critique_seuil',
                    'valeur': 5.0,
                    'description': 'Seuil en dessous duquel un article est considéré en stock critique',
                    'unite': 'unités',
                    'valeur_min': 0,
                    'valeur_max': 100
                },
                {
                    'id': 'default_taux_conversion_objectif',
                    'nom_parametre': 'taux_conversion_objectif',
                    'valeur': 70.0,
                    'description': 'Objectif de taux de conversion (confirmations/appels)',
                    'unite': '%',
                    'valeur_min': 0,
                    'valeur_max': 100
                },
                {
                    'id': 'default_delai_livraison_cible',
                    'nom_parametre': 'delai_livraison_cible',
                    'valeur': 3.0,
                    'description': 'Délai de livraison cible en jours',
                    'unite': 'jours',
                    'valeur_min': 1,
                    'valeur_max': 30
                },
                {
                    'id': 'default_satisfaction_minimale',
                    'nom_parametre': 'satisfaction_minimale',
                    'valeur': 4.0,
                    'description': 'Score de satisfaction client minimal acceptable',
                    'unite': '/5',
                    'valeur_min': 1,
                    'valeur_max': 5
                }
            ],
            'calcul': [
                {
                    'id': 'default_periode_analyse_defaut',
                    'nom_parametre': 'periode_analyse_defaut',
                    'valeur': 30,
                    'description': 'Période d\'analyse par défaut pour les KPIs',
                    'unite': 'jours',
                    'valeur_min': 1,
                    'valeur_max': 365
                },
                {
                    'id': 'default_article_populaire_seuil',
                    'nom_parametre': 'article_populaire_seuil',
                    'valeur': 2,
                    'description': 'Nombre minimum de ventes pour qu\'un article soit considéré populaire',
                    'unite': 'ventes',
                    'valeur_min': 1,
                    'valeur_max': 50
                },
                {
                    'id': 'default_client_fidele_seuil',
                    'nom_parametre': 'client_fidele_seuil',
                    'valeur': 2,
                    'description': 'Nombre minimum de commandes pour qu\'un client soit considéré fidèle',
                    'unite': 'commandes',
                    'valeur_min': 2,
                    'valeur_max': 10
                },
                {
                    'id': 'default_fidelisation_periode_jours',
                    'nom_parametre': 'fidelisation_periode_jours',
                    'valeur': 90,
                    'description': 'Période en jours pour calculer la fidélisation',
                    'unite': 'jours',
                    'valeur_min': 30,
                    'valeur_max': 365
                }
            ],
            'affichage': [
                {
                    'id': 'default_rafraichissement_auto',
                    'nom_parametre': 'rafraichissement_auto',
                    'valeur': 5,
                    'description': 'Intervalle de rafraîchissement automatique des données',
                    'unite': 'minutes',
                    'valeur_min': 1,
                    'valeur_max': 60
                },
                {
                    'id': 'default_afficher_tendances',
                    'nom_parametre': 'afficher_tendances',
                    'valeur': 1,
                    'description': 'Afficher les indicateurs de tendance (1=Oui, 0=Non)',
                    'unite': 'booléen',
                    'valeur_min': 0,
                    'valeur_max': 1
                },
                {
                    'id': 'default_activer_animations',
                    'nom_parametre': 'activer_animations',
                    'valeur': 1,
                    'description': 'Activer les animations dans l\'interface (1=Oui, 0=Non)',
                    'unite': 'booléen',
                    'valeur_min': 0,
                    'valeur_max': 1
                },
                {
                    'id': 'default_decimales_affichage',
                    'nom_parametre': 'decimales_affichage',
                    'valeur': 1,
                    'description': 'Nombre de décimales à afficher pour les valeurs',
                    'unite': 'décimales',
                    'valeur_min': 0,
                    'valeur_max': 3
                }
            ]
        }
        
        # Mapping des vraies catégories vers les catégories attendues par le frontend
        category_mapping = {
            'seuil': 'seuils',
            'objectif': 'seuils',
            'formule': 'calcul',
            'periode': 'calcul',
            'calcul': 'calcul',
            'affichage': 'affichage',
            'interface': 'affichage',
        }
        
        # Si aucune configuration en BD, utiliser les valeurs par défaut
        if not configs.exists():
            return JsonResponse({
                'success': True,
                'configurations': default_configs,
                'integer_fields': get_integer_fields(),
                'message': 'Configurations par défaut chargées (BD vide)',
                'is_default': True
            })
        
        # Organiser par catégorie mappée
        data = {
            'seuils': [],
            'calcul': [],
            'affichage': []
        }
        
        for config in configs:
            config_data = {
                'id': config.id,
                'nom_parametre': config.nom_parametre,
                'valeur': config.valeur,
                'description': config.description,
                'unite': config.unite,
                'valeur_min': config.valeur_min,
                'valeur_max': config.valeur_max,
            }
            # Mapper la catégorie réelle vers la catégorie frontend
            mapped_category = category_mapping.get(config.categorie, 'calcul')
            if mapped_category in data:
                data[mapped_category].append(config_data)
        
        return JsonResponse({
            'success': True,
            'configurations': data,
            'integer_fields': get_integer_fields(),
            'message': 'Configurations chargées avec succès',
            'is_default': False
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du chargement des configurations'
        }, status=500)

@api_login_required
def save_configurations(request):
    """API pour sauvegarder les configurations KPIs"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        configurations = data.get('configurations', [])
        
        if not configurations:
            return JsonResponse({
                'success': False,
                'message': 'Aucune configuration à sauvegarder'
            }, status=400)
        
        updated_count = 0
        errors = []
        field_errors = {}  # Erreurs spécifiques par champ
        
        for config_data in configurations:
            try:
                config_id = config_data.get('id')
                valeur_raw = config_data.get('valeur', '')
                # Validation numérique
                try:
                    nouvelle_valeur = float(valeur_raw) if valeur_raw != '' else 0.0
                except (ValueError, TypeError):
                    field_errors[str(config_id)] = "Valeur non numérique. Veuillez saisir un nombre."
                    continue
                
                if config_id:
                    config = KPIConfiguration.objects.get(id=config_id)
                    
                    # Validation spécifique pour les champs entiers
                    is_valid_integer, validated_value = validate_integer_value(config.nom_parametre, nouvelle_valeur)
                    if not is_valid_integer:
                        field_errors[str(config_id)] = validated_value  # validated_value contient le message d'erreur
                        continue
                    
                    # Utiliser la valeur validée (peut avoir été convertie en entier)
                    nouvelle_valeur = validated_value
                    config = KPIConfiguration.objects.get(id=config_id)
                    
                    # Valider les limites
                    if config.valeur_min is not None and nouvelle_valeur < config.valeur_min:
                        field_errors[str(config_id)] = f"Valeur trop faible (minimum: {config.valeur_min})"
                        continue
                    
                    if config.valeur_max is not None and nouvelle_valeur > config.valeur_max:
                        field_errors[str(config_id)] = f"Valeur trop élevée (maximum: {config.valeur_max})"
                        continue
                    
                    # Validations métier spécifiques
                    if config.nom_parametre == 'seuil_critique_stock' and nouvelle_valeur < 0:
                        field_errors[str(config_id)] = "Le seuil de stock critique ne peut pas être négatif"
                        continue
                        
                    if config.nom_parametre == 'taux_conversion_cible' and (nouvelle_valeur < 0 or nouvelle_valeur > 100):
                        field_errors[str(config_id)] = "Le taux de conversion doit être entre 0 et 100%"
                        continue
                        
                    if config.nom_parametre in ['delai_livraison_cible', 'periode_analyse_defaut'] and nouvelle_valeur <= 0:
                        field_errors[str(config_id)] = "Cette valeur doit être strictement positive"
                        continue
                    
                    # Mettre à jour
                    config.valeur = nouvelle_valeur
                    config.modifie_par = request.user
                    config.save()
                    updated_count += 1
                    
            except KPIConfiguration.DoesNotExist:
                errors.append(f"Configuration {config_id} introuvable")
            except ValueError as e:
                if config_id:
                    field_errors[str(config_id)] = "Valeur numérique invalide"
                else:
                    errors.append(f"Valeur invalide: {str(e)}")
        
        # S'il y a des erreurs de validation sur des champs spécifiques
        if field_errors:
            return JsonResponse({
                'success': False,
                'message': f"Erreurs de validation détectées sur {len(field_errors)} champ(s)",
                'field_errors': field_errors,
                'errors': errors,
                'updated_count': updated_count
            }, status=400)
        
        # S'il y a des erreurs générales seulement
        if errors:
            return JsonResponse({
                'success': False,
                'message': f"{updated_count} configurations sauvegardées, {len(errors)} erreurs",
                'errors': errors
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': f"{updated_count} configurations sauvegardées avec succès",
            'updated_count': updated_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Format JSON invalide'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors de la sauvegarde'
        }, status=500)

@api_login_required
def reset_configurations(request):
    """API pour restaurer les configurations par défaut"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        # Valeurs par défaut
        defaults = {
            'stock_critique_seuil': 5.0,
            'taux_conversion_objectif': 70.0,
            'delai_livraison_defaut': 3.0,
            'periode_analyse_defaut': 30.0,
            'article_populaire_seuil': 2.0,
            'client_fidele_seuil': 2.0,
            'rafraichissement_auto': 5.0,
            'afficher_tendances': 1.0,
            'activer_animations': 1.0,
        }
        
        reset_count = 0
        for nom_param, valeur_defaut in defaults.items():
            try:
                config = KPIConfiguration.objects.get(nom_parametre=nom_param)
                config.valeur = valeur_defaut
                config.modifie_par = request.user
                config.save()
                reset_count += 1
            except KPIConfiguration.DoesNotExist:
                continue
        
        return JsonResponse({
            'success': True,
            'message': f"{reset_count} configurations restaurées aux valeurs par défaut",
            'reset_count': reset_count
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors de la restauration'
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
    """API pour les données de l'onglet Performance Opérateurs"""
    try:
        # Obtenir les paramètres de la requête
        period = request.GET.get('period', 'today')
        operator_type = request.GET.get('operator_type', 'all')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        export_format = request.GET.get('export')
        
        # Calculer les dates selon la période
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
        
        # Convertir les dates pour les comparaisons avec les DateTimeFields
        # Utiliser __date pour les comparaisons de DateTimeField avec des dates
        
        # Construire la requête des opérateurs - Focus sur CONFIRMATION uniquement
        operateurs_query = Operateur.objects.filter(type_operateur='CONFIRMATION')
        
        # Récupérer tous les opérateurs avec leurs données
        operateurs_data = []
        
        # Métriques globales
        total_actions_global = 0
        total_confirmations_global = 0
        operateurs_actifs = 0
        
        for operateur in operateurs_query:
            # Calculer les métriques pour chaque opérateur
            
            # 1. Actions totales (Operations liées à l'opérateur)
            actions_count = Operation.objects.filter(
                operateur=operateur,
                date_operation__date__gte=date_debut,
                date_operation__date__lte=date_fin
            ).count()
            
            # 2. Confirmations (Operations de type confirmation)
            confirmations_count = Operation.objects.filter(
                operateur=operateur,
                date_operation__date__gte=date_debut,
                date_operation__date__lte=date_fin,
                type_operation__icontains='confirmation'
            ).count()
            
            # 3. Commandes affectées à l'opérateur dans la période
            commandes_affectees = Commande.objects.filter(
                etats__operateur=operateur,
                etats__date_debut__date__gte=date_debut,
                etats__date_debut__date__lte=date_fin
            ).count()
            
            # 4. Commandes confirmées par l'opérateur
            commandes_confirmees = Commande.objects.filter(
                etats__operateur=operateur,
                etats__enum_etat__libelle__icontains='Confirmée',
                etats__date_debut__date__gte=date_debut,
                etats__date_debut__date__lte=date_fin
            ).count()
            
            # 5. Commandes en cours pour cet opérateur
            commandes_en_cours = Commande.objects.filter(
                etats__operateur=operateur,
                etats__date_fin__isnull=True,  # États non terminés
                etats__date_debut__date__gte=date_debut,
                etats__date_debut__date__lte=date_fin
            ).exclude(
                etats__enum_etat__libelle__in=['Livrée', 'Annulée', 'Retournée']
            ).count()
            
            # 6. Calcul du taux de confirmation pour opérateurs CONFIRMATION
            # Ratio : Cmds Confirmées / Cmds Affectées
            if commandes_affectees > 0:
                taux_confirmation = (commandes_confirmees / commandes_affectees) * 100
            else:
                taux_confirmation = 0
            taux_confirmation_label = "Taux Confirmation"
            
            # 7. Calcul du panier moyen (commandes confirmées par l'opérateur)
            panier_moyen = Commande.objects.filter(
                etats__operateur=operateur,
                etats__enum_etat__libelle__icontains='Confirmée',
                etats__date_debut__date__gte=date_debut,
                etats__date_debut__date__lte=date_fin
            ).aggregate(
                moyenne=Avg('total_cmd')
            )['moyenne'] or 0
            
            # 8. Calcul de l'upsell (différence avec panier initial estimé)
            # Pour simplifier, on prend 10% du CA comme estimation d'upsell
            ca_operateur = Commande.objects.filter(
                etats__operateur=operateur,
                etats__enum_etat__libelle__icontains='Confirmée',
                etats__date_debut__date__gte=date_debut,
                etats__date_debut__date__lte=date_fin
            ).aggregate(
                total=Sum('total_cmd')
            )['total'] or 0
            
            upsell_estime = Decimal(str(ca_operateur)) * Decimal('0.1')  # 10% estimé comme upsell
            
            # 9. Calculs additionnels demandés
            # Commandes avec upsell (is_upsell=True)
            commandes_upsell_count = Commande.objects.filter(
                etats__operateur=operateur,
                etats__enum_etat__libelle__icontains='Confirmée',
                etats__date_debut__date__gte=date_debut,
                etats__date_debut__date__lte=date_fin,
                is_upsell=True
            ).count()
            
            # Panier min et max pour les commandes confirmées
            commandes_confirmees_query = Commande.objects.filter(
                etats__operateur=operateur,
                etats__enum_etat__libelle__icontains='Confirmée',
                etats__date_debut__date__gte=date_debut,
                etats__date_debut__date__lte=date_fin
            )
            
            panier_stats = commandes_confirmees_query.aggregate(
                panier_min=Min('total_cmd'),
                panier_max=Max('total_cmd')
            )
            panier_min = panier_stats['panier_min'] or 0
            panier_max = panier_stats['panier_max'] or 0
            
            # Moyenne du nombre d'articles par commande
            # Note: Ceci nécessite le modèle Panier (articles par commande)
            try:
                from commande.models import Panier
                avg_articles = commandes_confirmees_query.annotate(
                    nb_articles=Sum('paniers__quantite')
                ).aggregate(
                    moyenne_articles=Avg('nb_articles')
                )['moyenne_articles'] or 0
            except ImportError:
                # Si le modèle Panier n'existe pas ou n'est pas accessible
                avg_articles = 0
            
            # Marquer comme actif si l'opérateur a au moins une action
            is_active = actions_count > 0
            if is_active:
                operateurs_actifs += 1
            
            # Accumuler pour les métriques globales
            total_actions_global += actions_count
            total_confirmations_global += confirmations_count
            
            operateurs_data.append({
                'id': operateur.id,
                'nom': operateur.nom,
                'username': operateur.user.username,
                'type': operateur.type_operateur,
                'total_actions': actions_count,
                'total_confirmations': confirmations_count,
                'confirmation_rate': round(taux_confirmation, 1),
                'confirmation_rate_label': taux_confirmation_label,
                'commands_affected': commandes_affectees,
                'commands_confirmed': commandes_confirmees,
                'commands_in_progress': commandes_en_cours,
                'upsell_count': commandes_upsell_count,
                'average_basket': float(panier_moyen),
                'min_basket': float(panier_min),
                'max_basket': float(panier_max),
                'avg_articles_per_cmd': float(avg_articles),
                'upsell_amount': float(upsell_estime),
                'is_active': is_active
            })
        
        # Calculer le taux de confirmation global
        if total_actions_global > 0:
            taux_confirmation_global = (total_confirmations_global / total_actions_global) * 100
        else:
            taux_confirmation_global = 0
        
        # Métriques globales
        global_metrics = {
            'total_actions': total_actions_global,
            'total_confirmations': total_confirmations_global,
            'global_confirmation_rate': round(taux_confirmation_global, 1),
            'active_operators': operateurs_actifs
        }
        
        # Trier par nombre d'actions décroissant
        operateurs_data.sort(key=lambda x: x['total_actions'], reverse=True)
        
        # Si export Excel demandé
        if export_format == 'excel':
            return export_performance_operateurs_excel(operateurs_data, global_metrics, date_debut, date_fin)
        
        # Réponse JSON normale
        response_data = {
            'success': True,
            'operators': operateurs_data,
            'global_metrics': global_metrics,
            'period_info': {
                'start_date': date_debut.isoformat(),
                'end_date': date_fin.isoformat(),
                'period': period,
                'operator_type': operator_type
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
        content += f"Période: {date_debut.strftime('%d/%m/%Y')} - {date_fin.strftime('%d/%m/%Y')}\t\t\t\t\t\t\t\t\t\n"
        content += f"Généré le: {timezone.now().strftime('%d/%m/%Y à %H:%M')}\t\t\t\t\t\t\t\t\t\n"
        content += "\t\t\t\t\t\t\t\t\t\n"
        
        # Métriques globales
        content += "MÉTRIQUES GLOBALES\t\t\t\t\t\t\t\t\t\n"
        content += f"Total Actions\t{global_metrics['total_actions']}\t\t\t\t\t\t\t\t\n"
        content += f"Total Confirmations\t{global_metrics['total_confirmations']}\t\t\t\t\t\t\t\t\n"
        content += f"Taux Confirmation Global\t{global_metrics['global_confirmation_rate']}%\t\t\t\t\t\t\t\t\n"
        content += f"Opérateurs Actifs\t{global_metrics['active_operators']}\t\t\t\t\t\t\t\t\n"
        content += "\t\t\t\t\t\t\t\t\t\n"
        
        # En-têtes du tableau
        content += "DÉTAIL PAR OPÉRATEUR\t\t\t\t\t\t\t\t\t\t\t\n"
        content += "Opérateur\tActions\tTaux Confirm. (%)\tCmds Affectées\tCmds Confirmées\tCmds En Cours\tNb Upsell\tPanier Moyen (MAD)\tPanier Max (MAD)\tPanier Min (MAD)\tMoy. Articles\n"
        
        # Données des opérateurs
        for operateur in operateurs_data:
            content += f"{operateur['nom']}\t"
            content += f"{operateur['total_actions']}\t"
            content += f"{operateur['confirmation_rate']}\t"
            content += f"{operateur['commands_affected']}\t"
            content += f"{operateur['commands_confirmed']}\t"
            content += f"{operateur['commands_in_progress']}\t"
            content += f"{operateur['upsell_count']}\t"
            content += f"{operateur['average_basket']:.2f}\t"
            content += f"{operateur['max_basket']:.2f}\t"
            content += f"{operateur['min_basket']:.2f}\t"
            content += f"{operateur['avg_articles_per_cmd']:.1f}\n"
        
        # Configuration de la réponse HTTP
        response = HttpResponse(content, content_type='text/tab-separated-values; charset=utf-8-sig')
        
        # Nom du fichier avec date
        filename = f"performance_operateurs_{date_debut.strftime('%Y%m%d')}_{date_fin.strftime('%Y%m%d')}.txt"
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
