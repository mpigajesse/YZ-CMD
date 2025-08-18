from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Operateur

@receiver(post_save, sender=User)
def create_operateur_profile(sender, instance, created, **kwargs):
    """
    Crée automatiquement un profil Operateur quand un utilisateur 
    avec un groupe d'opérateur est créé
    """
    if created:
        # Déterminer le type d'opérateur selon les groupes
        type_operateur = None
        
        if instance.groups.filter(name='operateur_confirme').exists():
            type_operateur = 'CONFIRMATION'
        elif instance.groups.filter(name='operateur_logistique').exists():
            type_operateur = 'LOGISTIQUE'
        elif instance.groups.filter(name='operateur_preparation').exists():
            type_operateur = 'PREPARATION'
        elif instance.groups.filter(name='superviseur').exists():
            type_operateur = 'SUPERVISEUR_PREPARATION'
        elif instance.is_superuser or instance.groups.filter(name='admin').exists():
            type_operateur = 'ADMIN'
        
        # Créer le profil opérateur si un type est déterminé
        if type_operateur:
            Operateur.objects.create(
                user=instance,
                nom=instance.last_name or '',
                prenom=instance.first_name or '',
                mail=instance.email,
                type_operateur=type_operateur
            )

@receiver(post_save, sender=User)
def save_operateur_profile(sender, instance, **kwargs):
    """
    Sauvegarde le profil Operateur quand l'utilisateur est modifié
    """
    if hasattr(instance, 'profil_operateur'):
        # Synchroniser les informations de base
        operateur = instance.profil_operateur
        operateur.nom = instance.last_name or operateur.nom
        operateur.prenom = instance.first_name or operateur.prenom
        operateur.mail = instance.email or operateur.mail
        operateur.save() 