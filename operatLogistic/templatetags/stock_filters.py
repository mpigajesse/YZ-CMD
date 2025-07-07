from django import template

register = template.Library()

@register.filter
def filter_rupture(articles):
    """Filtre les articles en rupture de stock (qte_disponible <= 0)"""
    return [article for article in articles if article.qte_disponible <= 0]

@register.filter
def filter_stock_faible(articles):
    """Filtre les articles avec un stock faible (0 < qte_disponible <= 10)"""
    return [article for article in articles if 0 < article.qte_disponible <= 10]

@register.filter
def filter_a_commander(articles):
    """Filtre les articles à commander (10 < qte_disponible <= 20)"""
    return [article for article in articles if 10 < article.qte_disponible <= 20]

@register.filter
def calculer_valeur_stock(articles):
    """Calcule la valeur totale du stock"""
    return sum(article.qte_disponible * article.prix_unitaire for article in articles)

@register.filter
def format_prix(montant):
    """Formate un montant en DH avec séparateur de milliers"""
    return "{:,.2f} DH".format(montant) 