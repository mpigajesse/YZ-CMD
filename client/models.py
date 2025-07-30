from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from parametre.models import Operateur, Ville

# Create your models here.

class Client(models.Model):
    """
    Modèle pour les clients
    """
    nom = models.CharField(max_length=100, default='', verbose_name="Nom")
    prenom = models.CharField(max_length=100, default='', verbose_name="Prénom")
    numero_tel = models.CharField(max_length=30, unique=True, verbose_name="Numéro de téléphone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    note = models.TextField(blank=True, null=True, verbose_name="Note")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    
    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.numero_tel})"

    @property
    def get_full_name(self):
        return f"{self.prenom} {self.nom}".strip()

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['-date_creation']
