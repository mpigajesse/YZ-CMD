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