from django.contrib import admin
from .models import Article, Promotion

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'reference','nom', 'couleur', 'pointure', 'prix_unitaire','prix_actuel','phase', 'qte_disponible', 'actif', 'est_disponible')
    list_filter = ('categorie', 'couleur', 'phase', 'actif', 'date_creation')
    search_fields = ('nom', 'couleur', 'pointure', 'categorie')
    ordering = ('nom', 'couleur', 'pointure')
    list_editable = ('prix_unitaire','qte_disponible', 'actif', 'phase')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations produit', {
            'fields': ('nom', 'couleur', 'pointure', 'categorie', 'phase', 'description')
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
            return f"{prix} MAD (promo)"
        return f"{prix} MAD"
    prix_actuel.short_description = 'Prix actuel'

@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pourcentage_reduction', 'date_debut', 'date_fin', 'active', 'est_active', 'nombre_articles')
    list_filter = ('active', 'date_debut', 'date_fin')
    search_fields = ('nom', 'description')
    ordering = ('-date_debut', 'nom')
    list_editable = ('active',)
    readonly_fields = ('date_creation', 'date_modification')
    filter_horizontal = ('articles',)
    
    fieldsets = (
        ('Informations promotion', {
            'fields': ('nom', 'description', 'pourcentage_reduction')
        }),
        ('Articles en promotion', {
            'fields': ('articles',),
            'description': 'Sélectionnez les articles en phase "En Cours" à inclure dans la promotion'
        }),
        ('Période de validité', {
            'fields': ('date_debut', 'date_fin', 'active')
        }),
        ('Métadonnées', {
            'fields': ('cree_par', 'date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        from .models import Article  # Ensure Article is imported from the correct location
        if db_field.name == "articles":
            kwargs["queryset"] = Article.objects.filter(phase='EN_COURS', actif=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

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