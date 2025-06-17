from django import template
from datetime import timedelta

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