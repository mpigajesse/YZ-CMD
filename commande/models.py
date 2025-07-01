from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from client.models import Client
from article.models import Article
from parametre.models import Ville, Operateur

# Create your models here.

class EnumEtatCmd(models.Model):
    # Choix d'états de commande complets
    STATUS_CHOICES = [
        # États initiaux
        ('recue', 'Reçue'),
        ('non_affectee', 'Non affectée'),
        ('affectee', 'Affectée'),
        
        # États de confirmation
        ('en_cours_confirmation', 'En cours de confirmation'),
        ('confirmee', 'Confirmée'),
        
        # États problématiques
        ('erronnee', 'Erronée'),
        ('doublon', 'Doublon'),
        
        # États de préparation
        ('en_cours_preparation', 'En cours de préparation'),
        ('preparee', 'Préparée'),
        
        # États de livraison
        ('en_cours_livraison', 'En cours de livraison'),
        ('livree', 'Livrée'),
        ('retournee', 'Retournée'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('non_paye', 'Non payé'),
        ('partiellement_paye', 'Partiellement payé'),
        ('paye', 'Payé'),
    ]
    
    # Anciens choix de livraison conservés pour compatibilité
    DELIVERY_STATUS_CHOICES = [
        ('en_preparation', 'En préparation'),
        ('en_livraison', 'En livraison'),
        ('livree', 'Livrée'),
        ('retournee', 'Retournée'),
    ]
    
    libelle = models.CharField(max_length=100, unique=True)
    ordre = models.IntegerField(default=0)  # Pour ordonner les états
    couleur = models.CharField(max_length=7, default='#6B7280')  # Code couleur hex
    
    class Meta:
        verbose_name = "Définition d'état de commande(EnumEtatCmd)"
        verbose_name_plural = "Définitions d'états de commande(EnumEtatCmd)"
        ordering = ['ordre', 'libelle']
    
    def __str__(self):
        return self.libelle


class Commande(models.Model):
    num_cmd = models.CharField(max_length=50, unique=True)
    id_yz = models.PositiveIntegerField(unique=True, null=True, blank=True)  # Auto-incrémentation simple
    date_cmd = models.DateField(default=timezone.now)
    total_cmd = models.FloatField()
    adresse = models.TextField()
    motif_annulation = models.TextField(blank=True, null=True)
    is_upsell = models.BooleanField(default=False)
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='commandes')
    ville_init = models.CharField(max_length=100, blank=True, null=True)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, null=True, blank=True, related_name='commandes')
    produit_init = models.TextField(blank=True, null=True)  # Champ pour le produit brut du CSV
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-date_cmd', '-date_creation', 'id_yz']
        constraints = [
            models.CheckConstraint(check=models.Q(total_cmd__gte=0), name='total_cmd_positif'),
        ]
    
    def save(self, *args, **kwargs):
        # Générer l'ID YZ automatiquement si ce n'est pas encore fait
        if not self.id_yz:
            # Obtenir le dernier ID YZ et ajouter 1
            last_id_yz = Commande.objects.aggregate(
                max_id=models.Max('id_yz')
            )['max_id']
            self.id_yz = (last_id_yz or 0) + 1
        
        # Si num_cmd n'est pas défini, utiliser l'ID YZ
        if not self.num_cmd:
            self.num_cmd = str(self.id_yz)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Commande {self.id_yz or self.num_cmd} - {self.client}"
    
    @property
    def etat_actuel(self):
        """Retourne l'état actuel de la commande"""
        return self.etats.filter(date_fin__isnull=True).first()
    
    @property
    def historique_etats(self):
        """Retourne l'historique complet des états"""
        return self.etats.all().order_by('date_debut')


class Panier(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='paniers')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='paniers')
    quantite = models.IntegerField()
    sous_total = models.FloatField()
    
    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"
        unique_together = [['commande', 'article']]
        constraints = [
            models.CheckConstraint(check=models.Q(quantite__gt=0), name='quantite_positive'),
            models.CheckConstraint(check=models.Q(sous_total__gte=0), name='sous_total_positif'),
        ]
    
    def __str__(self):
        return f"{self.commande.num_cmd} - {self.article.nom} (x{self.quantite})"


class EtatCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='etats')
    enum_etat = models.ForeignKey(EnumEtatCmd, on_delete=models.CASCADE)
    date_debut = models.DateTimeField(default=timezone.now)
    date_fin = models.DateTimeField(blank=True, null=True)
    commentaire = models.TextField(blank=True, null=True)
    operateur = models.ForeignKey(Operateur, on_delete=models.CASCADE, related_name='etats_modifies', blank=True, null=True)
    
    class Meta:
        verbose_name = "État de commande(Suivi de commande)"
        verbose_name_plural = "États de commande(Suivi de commande)"
        ordering = ['-date_debut']
        constraints = [
            models.CheckConstraint(
                check=models.Q(date_fin__isnull=True) | models.Q(date_debut__lte=models.F('date_fin')),
                name='date_debut_avant_date_fin'
            ),
        ]
    
    def __str__(self):
        return f"{self.commande.num_cmd} - {self.enum_etat.libelle}"
    
    def terminer_etat(self, operateur=None):
        """Termine cet état en définissant la date_fin"""
        self.date_fin = timezone.now()
        if operateur:
            self.operateur = operateur
        self.save()
    
    @property
    def duree(self):
        """Retourne la durée de cet état"""
        if self.date_fin:
            return self.date_fin - self.date_debut
        return timezone.now() - self.date_debut


class Operation(models.Model):
    TYPE_OPERATION_CHOICES = [
        # Opérations spécifiques de confirmation
        ('APPEL', 'Appel '),
        ("Appel Whatsapp", "Appel Whatsapp"),
        ("Message Whatsapp", "Appel Whatsapp "),
        ("Vocal Whatsapp", "Vocal Whatsapp "),
        ('ENVOI_SMS', 'Envoi de SMS'),
    ]
    Type_Commentaire_CHOICES=[
        ("Commande Annulée", "Commande Annulée"),
        ("Client hésitant", "Client hésitant"),
        ("Client intéressé", "Client intéressé"),
        ("Client non intéressé", "Client non intéressé"),
        ("Client non joignable", "Client non joignable"),
        ("commande reportée", "commande reportée"),
        ("Article non disponible", "Article non disponible"),
        
    ]
    
    type_operation = models.CharField(max_length=30, choices=TYPE_OPERATION_CHOICES)
    date_operation = models.DateTimeField(default=timezone.now)
    conclusion = models.TextField()
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='operations')
    operateur = models.ForeignKey(Operateur, on_delete=models.CASCADE, related_name='operations')
    commentaire = models.TextField( blank=True, null=True,choices=Type_Commentaire_CHOICES)
    
    class Meta:
        verbose_name = "Opération"
        verbose_name_plural = "Opérations"
        ordering = ['-date_operation']
    
    def __str__(self):
        return f"{self.get_type_operation_display()} - {self.commande.num_cmd} par {self.operateur}"
