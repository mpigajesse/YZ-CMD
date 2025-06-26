from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg, Q, F, Min
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps

from commande.models import Commande, Panier, EtatCommande, Operation
from article.models import Article
from client.models import Client
from parametre.models import Operateur
from .models import KPIConfiguration  # Assurez-vous d'importer votre modèle de configuration

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
def dashboard_home(request):
    """Page principale du dashboard KPIs"""
    return render(request, 'kpis/dashboard.html')

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
          # Taux de Livraison (commandes livrées / commandes confirmées)
        commandes_confirmees_30j_total = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            etats__enum_etat__libelle__iexact='Confirmée'
        ).distinct().count()
        
        commandes_livrees_30j = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            etats__enum_etat__libelle__iexact='Livrée'
        ).distinct().count()
        
        if commandes_confirmees_30j_total > 0:
            taux_livraison = (commandes_livrees_30j / commandes_confirmees_30j_total) * 100
        else:
            taux_livraison = 0
        
        # Taux de livraison période précédente
        commandes_confirmees_precedent_total = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j,
            etats__enum_etat__libelle__iexact='Confirmée'
        ).distinct().count()
        
        commandes_livrees_precedent = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j,
            etats__enum_etat__libelle__iexact='Livrée'
        ).distinct().count()
        
        if commandes_confirmees_precedent_total > 0:
            taux_livraison_precedent = (commandes_livrees_precedent / commandes_confirmees_precedent_total) * 100
            tendance_taux_livraison = taux_livraison - taux_livraison_precedent
        else:
            tendance_taux_livraison = taux_livraison if taux_livraison > 0 else 0          # Stock Total
        stock_total = Article.objects.filter(actif=True).aggregate(
            total=Sum('qte_disponible')
        )['total'] or 0
        
        # Calculer la tendance du stock total basée sur les ventes récentes
        # Logique simple : comparer les quantités vendues récemment vs période précédente
        try:
            # Quantités vendues des 30 derniers jours
            qty_vendue_30j = Panier.objects.filter(
                commande__date_cmd__gte=debut_30j,
                commande__date_cmd__lte=aujourd_hui
            ).exclude(
                commande__etats__enum_etat__libelle__iexact='Annulée'
            ).aggregate(total=Sum('quantite'))['total'] or 0
            
            # Quantités vendues période précédente
            qty_vendue_precedente = Panier.objects.filter(
                commande__date_cmd__gte=debut_periode_precedente,
                commande__date_cmd__lt=debut_30j
            ).exclude(
                commande__etats__enum_etat__libelle__iexact='Annulée'
            ).aggregate(total=Sum('quantite'))['total'] or 0
            
            # Plus de ventes récentes = stock diminue plus vite (tendance négative)
            # Moins de ventes récentes = stock se maintient mieux (tendance positive)
            if qty_vendue_precedente > 0:
                ratio_ventes = qty_vendue_30j / qty_vendue_precedente
                # Si ratio > 1 : plus de ventes = tendance négative (stock baisse)
                # Si ratio < 1 : moins de ventes = tendance positive (stock se maintient)
                tendance_stock_total = (1 - ratio_ventes) * 10  # Facteur modéré
            else:
                # Pas de ventes précédentes : si ventes actuelles, tendance négative
                tendance_stock_total = -5 if qty_vendue_30j > 0 else 0
        except:
            tendance_stock_total = 0
        
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
                },'satisfaction': {
                    'valeur': round(satisfaction, 1),
                    'valeur_formatee': f"{satisfaction:.1f}",
                    'tendance': round(tendance_satisfaction, 2),
                    'taux_retour': round(taux_retour, 1),
                    'commandes_livrees': commandes_livrees,
                    'commandes_retournees': commandes_retournees,
                    'unite': '/5',
                    'label': 'Satisfaction',
                    'status': 'excellent' if satisfaction >= 4.5 else 'good' if satisfaction >= 4.0 else 'warning' if satisfaction >= 3.0 else 'critical',
                    'sub_value': f"{taux_retour:.1f}% de retours ({commandes_retournees}/{commandes_livrees})"
                },                'support_24_7': {
                    'valeur': round(taux_livraison, 1),
                    'valeur_formatee': f"{taux_livraison:.1f}",
                    'tendance': round(tendance_taux_livraison, 1),
                    'unite': '%',
                    'label': 'Taux Livraison',
                    'sub_value': f'{commandes_livrees_30j}/{commandes_confirmees_30j_total} livrées'
                },'stock_total': {
                    'valeur': stock_total,
                    'valeur_formatee': f"{stock_total:,}",
                    'tendance': round(tendance_stock_total, 1),
                    'unite': 'articles',
                    'label': 'Stock Total',
                    'sub_value': 'disponibles'
                }
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
        # === KPI 1: CA par Période ===
        # CA des 30 derniers jours
        ca_30j = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            date_cmd__lte=aujourd_hui
        ).exclude(
            etats__enum_etat__libelle__iexact='Annulée',
            etats__date_fin__isnull=True
        ).aggregate(total=Sum('total_cmd'))['total'] or 0
        
        # CA période précédente pour comparaison
        debut_periode_precedente = debut_30j - timedelta(days=30)
        ca_precedent = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j
        ).exclude(
            etats__enum_etat__libelle__iexact='Annulée',
            etats__date_fin__isnull=True
        ).aggregate(total=Sum('total_cmd'))['total'] or 0
        
        # Tendance CA
        if ca_precedent > 0:
            tendance_ca = ((ca_30j - ca_precedent) / ca_precedent) * 100
        else:
            tendance_ca = 100 if ca_30j > 0 else 0
        
        # === KPI 2: Panier Moyen ===
        panier_moyen_30j = Commande.objects.filter(
            date_cmd__gte=debut_30j
        ).exclude(
            etats__enum_etat__libelle__iexact='Annulée',
            etats__date_fin__isnull=True
        ).aggregate(moyenne=Avg('total_cmd'))['moyenne'] or 0
        
        # Panier moyen période précédente
        panier_moyen_precedent = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j
        ).exclude(
            etats__enum_etat__libelle__iexact='Annulée',
            etats__date_fin__isnull=True
        ).aggregate(moyenne=Avg('total_cmd'))['moyenne'] or 0
        
        # Tendance panier moyen
        if panier_moyen_precedent > 0:
            tendance_panier = ((panier_moyen_30j - panier_moyen_precedent) / panier_moyen_precedent) * 100
        else:
            tendance_panier = 100 if panier_moyen_30j > 0 else 0
          # === KPI 3: Taux de Confirmation ===
        commandes_total_30j = Commande.objects.filter(date_cmd__gte=debut_30j).count()
        commandes_confirmees_30j = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            etats__enum_etat__libelle__iexact='Confirmée'
        ).distinct().count()
        
        if commandes_total_30j > 0:
            taux_confirmation = (commandes_confirmees_30j / commandes_total_30j) * 100
        else:
            taux_confirmation = 0
        
        # Taux de confirmation période précédente
        commandes_total_precedent = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j
        ).count()
        commandes_confirmees_precedent = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j,
            etats__enum_etat__libelle__iexact='Confirmée'
        ).distinct().count()
        
        if commandes_total_precedent > 0:
            taux_confirmation_precedent = (commandes_confirmees_precedent / commandes_total_precedent) * 100
            tendance_taux_confirmation = taux_confirmation - taux_confirmation_precedent
        else:
            tendance_taux_confirmation = taux_confirmation if taux_confirmation > 0 else 0
        
        # === KPI 4: Nombre de Commandes ===
        nb_commandes_30j = Commande.objects.filter(
            date_cmd__gte=debut_30j
        ).exclude(
            etats__enum_etat__libelle__iexact='Annulée',
            etats__date_fin__isnull=True
        ).count()
        
        nb_commandes_precedent = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j
        ).exclude(
            etats__enum_etat__libelle__iexact='Annulée',
            etats__date_fin__isnull=True
        ).count()
        
        difference_commandes = nb_commandes_30j - nb_commandes_precedent
        
        # === KPIs Secondaires ===
        
        # Top 5 Modèles par CA
        top_modeles = (Article.objects
            .filter(paniers__commande__date_cmd__gte=debut_30j)
            .exclude(paniers__commande__etats__enum_etat__libelle__iexact='Annulée')
            .annotate(
                ca_total=Sum('paniers__sous_total'),
                quantite_vendue=Sum('paniers__quantite')
            )
            .order_by('-ca_total')[:5]
        )
        
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
            .exclude(etats__enum_etat__iexact='Annulée')
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
                    'valeur': float(ca_30j),
                    'valeur_formatee': f"{ca_30j:,.0f}",
                    'tendance': round(tendance_ca, 1),
                    'unite': 'DH',
                    'label': 'CA 30 jours',
                    'sub_value': f"vs période précédente"
                },
                'panier_moyen': {
                    'valeur': float(panier_moyen_30j) if panier_moyen_30j else 0,
                    'valeur_formatee': f"{panier_moyen_30j:.0f}" if panier_moyen_30j else "0",
                    'tendance': round(tendance_panier, 1),
                    'unite': 'DH',
                    'label': 'Panier Moyen',
                    'sub_value': f"Commandes validées"
                },                'taux_confirmation': {
                    'valeur': round(taux_confirmation, 1),
                    'valeur_formatee': f"{taux_confirmation:.1f}",
                    'tendance': round(tendance_taux_confirmation, 1),
                    'unite': '%',
                    'label': 'Taux Confirmation',
                    'sub_value': f"{commandes_confirmees_30j}/{commandes_total_30j} confirmées"
                },
                'nb_commandes': {
                    'valeur': nb_commandes_30j,
                    'valeur_formatee': str(nb_commandes_30j),
                    'tendance': difference_commandes,
                    'unite': 'commandes',
                    'label': 'Commandes Validées',
                    'sub_value': f"30 derniers jours"
                }
            },
            'kpis_secondaires': {
                'top_modeles': [
                    {
                        'nom': article.nom,
                        'ca': float(article.ca_total) if article.ca_total else 0,
                        'quantite': article.quantite_vendue or 0,
                        'couleur': article.couleur
                    } for article in top_modeles
                ],
                'ventes_categorie': [
                    {
                        'categorie': cat['categorie'],
                        'ca': float(cat['ca_total']) if cat['ca_total'] else 0,
                        'quantite': cat['quantite'] or 0
                    } for cat in ventes_par_categorie
                ],
                'ventes_geographique': [
                    {
                        'ville': ville['ville__nom'] or 'Inconnue',
                        'region': ville['ville__region__nom_region'] or 'Inconnue',
                        'ca': float(ville['ca_total']) if ville['ca_total'] else 0,
                        'commandes': ville['nb_commandes'] or 0
                    } for ville in ventes_par_ville
                ],
                'performance_operateurs': performance_operateurs
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
        
        # Calcul des données réelles si disponibles
        commandes_par_jour = Commande.objects.filter(
            date_cmd__gte=debut_date,
            date_cmd__lte=fin_date
        ).exclude(
            etats__enum_etat__libelle__iexact='Annulée',
            etats__date_fin__isnull=True
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
        
        # Calcul des ventes par article/modèle
        top_modeles = Article.objects.annotate(
            ca_total=Sum(
                'paniers__sous_total',
                filter=Q(
                    paniers__commande__date_cmd__gte=debut_date,
                    paniers__commande__date_cmd__lte=fin_date
                ) & ~Q(
                    paniers__commande__etats__enum_etat__libelle__iexact='Annulée',
                    paniers__commande__etats__date_fin__isnull=True
                )
            ),
            nb_ventes=Count(
                'paniers',
                filter=Q(
                    paniers__commande__date_cmd__gte=debut_date,
                    paniers__commande__date_cmd__lte=fin_date
                ) & ~Q(
                    paniers__commande__etats__enum_etat__libelle__iexact='Annulée',
                    paniers__commande__etats__date_fin__isnull=True
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
        }
        
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
        
        # Moyenne journalière
        jours_ecoules = (aujourd_hui - debut_mois).days + 1
        moyenne_jour = nouveaux_clients_mois / jours_ecoules if jours_ecoules > 0 else 0
        
        # === KPI 2: Clients Actifs (30 derniers jours) ===
        # Clients qui ont passé au moins une commande
        clients_actifs_ids = Commande.objects.filter(
            date_cmd__gte=debut_30j
        ).values_list('client_id', flat=True).distinct()
        
        clients_actifs_30j = len(set(clients_actifs_ids))
        
        # Clients actifs période précédente
        debut_periode_precedente = debut_30j - timedelta(days=30)
        clients_actifs_precedent_ids = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j
        ).values_list('client_id', flat=True).distinct()
        
        clients_actifs_precedent = len(set(clients_actifs_precedent_ids))
        difference_actifs = clients_actifs_30j - clients_actifs_precedent
        
        # Pourcentage du total
        total_clients = Client.objects.count()
        pourcentage_actifs = (clients_actifs_30j / total_clients * 100) if total_clients > 0 else 0
        
        # === KPI 3: Taux de Retour ===
        # Simplifié - basé sur les commandes des 30 derniers jours
        commandes_30j = Commande.objects.filter(date_cmd__gte=debut_30j).count()
        
        # Estimation basée sur les motifs d'annulation (retours)
        commandes_retournees = Commande.objects.filter(
            date_cmd__gte=debut_30j,
            motif_annulation__isnull=False
        ).count()
        
        taux_retour = (commandes_retournees / commandes_30j * 100) if commandes_30j > 0 else 0
        
        # Taux retour période précédente
        commandes_precedent = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j
        ).count()
        
        retours_precedent = Commande.objects.filter(
            date_cmd__gte=debut_periode_precedente,
            date_cmd__lt=debut_30j,
            motif_annulation__isnull=False
        ).count()
        
        taux_retour_precedent = (retours_precedent / commandes_precedent * 100) if commandes_precedent > 0 else 0
        tendance_retour = taux_retour - taux_retour_precedent
        
        # === KPI 4: Satisfaction Client ===
        # Calculé basé sur le taux de retour inversé et les commandes répétées
        commandes_clients_multiples = 0
        for client_id in clients_actifs_ids:
            nb_commandes = Commande.objects.filter(
                client_id=client_id,
                date_cmd__gte=debut_30j
            ).count()
            if nb_commandes > 1:
                commandes_clients_multiples += 1
        
        # Score satisfaction basé sur fidélisation et retours
        taux_fidelisation = (commandes_clients_multiples / clients_actifs_30j * 100) if clients_actifs_30j > 0 else 0
        score_satisfaction = min(5.0, max(1.0, 5.0 - (taux_retour / 20) + (taux_fidelisation / 100)))
        
        pourcentage_satisfaits = max(0, 100 - taux_retour * 2)
        
        # === ANALYSES DÉTAILLÉES ===
        
        # Top Clients VIP (par CA) - simplifié
        top_clients_data = []
        commandes_avec_ca = Commande.objects.filter(
            date_cmd__gte=debut_30j
        ).values('client_id').annotate(
            ca_total=Sum('total_cmd'),
            nb_commandes=Count('id')
        ).order_by('-ca_total')[:5]
        
        for client_data in commandes_avec_ca:
            try:
                client = Client.objects.get(id=client_data['client_id'])
                top_clients_data.append({
                    'nom': f"{client.prenom} {client.nom[0]}." if client.nom else "Client anonyme",
                    'ca_total': float(client_data['ca_total']) if client_data['ca_total'] else 0,
                    'ca_total_format': f"{client_data['ca_total']:,.0f} DH" if client_data['ca_total'] else "0 DH",
                    'nb_commandes': client_data['nb_commandes']
                })
            except Client.DoesNotExist:
                continue
          # Performance mensuelle
        # Commandes du mois en cours
        commandes_mois_actuel = Commande.objects.filter(
            date_cmd__gte=debut_mois,
            date_cmd__lte=aujourd_hui
        ).count()
        
        # CA moyen par client actif
        if clients_actifs_30j > 0 and len(top_clients_data) > 0:
            ca_total_clients_actifs = sum(client['ca_total'] for client in top_clients_data)
            ca_moyen_par_client = ca_total_clients_actifs / clients_actifs_30j
        else:
            ca_moyen_par_client = 0
        
        # Segmentation comportementale simplifiée
        clients_reguliers = sum(1 for client_id in clients_actifs_ids 
                              if Commande.objects.filter(client_id=client_id, date_cmd__gte=debut_30j).count() >= 3)
        
        clients_nouveaux_testeurs = Client.objects.filter(
            date_creation__date__gte=debut_30j
        ).filter(
            id__in=clients_actifs_ids
        ).count()
        
        clients_occasionnels = sum(1 for client_id in clients_actifs_ids 
                                 if Commande.objects.filter(client_id=client_id, date_cmd__gte=debut_30j).count() == 2)
        
        clients_vip = len(top_clients_data)
        total_clients_analyse = clients_actifs_30j
        
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
                    'sub_value': f"{moyenne_jour:.1f} nouveaux/jour"
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
                    'sub_value': f"{commandes_retournees}/{commandes_30j} retournées",
                    'status': 'good' if taux_retour < 5 else 'warning' if taux_retour < 10 else 'critical'
                },                'satisfaction': {
                    'valeur': round(score_satisfaction, 1),
                    'valeur_formatee': f"{score_satisfaction:.1f}",
                    'tendance': round(-tendance_retour, 1),  # Inverse du taux retour
                    'unite': '/5',
                    'label': 'Satisfaction',
                    'sub_value': f"{pourcentage_satisfaits:.1f}% satisfaits",
                    'status': 'excellent' if score_satisfaction >= 4.5 else 'good' if score_satisfaction >= 4.0 else 'warning' if score_satisfaction >= 3.0 else 'critical'
                },
                'fidelisation': {
                    'valeur': round(taux_fidelisation, 1),
                    'valeur_formatee': f"{taux_fidelisation:.1f}",
                    'tendance': round(difference_actifs / clients_actifs_precedent * 100 if clients_actifs_precedent > 0 else 0, 1),
                    'unite': '%',
                    'label': 'Fidélisation',
                    'sub_value': f"{commandes_clients_multiples}/{clients_actifs_30j} clients fidèles"
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
                'commandes_total_30j': commandes_30j,
                'panier_moyen_clients': round((sum(client['ca_total'] for client in top_clients_data) / clients_actifs_30j), 2) if clients_actifs_30j > 0 else 0
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

@api_login_required
def get_configurations(request):
    """API pour récupérer toutes les configurations KPIs"""
    try:
        configs = KPIConfiguration.objects.all().order_by('categorie', 'nom_parametre')
        
        # Si aucune configuration en base, retourner les valeurs par défaut
        if not configs.exists():
            default_configs = get_default_configurations()
            return JsonResponse({
                'success': True,
                'configurations': default_configs,
                'integer_fields': get_integer_fields(),
                'message': 'Configurations par défaut chargées (base de données vide)',
                'is_default': True
            })
        
        # Mapping des vraies catégories vers les catégories attendues par le frontend
        category_mapping = {
            'seuil': 'seuils',
            'objectif': 'seuils',
            'formule': 'calcul',
            'periode': 'calcul',
            'calcul': 'calcul',  # Ajout de la catégorie manquante
            'affichage': 'affichage',
            'interface': 'affichage',
        }
        
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
            'integer_fields': get_integer_fields(),  # Ajouter les champs entiers
            'message': 'Configurations chargées avec succès',
            'is_default': False
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'Erreur lors du chargement des configurations'
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
        
        # Si aucune configuration en base de données, initialiser avec les valeurs par défaut
        if not KPIConfiguration.objects.exists():
            created_count = create_default_configurations_in_db(request.user)
            if created_count > 0:
                return JsonResponse({
                    'success': True,
                    'message': f"{created_count} configurations par défaut créées en base de données",
                    'created_count': created_count,
                    'initialized': True
                })
        
        if not configurations:
            return JsonResponse({
                'success': False,
                'message': 'Aucune configuration à sauvegarder'
            }, status=400)
        
        updated_count = 0
        created_count = 0
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
                    # Gérer les configurations par défaut (IDs qui commencent par "default_")
                    if str(config_id).startswith('default_'):
                        # Pour les configurations par défaut, créer une nouvelle entrée en base
                        nom_parametre = config_data.get('nom_parametre')
                        description = config_data.get('description', '')
                        unite = config_data.get('unite', '')
                        valeur_min = config_data.get('valeur_min')
                        valeur_max = config_data.get('valeur_max')
                        
                        # Déterminer la catégorie
                        if 'seuil' in nom_parametre or 'objectif' in nom_parametre or 'alerte' in nom_parametre:
                            categorie = 'seuil'
                        elif 'afficher' in nom_parametre or 'theme' in nom_parametre or 'auto' in nom_parametre:
                            categorie = 'affichage'
                        else:
                            categorie = 'calcul'
                        
                        # Validation spécifique pour les champs entiers
                        is_valid_integer, validated_value = validate_integer_value(nom_parametre, nouvelle_valeur)
                        if not is_valid_integer:
                            field_errors[str(config_id)] = validated_value
                            continue
                        nouvelle_valeur = validated_value
                        
                        # Créer la nouvelle configuration
                        KPIConfiguration.objects.create(
                            nom_parametre=nom_parametre,
                            valeur=nouvelle_valeur,
                            description=description,
                            unite=unite,
                            valeur_min=valeur_min,
                            valeur_max=valeur_max,
                            categorie=categorie,
                            cree_par=request.user,
                            modifie_par=request.user
                        )
                        created_count += 1
                        continue
                    
                    # Logique existante pour les configurations en base
                    try:
                        config = KPIConfiguration.objects.get(id=config_id)
                    except KPIConfiguration.DoesNotExist:
                        errors.append(f"Configuration {config_id} introuvable")
                        continue
                    
                    # Validation spécifique pour les champs entiers
                    is_valid_integer, validated_value = validate_integer_value(config.nom_parametre, nouvelle_valeur)
                    if not is_valid_integer:
                        field_errors[str(config_id)] = validated_value  # validated_value contient le message d'erreur
                        continue
                    
                    # Utiliser la valeur validée (peut avoir été convertie en entier)
                    nouvelle_valeur = validated_value
                    
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
                'updated_count': updated_count,
                'created_count': created_count
            }, status=400)
        
        # S'il y a des erreurs générales seulement
        if errors:
            return JsonResponse({
                'success': False,
                'message': f"{updated_count} configurations sauvegardées, {created_count} créées, {len(errors)} erreurs",
                'errors': errors,
                'updated_count': updated_count,
                'created_count': created_count
            }, status=400)
        
        total_operations = updated_count + created_count
        message_parts = []
        if created_count > 0:
            message_parts.append(f"{created_count} configurations créées")
        if updated_count > 0:
            message_parts.append(f"{updated_count} configurations mises à jour")
        
        return JsonResponse({
            'success': True,
            'message': " et ".join(message_parts) + " avec succès" if message_parts else "Aucune modification effectuée",
            'updated_count': updated_count,
            'created_count': created_count,
            'total_operations': total_operations
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

def get_default_configurations():
    """Retourne les configurations par défaut complètes pour initialiser l'interface"""
    return {
        'seuils': [
            {
                'id': 'default_1',
                'nom_parametre': 'stock_critique_seuil',
                'valeur': 5,
                'description': 'Seuil en-dessous duquel un stock est considéré comme critique',
                'unite': 'unités',
                'valeur_min': 1,
                'valeur_max': 100,
                'type': 'number'
            },
            {
                'id': 'default_2', 
                'nom_parametre': 'taux_conversion_min',
                'valeur': 60,
                'description': 'Taux de conversion minimum acceptable pour les appels',
                'unite': '%',
                'valeur_min': 0,
                'valeur_max': 100,
                'type': 'number'
            },
            {
                'id': 'default_3',
                'nom_parametre': 'delai_livraison_alerte',
                'valeur': 5,
                'description': 'Délai de livraison déclenchant une alerte',
                'unite': 'jours',
                'valeur_min': 1,
                'valeur_max': 30,
                'type': 'number'
            },
            {
                'id': 'default_4',
                'nom_parametre': 'ca_objectif_mensuel',
                'valeur': 100000,
                'description': 'Objectif de chiffre d\'affaires mensuel',
                'unite': 'DH',
                'valeur_min': 1000,
                'valeur_max': 1000000,
                'type': 'number'
            }
        ],
        'calcul': [
            {
                'id': 'default_5',
                'nom_parametre': 'periode_analyse_defaut',
                'valeur': 30,
                'description': 'Période d\'analyse par défaut pour les KPIs',
                'unite': 'jours',
                'valeur_min': 7,
                'valeur_max': 365,
                'type': 'select',
                'options': [
                    {'value': 7, 'label': '7 jours'},
                    {'value': 15, 'label': '15 jours'},
                    {'value': 30, 'label': '30 jours'},
                    {'value': 60, 'label': '60 jours'},
                    {'value': 90, 'label': '90 jours'}
                ]
            },
            {
                'id': 'default_6',
                'nom_parametre': 'fidelisation_commandes_min',
                'valeur': 2,
                'description': 'Nombre minimum de commandes pour être considéré comme client fidèle',
                'unite': 'commandes',
                'valeur_min': 1,
                'valeur_max': 10,
                'type': 'number'
            },
            {
                'id': 'default_7',
                'nom_parametre': 'fidelisation_periode_jours',
                'valeur': 30,
                'description': 'Période en jours pour calculer la fidélisation',
                'unite': 'jours',
                'valeur_min': 7,
                'valeur_max': 365,
                'type': 'number'
            },
            {
                'id': 'default_8',
                'nom_parametre': 'stock_ventes_minimum',
                'valeur': 2,
                'description': 'Nombre minimum de ventes pour qu\'un article soit considéré comme populaire',
                'unite': 'ventes',
                'valeur_min': 1,
                'valeur_max': 20,
                'type': 'number'
            }
        ],
        'affichage': [
            {
                'id': 'default_9',
                'nom_parametre': 'afficher_tendances',
                'valeur': True,
                'description': 'Afficher les flèches de tendance sur les KPIs',
                'unite': '',
                'valeur_min': None,
                'valeur_max': None,
                'type': 'checkbox'
            },
            {
                'id': 'default_10',
                'nom_parametre': 'afficher_pourcentages',
                'valeur': True,
                'description': 'Afficher les valeurs en pourcentage quand c\'est pertinent',
                'unite': '',
                'valeur_min': None,
                'valeur_max': None,
                'type': 'checkbox'
            },
            {
                'id': 'default_11',
                'nom_parametre': 'theme_couleur',
                'valeur': 'bleu',
                'description': 'Thème de couleur pour les graphiques',
                'unite': '',
                'valeur_min': None,
                'valeur_max': None,
                'type': 'select',
                'options': [
                    {'value': 'bleu', 'label': 'Bleu (par défaut)'},
                    {'value': 'vert', 'label': 'Vert'},
                    {'value': 'orange', 'label': 'Orange'},
                    {'value': 'violet', 'label': 'Violet'}
                ]
            },
            {
                'id': 'default_12',
                'nom_parametre': 'auto_refresh',
                'valeur': True,
                'description': 'Actualisation automatique des données toutes les 5 minutes',
                'unite': '',
                'valeur_min': None,
                'valeur_max': None,
                'type': 'checkbox'
            }
        ]
    }

def create_default_configurations_in_db(user):
    """Crée les configurations par défaut en base de données"""
    default_configs = get_default_configurations()
    created_count = 0
    
    # Mappage des catégories frontend vers base de données
    category_reverse_mapping = {
        'seuils': 'seuil',
        'calcul': 'calcul', 
        'affichage': 'affichage'
    }
    
    for category, configs in default_configs.items():
        db_category = category_reverse_mapping.get(category, 'calcul')
        
        for config in configs:
            # Vérifier si la configuration existe déjà
            if not KPIConfiguration.objects.filter(nom_parametre=config['nom_parametre']).exists():
                KPIConfiguration.objects.create(
                    nom_parametre=config['nom_parametre'],
                    valeur=config['valeur'],
                    description=config['description'],
                    unite=config['unite'],
                    valeur_min=config['valeur_min'],
                    valeur_max=config['valeur_max'],
                    categorie=db_category,
                    cree_par=user,
                    modifie_par=user
                )
                created_count += 1
    
    return created_count
