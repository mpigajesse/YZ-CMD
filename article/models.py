from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

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
    
    # Prix de substitution (upsell)
    prix_upsell_1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix upsell 1")
    prix_upsell_2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix upsell 2")
    prix_upsell_3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix upsell 3")
    
    class Meta:
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        ordering = ['nom', 'couleur', 'pointure']
        unique_together = ['nom', 'couleur', 'pointure']  # Combinaison unique
        constraints = [
            models.CheckConstraint(check=models.Q(prix_unitaire__gt=0), name='prix_unitaire_positif'),
            models.CheckConstraint(check=models.Q(qte_disponible__gte=0), name='qte_disponible_positif'),
            # La contrainte sur la pointure a été supprimée car elle pose problème avec SQLite
            # models.CheckConstraint(
            #     check=models.Q(pointure__regex=r'^(3[0-9]|4[0-9]|50)$'), 
            #     name='pointure_valide'
            # ),
        ]
    
    def __str__(self):
        return f"{self.nom} - {self.couleur} - {self.pointure}"
    
    @property
    def est_disponible(self):
        return self.qte_disponible > 0 and self.actif
    
    @property
    def prix_actuel(self):
        """Retourne le prix actuel en tenant compte des promotions actives"""
        promotion_active = self.promotions.filter(
            date_debut__lte=timezone.now(),
            date_fin__gte=timezone.now(),
            active=True
        ).order_by('-pourcentage_reduction').first()
        
        if promotion_active:
            reduction = self.prix_unitaire * (promotion_active.pourcentage_reduction / 100)
            return self.prix_unitaire - reduction
        return self.prix_unitaire
    
    def get_all_prices(self):
        """Retourne tous les prix disponibles pour cet article (prix unitaire + upsells)"""
        prices = [self.prix_unitaire]
        if self.prix_upsell_1 is not None:
            prices.append(self.prix_upsell_1)
        if self.prix_upsell_2 is not None:
            prices.append(self.prix_upsell_2)
        if self.prix_upsell_3 is not None:
            prices.append(self.prix_upsell_3)
        return prices


class Promotion(models.Model):
    """
    Modèle pour les promotions appliquées aux articles
    """
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    pourcentage_reduction = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    active = models.BooleanField(default=True)
    articles = models.ManyToManyField(
        Article, 
        related_name='promotions',
        blank=True
    )
    code_promo = models.CharField(max_length=50, blank=True, null=True, unique=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Promotion"
        verbose_name_plural = "Promotions"
        ordering = ['-date_debut', 'nom']
        constraints = [
            models.CheckConstraint(
                check=models.Q(date_fin__gt=models.F('date_debut')), 
                name='date_fin_apres_debut'
            ),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.pourcentage_reduction}%)"
    
    @property
    def est_active(self):
        now = timezone.now()
        return self.active and self.date_debut <= now and self.date_fin >= now
    
    @property
    def est_future(self):
        return self.active and self.date_debut > timezone.now()
    
    @property
    def est_expiree(self):
        return self.date_fin < timezone.now()
