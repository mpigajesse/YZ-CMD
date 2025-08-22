from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par sa clé"""
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None