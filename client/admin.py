from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('numero_tel', 'nom', 'prenom', 'email', 'date_creation', 'is_active')
    # Suppression des filtres comme demandé
    # list_filter = ('is_active', 'date_creation')
    search_fields = ('numero_tel', 'nom', 'prenom', 'email', 'adresse')
    ordering = ('-date_creation',)
    readonly_fields = ('date_creation', 'date_modification')
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'numero_tel', 'email', 'adresse')
        }),
        ('Statut', {
            'fields': ('is_active', 'date_creation')
        }),
    )
