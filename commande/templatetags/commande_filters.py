from django import template
from datetime import timedelta
from django.db.models import Q

register = template.Library()

@register.filter
def format_timedelta(value):
    if not isinstance(value, timedelta):
        return value

@register.filter
def lookup(dictionary, key):
    """Permet d'accéder à une valeur de dictionnaire avec une clé dynamique"""
    return dictionary.get(key, {})

@register.filter
def dict_get(dictionary, key):
    """Alias de lookup - permet d'accéder à une valeur de dictionnaire avec une clé dynamique"""
    return dictionary.get(key, '')

@register.filter
def div(value, arg):
    """Division de deux nombres"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def confirmation_operation(commande):
    """Récupère la dernière opération de confirmation pour une commande"""
    operations_confirmation = commande.operations.filter(
        type_operation__in=[
            'AUCUNE_ACTION', 'APPEL_1', 'APPEL_2', 'APPEL_3', 'APPEL_4',
            'APPEL_5', 'APPEL_6', 'APPEL_7', 'APPEL_8', 'ENVOI_SMS',
            'ENVOI_MSG', 'PROPOSITION_ABONNEMENT', 'PROPOSITION_REDUCTION'
        ]
    ).order_by('-date_operation')
    
    return operations_confirmation.first() if operations_confirmation.exists() else None

@register.filter
def format_montant(value):
    """Formate un montant avec 2 décimales"""
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "0.00"

@register.filter
def get_etat(commande, libelle_etat):
    """
    Récupère un état spécifique de la commande par son libellé.
    Utilisé principalement pour trouver l'opérateur et la date d'un état précis.
    """
    try:
        # On cherche l'état actuel (sans date de fin) qui correspond au libellé
        etat = commande.etats.filter(
            enum_etat__libelle__exact=libelle_etat,
            date_fin__isnull=True
        ).first()
        
        # Si on ne trouve pas d'état actuel, on prend le plus récent (historique)
        if not etat:
            etat = commande.etats.filter(
                enum_etat__libelle__exact=libelle_etat
            ).order_by('-date_debut').first()
            
        return etat
    except Exception:
        return None

@register.filter
def get_prix_upsell(article, quantite):
    """
    Retourne le prix approprié en fonction de la quantité.
    Pour les articles upsell : le prix upsell REMPLACE le prix actuel.
    """
    if not article.isUpsell:
        return article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire
    
    # Pour les articles upsell, retourner directement le prix upsell correspondant
    if quantite == 1:
        return article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire
    elif quantite == 2 and article.prix_upsell_1:
        # Prix upsell 1 remplace le prix actuel
        return article.prix_upsell_1
    elif quantite == 3 and article.prix_upsell_2:
        # Prix upsell 2 remplace le prix actuel
        return article.prix_upsell_2
    elif quantite == 4 and article.prix_upsell_3:
        # Prix upsell 3 remplace le prix actuel
        return article.prix_upsell_3
    elif quantite > 4 and article.prix_upsell_4:
        # Prix upsell 4 remplace le prix actuel
        return article.prix_upsell_4
    else:
        # Si pas de prix upsell défini, utiliser le prix actuel
        return article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire

@register.filter
def get_prix_upsell_avec_compteur(article, compteur):
    """
    Retourne le prix approprié en fonction du compteur de la commande.
    Le compteur commence à s'incrémenter à partir de 2 unités d'articles upsell :
    - 0-1 unités upsell → compteur = 0 → prix normal
    - 2 unités upsell → compteur = 1 → prix upsell 1
    - 3 unités upsell → compteur = 2 → prix upsell 2
    - 4 unités upsell → compteur = 3 → prix upsell 3
    - 5+ unités upsell → compteur = 4+ → prix upsell 4
    
    Note: Les unités incluent les quantités (ex: 1 article qté 2 = 2 unités)
    Seuls les articles avec isUpsell=True utilisent les prix upsell.
    Les autres articles gardent leur prix normal.
    """
    # Si l'article n'est pas upsell, toujours retourner le prix normal
    if not article.isUpsell:
        return article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire
    
    # Pour les articles upsell, appliquer le prix selon le compteur
    if compteur == 0:
        # 0-1 articles upsell → prix normal
        return article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire
    elif compteur == 1 and article.prix_upsell_1:
        # 2 articles upsell → prix upsell 1
        return article.prix_upsell_1
    elif compteur == 2 and article.prix_upsell_2:
        # 3 articles upsell → prix upsell 2
        return article.prix_upsell_2
    elif compteur == 3 and article.prix_upsell_3:
        # 4 articles upsell → prix upsell 3
        return article.prix_upsell_3
    elif compteur >= 4 and article.prix_upsell_4:
        # 5+ articles upsell → prix upsell 4
        return article.prix_upsell_4
    else:
        # Si pas de prix upsell défini pour ce niveau, utiliser le prix actuel
        return article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire

@register.filter
def get_prix_upsell_supplement(article, quantite):
    """
    Retourne uniquement le supplément upsell (pas le prix total).
    """
    if not article.isUpsell or quantite <= 1:
        return 0
    
    if quantite == 2 and article.prix_upsell_1:
        return article.prix_upsell_1
    elif quantite == 3 and article.prix_upsell_2:
        return article.prix_upsell_2
    elif quantite == 4 and article.prix_upsell_3:
        return article.prix_upsell_3
    elif quantite > 4 and article.prix_upsell_4:
        return article.prix_upsell_4
    else:
        # Si pas de prix upsell défini, pas de supplément
        return 0

@register.filter
def calculer_sous_total_avec_compteur(panier, compteur):
    """
    Calcule le sous-total d'un panier en utilisant le compteur de la commande.
    Le compteur commence à s'incrémenter à partir de 2 unités d'articles upsell.
    Les unités incluent les quantités (ex: 1 article qté 2 = 2 unités).
    Seuls les articles avec isUpsell=True utilisent les prix upsell selon le niveau.
    Les autres articles gardent leur prix normal.
    """
    prix = get_prix_upsell_avec_compteur(panier.article, compteur)
    return prix * panier.quantite if prix is not None else 0

@register.filter
def calculer_sous_total_upsell(article, quantite):
    """
    Calcule le sous-total en utilisant le prix approprié.
    Pour les articles upsell, le prix upsell remplace le prix unitaire.
    """
    prix = get_prix_upsell(article, quantite)
    
    if article.isUpsell:
        # Pour les articles upsell, get_prix_upsell retourne le prix unitaire (pour qté 1) 
        # ou le prix upsell (pour qté > 1) - on multiplie par la quantité
        return prix * quantite if prix is not None else 0
    else:
        # Pour les articles normaux, multiplier par la quantité
        return prix * quantite if prix is not None else 0

@register.filter
def has_articles_upsell(commande):
    """
    Retourne True si la commande contient au moins un article avec isUpsell=True
    """
    return commande.paniers.filter(article__isUpsell=True).exists()

@register.filter
def get_prix_avec_phase_info(article, compteur=None):
    """
    Retourne un dictionnaire avec le prix et le libellé selon la phase de l'article.
    Gère les phases : EN_COURS, LIQUIDATION, EN_TEST et les promotions.
    """
    # Déterminer le prix de base
    if compteur is not None and article.isUpsell:
        prix = get_prix_upsell_avec_compteur(article, compteur)
    else:
        prix = article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire
    
    # Déterminer le libellé selon la phase et les promotions
    if article.has_promo_active:
        libelle = "Prix promotion"
        couleur_classe = "text-red-600"
    elif article.phase == 'LIQUIDATION':
        libelle = "Prix liquidation"
        couleur_classe = "text-orange-600"
    elif article.phase == 'EN_TEST':
        libelle = "Prix test"
        couleur_classe = "text-blue-600"
    elif compteur is not None and compteur > 0 and article.isUpsell:
        libelle = f"Prix upsell niveau {compteur}"
        couleur_classe = "text-green-600"
    else:
        libelle = "Prix normal"
        couleur_classe = "text-gray-600"
    
    return {
        'prix': prix,
        'libelle': libelle,
        'couleur_classe': couleur_classe
    }

@register.filter
def get_prix_avec_phase_simple(article):
    """
    Version simplifiée pour les templates sans compteur.
    Retourne un dictionnaire avec le prix et le libellé selon la phase de l'article.
    """
    return get_prix_avec_phase_info(article, compteur=None)

@register.filter
def get_phase_libelle(article):
    """
    Retourne uniquement le libellé de la phase pour l'affichage.
    """
    info = get_prix_avec_phase_info(article, compteur=None)
    return info['libelle']

@register.filter
def get_phase_couleur(article):
    """
    Retourne uniquement la classe de couleur pour l'affichage.
    """
    info = get_prix_avec_phase_info(article, compteur=None)
    return info['couleur_classe']