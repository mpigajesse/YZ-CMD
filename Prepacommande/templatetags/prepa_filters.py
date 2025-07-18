from django import template
from django.utils.safestring import mark_safe
import locale

register = template.Library()

@register.filter
def mul(value, multiplier):
    """
    Multiplie une valeur par un multiplicateur.
    Usage: {{ value|mul:multiplier }}
    """
    try:
        return float(value) * float(multiplier)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, divisor):
    """
    Divise une valeur par un diviseur.
    Usage: {{ value|div:divisor }}
    """
    try:
        divisor = float(divisor)
        if divisor == 0:
            return 0
        return float(value) / divisor
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """
    Calcule le pourcentage d'une valeur par rapport au total.
    Usage: {{ value|percentage:total }}
    """
    try:
        total = float(total)
        if total == 0:
            return 0
        return (float(value) / total) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def format_currency(value):
    """
    Formate une valeur en devise (DH).
    Usage: {{ value|format_currency }}
    """
    try:
        value = float(value)
        return f"{value:,.2f} DH"
    except (ValueError, TypeError):
        return "0,00 DH"

@register.filter
def progress_width(value, total):
    """
    Calcule la largeur d'une barre de progression en pourcentage.
    Usage: {{ value|progress_width:total }}
    """
    try:
        total = float(total)
        if total == 0:
            return 0
        percentage = (float(value) / total) * 100
        return min(percentage, 100)  # Ne pas dépasser 100%
    except (ValueError, TypeError):
        return 0

@register.filter
def status_badge_class(status):
    """
    Retourne la classe CSS appropriée pour un badge de statut.
    Usage: {{ status|status_badge_class }}
    """
    status_classes = {
        'En préparation': 'bg-blue-100 text-blue-800',
        'Préparée': 'bg-green-100 text-green-800',
        'En cours de livraison': 'bg-orange-100 text-orange-800',
        'Livrée': 'bg-purple-100 text-purple-800',
        'Annulée': 'bg-red-100 text-red-800',
        'À imprimer': 'bg-yellow-100 text-yellow-800',
    }
    return status_classes.get(status, 'bg-gray-100 text-gray-800')

@register.filter
def status_icon(status):
    """
    Retourne l'icône FontAwesome appropriée pour un statut.
    Usage: {{ status|status_icon }}
    """
    status_icons = {
        'En préparation': 'fas fa-cog fa-spin',
        'Préparée': 'fas fa-check',
        'En cours de livraison': 'fas fa-truck',
        'Livrée': 'fas fa-check-circle',
        'Annulée': 'fas fa-times-circle',
        'À imprimer': 'fas fa-print',
    }
    return status_icons.get(status, 'fas fa-circle')

@register.filter
def subtract(value, amount):
    """
    Soustrait un montant d'une valeur.
    Usage: {{ value|subtract:amount }}
    """
    try:
        return float(value) - float(amount)
    except (ValueError, TypeError):
        return 0

@register.filter
def add_percent(value, percent):
    """
    Ajoute un pourcentage à une valeur.
    Usage: {{ value|add_percent:10 }} pour ajouter 10%
    """
    try:
        value = float(value)
        percent = float(percent)
        return value + (value * percent / 100)
    except (ValueError, TypeError):
        return 0

@register.filter
def days_since(date):
    """
    Calcule le nombre de jours depuis une date.
    Usage: {{ date|days_since }}
    """
    try:
        from django.utils import timezone
        if not date:
            return 0
        now = timezone.now()
        if hasattr(date, 'date'):
            date = date.date()
        if hasattr(now, 'date'):
            now = now.date()
        delta = now - date
        return delta.days
    except (ValueError, TypeError, AttributeError):
        return 0

@register.simple_tag
def progress_bar(value, total, css_class=""):
    """
    Génère une barre de progression HTML.
    Usage: {% progress_bar current_value total_value "custom-class" %}
    """
    try:
        percentage = progress_width(value, total)
        return mark_safe(f'''
            <div class="w-full bg-gray-200 rounded-full h-2 {css_class}">
                <div class="h-2 rounded-full bg-purple-600 transition-all duration-500" style="width: {percentage}%"></div>
            </div>
        ''')
    except:
        return mark_safe('<div class="w-full bg-gray-200 rounded-full h-2"><div class="h-2 rounded-full bg-gray-400" style="width: 0%"></div></div>')

@register.simple_tag
def metric_card(title, value, icon, color_class="purple"):
    """
    Génère une carte de métrique HTML.
    Usage: {% metric_card "Total" 150 "fas fa-chart-bar" "blue" %}
    """
    return mark_safe(f'''
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    <div class="flex items-center justify-center w-12 h-12 rounded-lg bg-{color_class}-100">
                        <i class="{icon} text-xl text-{color_class}-600"></i>
                    </div>
                </div>
                <div class="ml-4">
                    <h3 class="text-sm font-medium text-gray-500 uppercase tracking-wide">{title}</h3>
                    <p class="text-2xl font-bold text-gray-900">{value}</p>
                </div>
            </div>
        </div>
    ''') 