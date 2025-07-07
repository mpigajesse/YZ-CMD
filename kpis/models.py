from django.db import models
from django.contrib.auth.models import User

class KPIConfiguration(models.Model):
    """Configuration des paramètres et seuils KPIs"""
    
    # Catégories de paramètres
    CATEGORY_CHOICES = [
        ('seuils', 'Seuils d\'alerte'),
        ('calcul', 'Paramètres de calcul'),
        ('affichage', 'Préférences d\'affichage'),
    ]
    
    nom_parametre = models.CharField(max_length=100, unique=True, help_text="Nom unique du paramètre")
    categorie = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='seuils')
    valeur = models.FloatField(help_text="Valeur numérique du paramètre")
    description = models.TextField(help_text="Description et utilité du paramètre")
    unite = models.CharField(max_length=20, blank=True, help_text="Unité de mesure (%, jours, etc.)")
    valeur_min = models.FloatField(null=True, blank=True, help_text="Valeur minimum autorisée")
    valeur_max = models.FloatField(null=True, blank=True, help_text="Valeur maximum autorisée")
    
    # Métadonnées
    modifie_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Configuration KPI"
        verbose_name_plural = "Configurations KPIs"
        ordering = ['categorie', 'nom_parametre']
    
    def __str__(self):
        return f"{self.nom_parametre} = {self.valeur} {self.unite}"
