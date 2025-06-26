from django.contrib import admin
from .models import EnumEtatCmd, Commande, Panier, EtatCommande, Operation

@admin.register(EnumEtatCmd)
class EnumEtatCmdAdmin(admin.ModelAdmin):
    list_display = ('id', 'libelle', 'ordre', 'couleur')
    search_fields = ('libelle',)
    ordering = ('ordre', 'libelle')
    list_editable = ('ordre', 'couleur')

class PanierInline(admin.TabularInline):
    model = Panier
    extra = 0
    readonly_fields = ('sous_total',)

class EtatCommandeInline(admin.TabularInline):
    model = EtatCommande
    extra = 0
    readonly_fields = ('date_debut',)

class OperationInline(admin.TabularInline):
    model = Operation
    extra = 0
    readonly_fields = ('date_operation',)

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('num_cmd', 'id_yz', 'date_cmd', 'total_cmd', 'etat_actuel_display', 'client', 'produit_init', 'ville', 'ville_init', 'is_upsell')
    list_filter = ('is_upsell', 'date_cmd', 'ville')
    search_fields = ('num_cmd', 'id_yz', 'client__numero_tel', 'client__nom', 'client__prenom', 'produit_init', 'ville_init')
    ordering = ('-date_cmd', '-date_creation')
    inlines = [PanierInline, EtatCommandeInline, OperationInline]
    readonly_fields = ('date_creation', 'date_modification', 'etat_actuel_display')
    
    def etat_actuel_display(self, obj):
        """Affiche l'état actuel de la commande"""
        etat = obj.etat_actuel
        if etat:
            return etat.enum_etat.libelle
        return "Aucun état"
    etat_actuel_display.short_description = "État actuel"
    
    fieldsets = (
        ('Informations commande', {
            'fields': ('num_cmd', 'id_yz', 'date_cmd', 'total_cmd', 'is_upsell', 'produit_init')
        }),
        ('Client et livraison', {
            'fields': ('client', 'ville', 'ville_init', 'adresse')
        }),
        ('État actuel', {
            'fields': ('etat_actuel_display',)
        }),
        ('Annulation', {
            'fields': ('motif_annulation',),
            'classes': ('collapse',)
        }),
        ('Dates système', {
            'fields': ('date_creation', 'date_modification'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Panier)
class PanierAdmin(admin.ModelAdmin):
    list_display = ('commande', 'article', 'quantite', 'sous_total')
    list_filter = ('commande__date_cmd',)
    search_fields = ('commande__num_cmd', 'article__nom')
    ordering = ('-commande__date_cmd',)

@admin.register(EtatCommande)
class EtatCommandeAdmin(admin.ModelAdmin):
    list_display = ('id', 'commande', 'enum_etat', 'date_debut', 'date_fin')
    list_filter = ('enum_etat', 'date_debut')
    search_fields = ('commande__num_cmd', 'enum_etat__libelle')
    ordering = ('-date_debut',)
    readonly_fields = ('date_debut',)

@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('id', 'type_operation', 'date_operation', 'commande', 'operateur')
    list_filter = ('type_operation', 'date_operation')
    search_fields = ('commande__num_cmd', 'operateur__nom', 'operateur__prenom', 'type_operation')
    ordering = ('-date_operation',)
    readonly_fields = ('date_operation',)
