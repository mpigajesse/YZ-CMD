from django.contrib import admin
from .models import Article, Promotion

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'reference', 'couleur', 'pointure', 'prix_unitaire', 'prix_upsell_1', 'prix_upsell_2', 'prix_upsell_3', 'prix_actuel', 'categorie', 'qte_disponible', 'actif', 'est_disponible')
    list_filter = ('categorie', 'couleur', 'actif', 'date_creation')
    search_fields = ('nom', 'reference', 'couleur', 'pointure', 'categorie')
    ordering = ('nom', 'couleur', 'pointure')
    list_editable = ('prix_unitaire', 'prix_upsell_1', 'prix_upsell_2', 'prix_upsell_3', 'qte_disponible', 'actif')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations produit', {
            'fields': ('nom', 'couleur', 'pointure', 'categorie', 'description')
        }),
        ('Prix', {
            'fields': ('prix_unitaire', 'prix_upsell_1', 'prix_upsell_2', 'prix_upsell_3'),
            'description': 'Prix unitaire standard et prix de substitution (upsell)'
        }),
        ('Stock', {
            'fields': ('qte_disponible', 'actif')
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
    
    def prix_actuel(self, obj):
        prix = obj.prix_actuel
        if prix != obj.prix_unitaire:
            return f"{prix} €  (promo)"
        return f"{prix} €"
    prix_actuel.short_description = 'Prix actuel'

class ArticleInline(admin.TabularInline):
    model = Promotion.articles.through
    extra = 1
    verbose_name = "Article en promotion"
    verbose_name_plural = "Articles en promotion"

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pourcentage_reduction', 'date_debut', 'date_fin', 'active', 'est_active', 'code_promo', 'nombre_articles')
    list_filter = ('active', 'date_debut', 'date_fin')
    search_fields = ('nom', 'description', 'code_promo')
    ordering = ('-date_debut', 'nom')
    list_editable = ('active',)
    readonly_fields = ('date_creation', 'date_modification')
    filter_horizontal = ('articles',)
    inlines = [ArticleInline]
    exclude = ('articles',)
    
    fieldsets = (
        ('Informations promotion', {
            'fields': ('nom', 'description', 'pourcentage_reduction', 'code_promo')
        }),
        ('Période de validité', {
            'fields': ('date_debut', 'date_fin', 'active')
        }),
        ('Métadonnées', {
            'fields': ('cree_par', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def est_active(self, obj):
        return obj.est_active
    est_active.boolean = True
    est_active.short_description = 'Active maintenant'
    
    def nombre_articles(self, obj):
        return obj.articles.count()
    nombre_articles.short_description = 'Nb articles'
    
    def save_model(self, request, obj, form, change):
        if not obj.cree_par:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)
