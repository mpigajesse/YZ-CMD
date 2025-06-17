from django.contrib import admin
from .models import Region, Ville, Operateur

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom_region')
    search_fields = ('nom_region',)
    ordering = ('nom_region',)

@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'region', 'frais_livraison', 'frequence_livraison')
    list_filter = ('region', 'frequence_livraison')
    search_fields = ('nom', 'region__nom_region')
    ordering = ('nom',)

@admin.register(Operateur)
class OperateurAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'mail', 'type_operateur', 'actif', 'date_creation')
    list_filter = ('type_operateur', 'actif', 'date_creation')
    search_fields = ('nom', 'prenom', 'mail', 'user__username')
    ordering = ('nom', 'prenom')
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('user', 'nom', 'prenom', 'mail', 'telephone')
        }),
        ('Profil opérateur', {
            'fields': ('type_operateur', 'photo', 'adresse', 'actif')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )
    
    def nom_complet(self, obj):
        return obj.nom_complet
    nom_complet.short_description = 'Nom complet'
