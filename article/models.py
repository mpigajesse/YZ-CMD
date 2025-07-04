from sre_parse import CATEGORIES
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP

# Create your models here.

class Article(models.Model):
    """
    Modèle pour les articles
    """
    # Choix pour la phase
    PHASE_CHOICES = [
        ('EN_COURS', 'En Cours'),
        ('LIQUIDATION', 'Liquidation'),
        ('EN_TEST', 'En Test'),
    ]
    
    CATEGORIES_CHOICES = [
        ('HOMME', 'Homme'),
        ('FEMME', 'Femme'),
    ]
    
    nom = models.CharField(max_length=200)
    reference = models.CharField(max_length=50, unique=True, null=True, blank=True, default=None)
    couleur = models.CharField(max_length=50)
    pointure = models.CharField(max_length=10)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    prix_actuel = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    categorie = models.CharField(max_length=100)
    phase = models.CharField(
        max_length=20,
        choices=PHASE_CHOICES,
        default='EN_COURS',
        verbose_name="Phase de l'article"
    )
    qte_disponible = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='articles/', blank=True, null=True)
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    
    # Nouveaux champs
    isUpsell = models.BooleanField(default=False, verbose_name="Est un upsell")
    
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
            # Contrainte: Un article marqué comme upsell doit être en phase 'EN_COURS'
            models.CheckConstraint(
                check=models.Q(isUpsell=False) | models.Q(phase='EN_COURS'),
                name='upsell_seulement_en_cours'
            ),
        ]
    
    def __str__(self):
        return f"{self.nom} - {self.couleur} - {self.pointure}"
    
    def clean(self):
        # Vérifier que le prix actuel a exactement 2 décimales
        if self.prix_actuel is not None:
            # Convertir en Decimal et vérifier le nombre de décimales
            prix_decimal = Decimal(str(self.prix_actuel))
            # Vérifier que le nombre de décimales est <= 2
            if prix_decimal != prix_decimal.quantize(Decimal('0.01')):
                raise ValidationError({
                    'prix_actuel': 'Assurez-vous qu\'il n\'y a pas plus de 2 chiffres après la virgule.'
                })
        
        # Vérification existante pour upsell
        if self.isUpsell and self.phase != 'EN_COURS':
            raise ValidationError("Un article ne peut pas être marqué comme 'upsell' s'il est en liquidation ou en test.")
            
        # Vérifier qu'un article en promotion n'est pas marqué comme upsell
        if self.isUpsell and self.has_promo_active:
            raise ValidationError("Un article ne peut pas être marqué comme 'upsell' s'il est en promotion.")
        
        super().clean()
    
    def save(self, *args, **kwargs):
        # Toujours s'assurer que prix_actuel est défini
        if self.prix_actuel is None:
            self.prix_actuel = self.prix_unitaire
        
        # Arrondir le prix actuel à 2 décimales si nécessaire
        self.prix_actuel = Decimal(str(self.prix_actuel)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        super().save(*args, **kwargs)
    
    @property
    def est_disponible(self):
        return self.qte_disponible > 0 and self.actif
    
    def update_prix_actuel(self):
        """Met à jour le prix actuel en tenant compte des promotions actives"""
        now = timezone.now()
        promotion_active = self.promotions.filter(
            date_debut__lte=now,
            date_fin__gte=now,
            active=True
        ).order_by('-pourcentage_reduction').first()
        
        # Prix actuel = prix unitaire par défaut
        if self.prix_actuel is None:
            self.prix_actuel = self.prix_unitaire
        
        # Appliquer la réduction si une promotion est active
        if promotion_active:
            reduction = self.prix_unitaire * (promotion_active.pourcentage_reduction / 100)
            self.prix_actuel = self.prix_unitaire - reduction
        else:
            # Si pas de promotion, le prix actuel est égal au prix unitaire
            self.prix_actuel = self.prix_unitaire
            
        self.save(update_fields=['prix_actuel'])
    
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

    @property
    def has_promo_active(self):
        """Retourne True si l'article a au moins une promotion active (non expirée et active=True)"""
        now = timezone.now()
        return self.promotions.filter(active=True, date_debut__lte=now, date_fin__gte=now).exists()

    def get_prix_upsell(self, quantite):
        """
        Retourne le prix approprié en fonction de la quantité pour un article upsell.
        """
        if not self.isUpsell:
            return self.prix_actuel if self.prix_actuel is not None else self.prix_unitaire
            
        if quantite == 1:
            return self.prix_actuel if self.prix_actuel is not None else self.prix_unitaire
        elif quantite == 2 and self.prix_upsell_1:
            return self.prix_upsell_1
        elif quantite == 3 and self.prix_upsell_2:
            return self.prix_upsell_2
        elif quantite > 3 and self.prix_upsell_3:
            return self.prix_upsell_3
        else:
            return self.prix_actuel if self.prix_actuel is not None else self.prix_unitaire
            
    def get_increment_compteur(self, quantite):
        """
        Retourne l'incrément du compteur en fonction de la quantité pour un article upsell.
        """
        if not self.isUpsell:
            return 0
            
        if quantite == 1:
            return 0
        elif quantite == 2:
            return 1 if self.prix_upsell_1 else 0
        elif quantite == 3:
            return 2 if self.prix_upsell_2 else 0
        elif quantite > 3:
            return 3 if self.prix_upsell_3 else 0
        return 0


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
        blank=True,
        limit_choices_to={'phase': 'EN_COURS'}  # Limite les choix aux articles en phase "En Cours"
    )

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
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # On ne peut vérifier les articles que si l'instance a déjà un ID
        if self.pk:
            # Vérifier que tous les articles sont en phase "En Cours"
            articles_non_valides = self.articles.exclude(phase='EN_COURS')
            if articles_non_valides.exists():
                raise ValidationError({
                    'articles': "Seuls les articles en phase 'En Cours' peuvent être ajoutés à une promotion. "
                               f"Articles non valides : {', '.join(str(a) for a in articles_non_valides)}"
                })
    
    def save(self, *args, **kwargs):
        # Ne pas appeler clean() ici pour éviter l'erreur
        super().save(*args, **kwargs)
    
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

# Signal pour initialiser le prix actuel au prix unitaire lors de la création
@receiver(post_save, sender=Article)
def initialize_prix_actuel(sender, instance, created, **kwargs):
    # Si l'article vient d'être créé et que le prix actuel n'est pas défini
    if created and instance.prix_actuel is None:
        instance.prix_actuel = instance.prix_unitaire
        instance.save(update_fields=['prix_actuel'])

# Signal pour automatiquement mettre à jour les articles quand une promotion est modifiée ou expirée
@receiver(post_save, sender=Promotion)
def update_article_prices(sender, instance, **kwargs):
    # Pour tous les articles associés à cette promotion
    for article in instance.articles.all():
        # Mettre à jour le prix actuel basé sur les promotions actives
        article.update_prix_actuel()

class Categorie(models.Model):
    isUpsell = models.BooleanField(default=False)
    qte_disponible = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    def __str__(self):
        return f"{self.nom} ({self.reference})"

class MouvementStock(models.Model):
    TYPE_MOUVEMENT_CHOICES = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
        ('ajustement_pos', 'Ajustement Positif'),
        ('ajustement_neg', 'Ajustement Négatif'),
        ('inventaire', 'Inventaire'),
        ('retour_client', 'Retour Client'),
    ]
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='mouvements')
    type_mouvement = models.CharField(max_length=20, choices=TYPE_MOUVEMENT_CHOICES)
    quantite = models.IntegerField(help_text="Quantité du mouvement. Positive pour une entrée, négative pour une sortie.")
    qte_apres_mouvement = models.IntegerField()
    date_mouvement = models.DateTimeField(auto_now_add=True)
    operateur = models.ForeignKey('parametre.Operateur', on_delete=models.SET_NULL, null=True, blank=True)
    commentaire = models.TextField(blank=True, null=True)
    commande_associee = models.ForeignKey('commande.Commande', on_delete=models.SET_NULL, null=True, blank=True, help_text="Commande liée à ce mouvement (si applicable)")

    def __str__(self):
        return f"{self.get_type_mouvement_display()} de {self.quantite} pour {self.article.nom}"

    class Meta:
        ordering = ['-date_mouvement']
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"