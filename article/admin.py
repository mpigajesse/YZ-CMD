from django.contrib import admin
from .models import Article, Promotion, Categorie, Genre, Pointure, Couleur, VarianteArticle, MouvementStock

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'isUpsell', 'qte_disponible', 'actif', 'date_creation')
    list_filter = ('isUpsell', 'actif', 'date_creation')
    search_fields = ('nom', 'description')
    ordering = ('nom',)
    list_editable = ('isUpsell', 'qte_disponible', 'actif')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations catégorie', {
            'fields': ('nom', 'description')
        }),
        ('Configuration', {
            'fields': ('isUpsell', 'qte_disponible', 'actif')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('nom', 'actif', 'date_creation')
    list_filter = ('actif', 'date_creation')
    search_fields = ('nom', 'description')
    ordering = ('nom',)
    list_editable = ('actif',)
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations genre', {
            'fields': ('nom', 'description', 'actif')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Pointure)
class PointureAdmin(admin.ModelAdmin):
    list_display = ('pointure', 'ordre', 'actif', 'date_creation')
    list_filter = ('actif', 'date_creation')
    search_fields = ('pointure', 'description')
    ordering = ('ordre', 'pointure')
    list_editable = ('ordre', 'actif')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations pointure', {
            'fields': ('pointure', 'description', 'ordre', 'actif')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Couleur)
class CouleurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_hex', 'actif', 'date_creation')
    list_filter = ('actif', 'date_creation')
    search_fields = ('nom', 'description')
    ordering = ('nom',)
    list_editable = ('code_hex', 'actif')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations couleur', {
            'fields': ('nom', 'code_hex', 'description', 'actif')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VarianteArticle)
class VarianteArticleAdmin(admin.ModelAdmin):
    list_display = ('article', 'couleur', 'pointure', 'qte_disponible', 'prix_unitaire', 'prix_achat', 'prix_actuel', 'actif')
    list_filter = ('actif', 'article__categorie', 'couleur', 'pointure', 'date_creation')
    search_fields = ('article__nom', 'couleur__nom', 'pointure__pointure')
    ordering = ('article__nom', 'couleur__nom', 'pointure__pointure')
    list_editable = ('qte_disponible', 'prix_unitaire', 'prix_achat', 'actif')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Article et variante', {
            'fields': ('article', 'couleur', 'pointure')
        }),
        ('Prix', {
            'fields': ('prix_unitaire', 'prix_achat', 'prix_actuel')
        }),
        ('Stock', {
            'fields': ('qte_disponible', 'actif')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def prix_actuel(self, obj):
        prix = obj.prix_actuel
        if prix and prix != obj.prix_unitaire:
            return f"{prix} MAD (promo)"
        return f"{prix} MAD" if prix else "Non défini"
    prix_actuel.short_description = 'Prix actuel'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'reference', 'nom', 'categorie', 'prix_unitaire', 'prix_achat', 'prix_actuel', 'phase', 'qte_disponible', 'actif', 'est_disponible', 'isUpsell')
    list_filter = ('categorie', 'phase', 'actif', 'date_creation', 'isUpsell')
    search_fields = ('nom', 'reference', 'categorie')
    ordering = ('nom', 'categorie')
    list_editable = ('prix_unitaire', 'prix_achat', 'actif', 'phase', 'isUpsell')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations produit', {
            'fields': ('nom', 'reference', 'categorie', 'phase', 'description')
        }),
        ('Prix', {
            'fields': ('prix_unitaire', 'prix_achat', 'prix_upsell_1', 'prix_upsell_2', 'prix_upsell_3', 'prix_upsell_4'),
            'description': 'Prix unitaire, prix d\'achat et prix de substitution (upsell)'
        }),
        ('Configuration Upsell', {
            'fields': ('isUpsell',),
            'description': 'Configuration pour les articles upsell'
        }),
        ('Stock', {
            'fields': ('qte_disponible', 'actif'),
            'description': 'La quantité totale est calculée automatiquement à partir des variantes'
        }),
        ('Média', {
            'fields': ('image', 'image_url')
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
        if prix and prix != obj.prix_unitaire:
            return f"{prix} MAD (promo)"
        return f"{prix} MAD" if prix else "Non défini"
    prix_actuel.short_description = 'Prix actuel'


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('article', 'variante_info', 'type_mouvement', 'quantite', 'qte_apres_mouvement', 'date_mouvement', 'operateur')
    list_filter = ('type_mouvement', 'date_mouvement', 'article__categorie')
    search_fields = ('article__nom', 'variante__couleur__nom', 'variante__pointure__pointure')
    ordering = ('-date_mouvement',)
    readonly_fields = ('date_mouvement', 'qte_apres_mouvement')
    
    fieldsets = (
        ('Article et variante', {
            'fields': ('article', 'variante')
        }),
        ('Mouvement', {
            'fields': ('type_mouvement', 'quantite', 'qte_apres_mouvement')
        }),
        ('Informations', {
            'fields': ('commentaire', 'commande_associee', 'operateur', 'date_mouvement')
        }),
    )
    
    def variante_info(self, obj):
        if obj.variante:
            return f"{obj.variante.couleur.nom} - {obj.variante.pointure.pointure}"
        return "Article général"
    variante_info.short_description = 'Variante'


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