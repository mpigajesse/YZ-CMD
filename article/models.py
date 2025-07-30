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
    prix_achat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
    image_url = models.URLField(blank=True, null=True, help_text="Lien direct vers une image externe (ex: Unsplash)")
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    actif = models.BooleanField(default=True)
    
    # Nouveaux champs
    isUpsell = models.BooleanField(default=False, verbose_name="Est un upsell")
    
    # Prix de substitution (upsell)
    prix_upsell_1 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix upsell 1")
    prix_upsell_2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix upsell 2")
    prix_upsell_3 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix upsell 3")
    prix_upsell_4 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Prix upsell 4")
    
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
        base_str = f"{self.nom} - {self.couleur} - {self.pointure}"
        if self.isUpsell:
            base_str += f" (Upsell - PA: {self.prix_achat} MAD)"
        elif self.prix_achat > 0:
            base_str += f" (PA: {self.prix_achat} MAD)"
        return base_str
    
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
        
        # Désactiver automatiquement l'upsell pour les articles en liquidation ou en test
        if self.isUpsell and self.phase in ['LIQUIDATION', 'EN_TEST']:
            self.isUpsell = False
            
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
        
        # Désactiver automatiquement l'upsell si nécessaire
        if self.isUpsell and self.should_disable_upsell():
            self.isUpsell = False
        
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
            nouveau_prix = self.prix_unitaire - reduction
            # Arrondir à 2 décimales
            self.prix_actuel = Decimal(str(nouveau_prix)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            # Si pas de promotion, le prix actuel revient au prix unitaire
            self.prix_actuel = self.prix_unitaire
            
        self.save(update_fields=['prix_actuel'])
    
    def appliquer_promotion(self, promotion):
        """Applique une promotion spécifique à cet article"""
        if promotion.est_active and self in promotion.articles.all():
            reduction = self.prix_unitaire * (promotion.pourcentage_reduction / 100)
            nouveau_prix = self.prix_unitaire - reduction
            self.prix_actuel = Decimal(str(nouveau_prix)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Désactiver l'upsell automatiquement lors de l'application d'une promotion
            fields_to_update = ['prix_actuel']
            if self.isUpsell:
                self.isUpsell = False
                fields_to_update.append('isUpsell')
            
            self.save(update_fields=fields_to_update)
            return True
        return False
    
    def retirer_promotion(self):
        """Retire toutes les promotions et remet le prix actuel au prix unitaire"""
        self.prix_actuel = self.prix_unitaire
        
        # Note: Ne pas réactiver automatiquement l'upsell car cela doit être fait manuellement
        # L'upsell reste désactivé après une promotion pour éviter les activations non désirées
        
        self.save(update_fields=['prix_actuel'])
        return True
    
    def get_all_prices(self):
        """Retourne tous les prix disponibles pour cet article (prix unitaire + upsells)"""
        prices = [self.prix_unitaire]
        if self.prix_upsell_1 is not None:
            prices.append(self.prix_upsell_1)
        if self.prix_upsell_2 is not None:
            prices.append(self.prix_upsell_2)
        if self.prix_upsell_3 is not None:
            prices.append(self.prix_upsell_3)
        if self.prix_upsell_4 is not None:
            prices.append(self.prix_upsell_4)
        return prices

    @property
    def has_promo_active(self):
        """Retourne True si l'article a au moins une promotion active (non expirée et active=True)"""
        now = timezone.now()
        return self.promotions.filter(active=True, date_debut__lte=now, date_fin__gte=now).exists()

    @property
    def economie(self):
        """Retourne l'économie réalisée grâce aux promotions"""
        if self.prix_actuel is not None and self.prix_unitaire > self.prix_actuel:
            return self.prix_unitaire - self.prix_actuel
        return Decimal('0.00')
    
    def should_disable_upsell(self):
        """Vérifie si l'upsell devrait être désactivé automatiquement"""
        return (
            self.phase in ['LIQUIDATION', 'EN_TEST'] or
            (self.pk and self.has_promo_active)
        )

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
        elif quantite == 4 and self.prix_upsell_3:
            return self.prix_upsell_3
        elif quantite > 4 and self.prix_upsell_4:
            return self.prix_upsell_4
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
        elif quantite == 4:
            return 3 if self.prix_upsell_3 else 0
        elif quantite > 4:
            return 4 if self.prix_upsell_4 else 0
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
    
    def activer_promotion(self):
        """Active la promotion et applique les réductions aux articles"""
        self.active = True
        # Utiliser update() pour éviter de déclencher le signal post_save
        Promotion.objects.filter(id=self.id).update(active=True)
        
        # Appliquer la promotion à tous les articles associés
        for article in self.articles.all():
            article.appliquer_promotion(self)
        
        return True
    
    def desactiver_promotion(self):
        """Désactive la promotion et remet les prix des articles à leur état initial"""
        self.active = False
        # Utiliser update() pour éviter de déclencher le signal post_save
        Promotion.objects.filter(id=self.id).update(active=False)
        
        # Retirer la promotion de tous les articles associés
        for article in self.articles.all():
            # Vérifier si l'article n'a pas d'autres promotions actives
            autres_promotions_actives = article.promotions.filter(
                active=True,
                date_debut__lte=timezone.now(),
                date_fin__gte=timezone.now()
            ).exclude(id=self.id).exists()
            
            if not autres_promotions_actives:
                article.retirer_promotion()
            else:
                # Recalculer le prix avec les autres promotions actives
                article.update_prix_actuel()
        
        return True
    
    def verifier_et_appliquer_automatiquement(self):
        """Vérifie si la promotion doit être active et l'applique automatiquement"""
        now = timezone.now()
        
        # Si la promotion est dans sa période d'activité et n'est pas encore active
        if (self.date_debut <= now <= self.date_fin and not self.active):
            self.activer_promotion()
            return "activated"
        
        # Si la promotion est expirée et encore active
        elif (now > self.date_fin and self.active):
            self.desactiver_promotion()
            return "deactivated"
        
        return "no_change"
    
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
    
    def calculer_statistiques_prix(self):
        """Calcule les statistiques de prix pour tous les articles de la promotion"""
        articles = self.articles.all()
        
        if not articles:
            return {
                'prix_moyen_original': 0,
                'prix_moyen_reduit': 0,
                'economie_moyenne': 0,
                'economie_totale': 0,
                'prix_min_original': 0,
                'prix_max_original': 0,
                'prix_min_reduit': 0,
                'prix_max_reduit': 0
            }
        
        # Calculs des prix
        prix_originaux = [float(article.prix_unitaire) for article in articles]
        prix_reduits = [float(article.prix_actuel or article.prix_unitaire) for article in articles]
        economies = [float(article.economie) for article in articles]
        
        # Statistiques
        prix_moyen_original = sum(prix_originaux) / len(prix_originaux)
        prix_moyen_reduit = sum(prix_reduits) / len(prix_reduits)
        economie_moyenne = sum(economies) / len(economies)
        economie_totale = sum(economies)
        
        return {
            'prix_moyen_original': prix_moyen_original,
            'prix_moyen_reduit': prix_moyen_reduit,
            'economie_moyenne': economie_moyenne,
            'economie_totale': economie_totale,
            'prix_min_original': min(prix_originaux),
            'prix_max_original': max(prix_originaux),
            'prix_min_reduit': min(prix_reduits),
            'prix_max_reduit': max(prix_reduits),
            'nb_articles': len(articles)
        }

class Categorie(models.Model):
    """
    Modèle pour les catégories d'articles
    """
    isUpsell = models.BooleanField(default=False)
    qte_disponible = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
    
    def __str__(self):
        return f"Catégorie - Upsell: {self.isUpsell}"


class MouvementStock(models.Model):
    """
    Modèle pour tracer les mouvements de stock des articles
    """
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
    commentaire = models.TextField(blank=True, null=True)
    commande_associee = models.ForeignKey(
        'commande.Commande', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        help_text="Commande liée à ce mouvement (si applicable)"
    )
    operateur = models.ForeignKey(
        'parametre.Operateur', 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True
    )
    
    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ['-date_mouvement']
    
    def __str__(self):
        return f"{self.article.nom} - {self.get_type_mouvement_display()} - {self.quantite}"


# Signal pour initialiser le prix actuel au prix unitaire lors de la création
@receiver(post_save, sender=Article)
def initialize_prix_actuel(sender, instance, created, **kwargs):
    # Si l'article vient d'être créé et que le prix actuel n'est pas défini
    if created and instance.prix_actuel is None:
        instance.prix_actuel = instance.prix_unitaire
        instance.save(update_fields=['prix_actuel'])

# Signal pour automatiquement mettre à jour les articles quand une promotion est modifiée ou expirée
@receiver(post_save, sender=Promotion)
def update_article_prices(sender, instance, created, **kwargs):
    """Met à jour les prix des articles quand une promotion est modifiée"""
    from django.utils import timezone
    
    # Vérifier automatiquement si la promotion doit être active (seulement pour les nouvelles promotions)
    if created:
        now = timezone.now()
        if instance.date_debut <= now <= instance.date_fin:
            instance.activer_promotion()
    
    # Pour tous les articles associés à cette promotion
    for article in instance.articles.all():
        # Mettre à jour le prix actuel basé sur toutes les promotions actives
        article.update_prix_actuel()