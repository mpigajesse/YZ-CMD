from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Region(models.Model):
    nom_region = models.CharField(max_length=100, unique=True)
    
    class Meta:
        verbose_name = "Région"
        verbose_name_plural = "Régions"
        ordering = ['nom_region']
    
    def __str__(self):
        return self.nom_region


class Ville(models.Model):
    nom = models.CharField(max_length=100)
    frais_livraison = models.FloatField()
    frequence_livraison = models.CharField(max_length=50)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='villes')
    
    class Meta:
        verbose_name = "Ville"
        verbose_name_plural = "Villes"
        ordering = ['nom']
        unique_together = ['nom', 'region']  # Une ville unique par région
    
    def __str__(self):
        return f"{self.nom} ({self.region.nom_region})"


class Operateur(models.Model):
    TYPE_OPERATEUR_CHOICES = [
        ('CONFIRMATION', 'Opérateur de Confirmation'),
        ('LOGISTIQUE', 'Opérateur Logistique'),
        ('PREPARATION', 'Opérateur de Préparation'),
        ('ADMIN', 'Administrateur'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_operateur')
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    mail = models.EmailField()
    type_operateur = models.CharField(max_length=20, choices=TYPE_OPERATEUR_CHOICES, default='CONFIRMATION')
    photo = models.ImageField(upload_to='photos/operateurs/', blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Opérateur"
        verbose_name_plural = "Opérateurs"
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.get_type_operateur_display()}"
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}".strip()
    
    def get_full_name(self):
        """Méthode pour compatibilité avec les templates"""
        return self.nom_complet
    
    @property
    def is_confirmation(self):
        return self.type_operateur == 'CONFIRMATION'
    
    @property
    def is_logistique(self):
        return self.type_operateur == 'LOGISTIQUE'
    
    @property
    def is_preparation(self):
        return self.type_operateur == 'PREPARATION'
    
    @property
    def is_admin(self):
        return self.type_operateur == 'ADMIN'


class HistoriqueMotDePasse(models.Model):
    """
    Modèle pour tracer l'historique des modifications de mots de passe des opérateurs
    """
    operateur = models.ForeignKey(Operateur, on_delete=models.CASCADE, related_name='historique_mots_de_passe')
    administrateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                     help_text="Administrateur qui a modifié le mot de passe")
    date_modification = models.DateTimeField(default=timezone.now)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True, help_text="Adresse IP de l'administrateur")
    commentaire = models.TextField(blank=True, null=True, help_text="Commentaire optionnel sur la modification")
    
    class Meta:
        verbose_name = "Historique Mot de Passe"
        verbose_name_plural = "Historiques Mots de Passe"
        ordering = ['-date_modification']
    
    def __str__(self):
        admin_name = self.administrateur.get_full_name() if self.administrateur else "Système"
        return f"Modification MDP de {self.operateur.nom_complet} par {admin_name} le {self.date_modification.strftime('%d/%m/%Y %H:%M')}"
