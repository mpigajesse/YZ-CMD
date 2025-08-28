from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from client.models import Client
from article.models import Article, VarianteArticle
from parametre.models import Ville, Operateur

# Create your models here.

class EnumEtatCmd(models.Model):
    # Choix d'états de commande
    STATUS_CHOICES = [
        ('non_affectee', 'Non affectée'),
        ('affectee', 'Affectée'),
        ('en_cours_confirmation', 'En cours de confirmation'),
        ('confirmee', 'Confirmée'),
        ('erronnee', 'Erronée'),
        ('doublon', 'Doublon'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('non_paye', 'Non payé'),
        ('partiellement_paye', 'Partiellement payé'),
        ('paye', 'Payé'),
    ]
    
    DELIVERY_STATUS_CHOICES = [
        ('à imprimer', 'À imprimer'),
        ('en_preparation', 'En préparation'),
        ('collectee', 'Collectée'),
        ('emballee', 'Emballée'),
        ('validee', 'Validée'),
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
    ORIGINE_CHOICES = [
        ('OC', 'Opérateur Confirmation'),
        ('ADMIN', 'Administrateur'),
        ('SYNC', 'Synchronisation')
    ]
    
    num_cmd = models.CharField(max_length=50, unique=True)
    id_yz = models.PositiveIntegerField(unique=True, null=True, blank=True)
    origine = models.CharField(max_length=10, choices=ORIGINE_CHOICES, default='SYNC')
    date_cmd = models.DateField(default=timezone.now)
    total_cmd = models.FloatField()
    adresse = models.TextField()
    motif_annulation = models.TextField(blank=True, null=True)
    is_upsell = models.BooleanField(default=False)
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(auto_now=True)
    last_sync_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de dernière synchronisation")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='commandes')
    ville_init = models.CharField(max_length=100, blank=True, null=True)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, null=True, blank=True, related_name='commandes')
    produit_init = models.TextField(blank=True, null=True)
    compteur = models.IntegerField(default=0, verbose_name="Compteur d'utilisation")
  
    # Relation avec Envoi pour les exports journaliers
    envoi = models.ForeignKey('Envoi', on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes_associees')
  
    
    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-date_cmd', '-date_creation', 'id_yz']
        constraints = [
            models.CheckConstraint(check=models.Q(total_cmd__gte=0), name='total_cmd_positif'),
        ]
    
    # Point de départ souhaité pour id_yz
    START_ID_YZ = 211971

    def save(self, *args, **kwargs):
        # Générer l'ID YZ automatiquement si ce n'est pas encore fait
        if self.id_yz is None:
            last_id_yz = Commande.objects.aggregate(max_id=models.Max('id_yz'))['max_id']
            base = self.START_ID_YZ - 1
            # Si aucune commande, commencer à 211971; sinon continuer après le max existant
            self.id_yz = max(last_id_yz or base, base) + 1
        
        # Générer le numéro de commande selon l'origine si ce n'est pas déjà fait
        if not self.num_cmd:
            if self.origine == 'OC':
                # Format pour les opérateurs de confirmation: OC-00001
                prefix = 'OC-'
                last_oc = Commande.objects.filter(
                    num_cmd__startswith=prefix
                ).order_by('-num_cmd').first()
                
                if last_oc:
                    last_number = int(last_oc.num_cmd.split('-')[1])
                    new_number = last_number + 1
                else:
                    new_number = 1
                
                self.num_cmd = f"{prefix}{new_number:05d}"
                
            elif self.origine == 'ADMIN':
                # Format pour les administrateurs: ADMIN-00001
                prefix = 'ADMIN-'
                last_admin = Commande.objects.filter(
                    num_cmd__startswith=prefix
                ).order_by('-num_cmd').first()
                
                if last_admin:
                    last_number = int(last_admin.num_cmd.split('-')[1])
                    new_number = last_number + 1
                else:
                    new_number = 1
                
                self.num_cmd = f"{prefix}{new_number:05d}"
            else:
                # Pour les commandes synchronisées, utiliser l'ID YZ comme avant
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

    def recalculer_totaux_upsell(self):
        """
        Recalcule automatiquement les totaux de la commande selon le compteur upsell.
        Tous les articles de la commande prennent le prix upsell correspondant au compteur.
        """
        from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
        
        print(f"🔄 recalculer_totaux_upsell - Compteur actuel: {self.compteur}")
        
        nouveau_total = 0
        
        # Recalculer chaque panier selon le compteur upsell
        for panier in self.paniers.all():
            # Calculer le prix selon le compteur de la commande
            prix_unitaire = get_prix_upsell_avec_compteur(panier.article, self.compteur)
            nouveau_sous_total = prix_unitaire * panier.quantite
            
            print(f"   📦 {panier.article.nom} (upsell: {panier.article.isUpsell}): qté={panier.quantite}, prix={prix_unitaire}, sous_total={nouveau_sous_total}")
            
            # Mettre à jour le sous-total du panier si nécessaire
            if panier.sous_total != nouveau_sous_total:
                panier.sous_total = float(nouveau_sous_total)
                panier.save()
            
            nouveau_total += nouveau_sous_total
        
        # Ajouter les frais de livraison au total
        frais_livraison = self.ville.frais_livraison if self.ville else 0
        nouveau_total_avec_frais = float(nouveau_total) + float(frais_livraison)
        
        # Mettre à jour le total de la commande si nécessaire
        if self.total_cmd != nouveau_total_avec_frais:
            self.total_cmd = nouveau_total_avec_frais
            self.save(update_fields=['total_cmd'])
    
    @property
    def sous_total_articles(self):
        """Retourne le sous-total des articles sans les frais de livraison"""
        return sum(panier.sous_total for panier in self.paniers.all())
    
    @property
    def frais_livraison(self):
        """Retourne les frais de livraison"""
        frais = self.ville.frais_livraison if self.ville else 0
        return float(frais)
    
    @property
    def total_avec_frais(self):
        """Retourne le total articles + frais de livraison"""
        return float(self.sous_total_articles) + float(self.frais_livraison)


class Panier(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='paniers')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='paniers')
    variante = models.ForeignKey(VarianteArticle, on_delete=models.SET_NULL, null=True, blank=True, related_name='paniers')
    quantite = models.IntegerField()
    sous_total = models.FloatField()
    
    class Meta:
        verbose_name = "Panier"
        verbose_name_plural = "Paniers"
        unique_together = [['commande', 'article', 'variante']]
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
        ('MODIFICATION', 'Modification'),
        ('PROBLEME_SIGNALÉ', 'Problème signalé'),
        ('RENVOI_PREPARATION', 'Renvoi en préparation'),
        # Opérations d'affectation par supervision
        ('AFFECTATION_SUPERVISION', 'Affectation par supervision'),
        ('REAFFECTATION_SUPERVISION', 'Réaffectation par supervision'),
        # Opérations d'affectation par admin
        ('AFFECTATION_ADMIN', 'Affectation par admin'),
        ('REAFFECTATION_ADMIN', 'Réaffectation par admin'),
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


class Envoi(models.Model):


    # Relations
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='envois', null=True, blank=True)   
    region = models.ForeignKey(
        'parametre.Region', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='envois'
    )
    
    # Informations principales
    date_envoi = models.DateField(default=timezone.now, verbose_name="Date d'envoi")
    date_livraison_prevue = models.DateField(verbose_name="Date de livraison prévue")
    date_livraison_effective = models.DateField(null=True, blank=True, verbose_name="Date de clôture")
    
    # Statut et suivi
    status = models.BooleanField(default=True, verbose_name="En cours")
    numero_envoi = models.CharField(max_length=50, blank=True, verbose_name="Numéro d'envoi")
    
    # Opérateurs et traçabilité
    operateur_creation = models.ForeignKey(
        Operateur, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='envois_crees',
        verbose_name="Créé par"
    )
    
    # Dates de suivi
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    # Statistiques
    nb_commandes = models.PositiveIntegerField(default=0, verbose_name="Nombre de commandes")

    class Meta:
        verbose_name = "Envoi"
        verbose_name_plural = "Envois"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['status', 'date_creation']),
            models.Index(fields=['region', 'date_envoi']),
        ]

    def save(self, *args, **kwargs):
        # Générer automatiquement le numéro d'envoi si pas défini
        if not self.numero_envoi:
            from django.utils import timezone
            today = timezone.now().date()
            count = Envoi.objects.filter(date_creation__date=today).count() + 1
            self.numero_envoi = f"ENV-{today.strftime('%Y%m%d')}-{count:04d}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        status_text = "En cours" if self.status else "Clôturé"
        return f"Envoi {self.numero_envoi} - {status_text}"

    @property
    def commandes_associees(self):
        """Retourne les commandes associées à cet envoi"""
        return self.commande_set.all()

    def marquer_comme_livre(self, operateur, date_livraison=None):
        """Marquer l'envoi comme livré (clôturé)"""
        from django.utils import timezone
        self.status = False  # False = clôturé
        self.date_livraison_effective = date_livraison or timezone.now().date()
        self.save()

    def annuler(self, operateur):
        """Annuler l'envoi"""
        self.status = False  # False = annulé/clôturé
        self.save()

class EtatArticleRenvoye(models.Model):
    commande = models.ForeignKey('Commande', on_delete=models.CASCADE, related_name='etats_articles_renvoyes')
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    etat = models.ForeignKey(EnumEtatCmd, on_delete=models.PROTECT)  # FK vers la table d’états
    quantite = models.PositiveIntegerField(default=1)
    date_maj = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('commande', 'article')
        verbose_name = "État d'article renvoyé"
        verbose_name_plural = "États d'articles renvoyés"

    def __str__(self):
        return f"{self.article} ({self.etat}) dans {self.commande}"

