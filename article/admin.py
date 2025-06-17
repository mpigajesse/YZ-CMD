from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'couleur', 'pointure', 'prix_unitaire', 'categorie', 'qte_disponible', 'actif', 'est_disponible')
    list_filter = ('categorie', 'couleur', 'actif', 'date_creation')
    search_fields = ('nom', 'couleur', 'pointure', 'categorie')
    ordering = ('nom', 'couleur', 'pointure')
    list_editable = ('prix_unitaire', 'qte_disponible', 'actif')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations produit', {
            'fields': ('nom', 'couleur', 'pointure', 'categorie', 'description')
        }),
        ('Prix et stock', {
            'fields': ('prix_unitaire', 'qte_disponible', 'actif')
        }),
        ('Média', {
            'fields': ('image',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def est_disponible(self, obj):
        return obj.est_disponible
    est_disponible.boolean = True
    est_disponible.short_description = 'Disponible'
