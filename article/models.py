from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Article(models.Model):
    """
    Modèle pour les articles
    """
    nom = models.CharField(max_length=200)
    reference = models.CharField(max_length=50, unique=True, null=True, blank=True, default=None)
    couleur = models.CharField(max_length=50)
    pointure = models.CharField(max_length=10)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    categorie = models.CharField(max_length=100)
    qte_disponible = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='articles/', blank=True, null=True)
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['nom', 'couleur', 'pointure']
        unique_together = ['nom', 'couleur', 'pointure']  # Combinaison unique
        constraints = [
            models.CheckConstraint(check=models.Q(prix_unitaire__gt=0), name='prix_unitaire_positif'),
            models.CheckConstraint(check=models.Q(qte_disponible__gte=0), name='qte_disponible_positif'),
        ]
    
    def __str__(self):
        return f"{self.nom} - {self.couleur} - {self.pointure}"
    
    @property
    def est_disponible(self):
        return self.qte_disponible > 0 and self.actif
