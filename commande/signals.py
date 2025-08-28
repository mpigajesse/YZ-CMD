from django.db.models.signals import post_save, pre_save
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Commande, EnumEtatCmd


@receiver(pre_save, sender=Commande)
def detect_compteur_change(sender, instance, **kwargs):
    """
    Détecte les changements du compteur avant la sauvegarde
    et stocke l'ancienne valeur pour comparaison
    """
    if instance.pk:
        try:
            old_instance = Commande.objects.get(pk=instance.pk)
            instance._old_compteur = old_instance.compteur
        except Commande.DoesNotExist:
            instance._old_compteur = 0
    else:
        instance._old_compteur = 0


@receiver(post_save, sender=Commande)
def auto_recalcul_totaux_upsell(sender, instance, created, **kwargs):
    """
    Recalcule automatiquement les totaux selon la nouvelle logique upsell
    quand le compteur change d'état (différent de zéro)
    """
    # Éviter la récursion infinie
    if hasattr(instance, '_recalcul_en_cours'):
        return
    
    # Vérifier si le compteur a changé
    old_compteur = getattr(instance, '_old_compteur', 0)
    nouveau_compteur = instance.compteur
    
    # Déclencher le recalcul si :
    # 1. Le compteur a changé ET
    # 2. Le nouveau compteur n'est pas zéro
    if old_compteur != nouveau_compteur and nouveau_compteur != 0:
        # Marquer pour éviter la récursion
        instance._recalcul_en_cours = True
        
        try:
            # Déclencher le recalcul automatique
            instance.recalculer_totaux_upsell()
            
            # Log pour le debugging (optionnel)
            print(f"🔄 Recalcul automatique déclenché pour commande {instance.id_yz}")
            print(f"   Compteur: {old_compteur} → {nouveau_compteur}")
            print(f"   Nouveau total: {instance.total_cmd:.2f} DH")
            
        finally:
            # Nettoyer le flag
            delattr(instance, '_recalcul_en_cours') 


@receiver(post_migrate)
def ensure_default_enum_etats(sender, app_config, **kwargs):
    """
    Garantit la présence des états par défaut après les migrations.
    Intègre tous les états nécessaires directement dans le projet.
    """
    if app_config.name != 'commande':
        return

    default_states = [
        {'libelle': 'Non affectée', 'ordre': 1, 'couleur': '#6B7280'},
        {'libelle': 'Affectée', 'ordre': 2, 'couleur': '#3B82F6'},
        {'libelle': 'En cours de confirmation', 'ordre': 3, 'couleur': '#F59E0B'},
        {'libelle': 'Confirmée', 'ordre': 4, 'couleur': '#10B981'},
        {'libelle': 'Annulée', 'ordre': 5, 'couleur': '#EF4444'},
        {'libelle': 'Doublon', 'ordre': 6, 'couleur': '#EF4444'},
        {'libelle': 'Erronée', 'ordre': 7, 'couleur': '#F97316'},
        {'libelle': 'Retour Confirmation', 'ordre': 8, 'couleur': '#8B5CF6'},
        {'libelle': 'Livrée', 'ordre': 9, 'couleur': '#22C55E'},
        {'libelle': 'En préparation', 'ordre': 10, 'couleur': '#06B6D4'},
        {'libelle': 'Préparée', 'ordre': 11, 'couleur': '#14B8A6'},
        {'libelle': 'Collectée', 'ordre': 12, 'couleur': '#6366F1'},
        {'libelle': 'Emballée', 'ordre': 13, 'couleur': '#8B5CF6'},
        {'libelle': 'Validée', 'ordre': 14, 'couleur': '#22C55E'},
    ]

    for state in default_states:
        EnumEtatCmd.objects.get_or_create(
            libelle=state['libelle'],
            defaults={'ordre': state['ordre'], 'couleur': state['couleur']}
        )