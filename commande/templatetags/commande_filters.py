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
    Retourne le prix upsell approprié en fonction de la quantité.
    """
    if not article.isUpsell:
        return article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire
        
    if quantite == 1:
        return article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire
    elif quantite == 2 and article.prix_upsell_1:
        return article.prix_upsell_1
    elif quantite == 3 and article.prix_upsell_2:
        return article.prix_upsell_2
    elif quantite > 3 and article.prix_upsell_3:
        return article.prix_upsell_3
    else:
        return article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire

@register.filter
def calculer_sous_total_upsell(article, quantite):
    """
    Calcule le sous-total en utilisant le prix upsell approprié.
    Pour les articles upsell, le sous-total est le prix upsell, pas le prix * quantité.
    """
    prix = get_prix_upsell(article, quantite)
    
    if article.isUpsell:
        return prix if prix is not None else 0
    else:
        return prix * quantite if prix is not None else 0