from django.contrib import admin
from .models import Article, Promotion, Categorie, Genre, Pointure, Couleur, VarianteArticle, MouvementStock
from django.db.models import Sum, Q
from django.contrib import messages
from django.http import HttpResponseRedirect

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'quantite_disponible', 'actif', 'date_creation')
    list_filter = ('actif', 'date_creation')
    search_fields = ('nom', 'description')
    ordering = ('nom',)
    list_editable = ['actif']
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations catégorie', {
            'fields': ('nom', 'description')
        }),
        ('Configuration', {
            'fields': ('actif',)
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            total_qte=Sum('articles__variantes__qte_disponible', filter=Q(articles__actif=True, articles__variantes__actif=True))
        )

    def quantite_disponible(self, obj):
        return obj.total_qte or 0
    quantite_disponible.short_description = 'Quantité disponible'
    quantite_disponible.admin_order_field = 'total_qte'


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
    list_display = ('article', 'reference_variante', 'couleur', 'pointure', 'qte_disponible', 'prix_unitaire_display', 'prix_achat_display', 'prix_actuel_display', 'actif')
    list_filter = ('actif', 'article__categorie', 'couleur', 'pointure', 'date_creation')
    search_fields = ('article__nom', 'couleur__nom', 'pointure__pointure')
    ordering = ('article__nom', 'couleur__nom', 'pointure__pointure')
    list_editable = ('qte_disponible', 'actif')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Article et variante', {
            'fields': ('article', 'couleur', 'pointure')
        }),
        ('Stock', {
            'fields': ('qte_disponible', 'actif')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def prix_unitaire_display(self, obj):
        return f"{obj.prix_unitaire} MAD" if obj.prix_unitaire else "Non défini"
    prix_unitaire_display.short_description = 'Prix unitaire'
    
    def prix_achat_display(self, obj):
        return f"{obj.prix_achat} MAD" if obj.prix_achat else "Non défini"
    prix_achat_display.short_description = 'Prix d\'achat'
    
    def prix_actuel_display(self, obj):
        prix = obj.prix_actuel
        if prix and prix != obj.prix_unitaire:
            return f"{prix} MAD (promo)"
        return f"{prix} MAD" if prix else "Non défini"
    prix_actuel_display.short_description = 'Prix actuel'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'reference', 'nom', 'genre', 'categorie', 'prix_unitaire', 'prix_achat', 'prix_actuel', 'phase', 'actif', 'est_disponible', 'isUpsell')
    list_filter = ('categorie', 'phase', 'actif', 'date_creation', 'isUpsell','genre')
    search_fields = ('nom', 'reference', 'categorie__nom')
    ordering = ('nom', 'categorie__nom')
    list_editable = ('prix_unitaire', 'prix_achat', 'actif', 'phase', 'isUpsell')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations produit', {
            'fields': ('nom', 'reference', 'categorie', 'genre', 'phase', 'description')
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
            'fields': ('actif',),
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
    
    def changelist_view(self, request, extra_context=None):
        """Rend la vue de liste plus robuste après des purges de données.
        Si un POST tente de modifier des lignes qui n'existent plus, on rafraîchit.
        """
        try:
            return super().changelist_view(request, extra_context)
        except Article.DoesNotExist:
            messages.warning(request, "La liste était obsolète après une suppression. Rafraîchie.")
            return HttpResponseRedirect(request.path)
    
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