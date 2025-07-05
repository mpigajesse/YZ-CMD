from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Commande


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