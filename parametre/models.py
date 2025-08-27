from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class Region(models.Model):
    nom_region = models.CharField(max_length=100, unique=True)
    actif = models.BooleanField(default=False)
    
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
        ('SUPERVISEUR_PREPARATION', 'Superviseur de Préparation'),
    ]
    
    @property
    def is_livraison(self):
        """
        Propriété qui indique si l'opérateur est un opérateur logistique (de livraison)
        """
        return self.type_operateur == 'LOGISTIQUE'
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_operateur')
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    mail = models.EmailField()
    type_operateur = models.CharField(max_length=30, choices=TYPE_OPERATEUR_CHOICES, default='CONFIRMATION')
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
        # Autoriser les superviseurs à être traités comme équipe préparation
        return self.type_operateur in ['PREPARATION', 'SUPERVISEUR_PREPARATION']
    
    @property
    def is_superviseur_preparation(self):
        return self.type_operateur == 'SUPERVISEUR_PREPARATION'
        
    @property
    def is_admin(self):
        return self.type_operateur == 'ADMIN'
    
    @property
    def is_superviseur(self):
        """Propriété qui indique si l'opérateur est un superviseur"""
        return self.type_operateur == 'SUPERVISEUR_PREPARATION'
    
    @classmethod
    def get_superviseurs(cls):
        """Retourne tous les superviseurs actifs"""
        return cls.objects.filter(
            type_operateur='SUPERVISEUR_PREPARATION',
            actif=True
        )
    
    @classmethod
    def get_by_group(cls, group_name):
        """Retourne tous les opérateurs d'un groupe spécifique"""
        group_mapping = {
            'operateur_confirme': 'CONFIRMATION',
            'operateur_logistique': 'LOGISTIQUE',
            'operateur_preparation': 'PREPARATION',
            'superviseur': 'SUPERVISEUR_PREPARATION',
            'admin': 'ADMIN'
        }
        
        if group_name in group_mapping:
            return cls.objects.filter(
                type_operateur=group_mapping[group_name],
                actif=True
            )
        return cls.objects.none()
    
    def get_group_name(self):
        """Retourne le nom du groupe Django correspondant au type d'opérateur"""
        group_mapping = {
            'CONFIRMATION': 'operateur_confirme',
            'LOGISTIQUE': 'operateur_logistique',
            'PREPARATION': 'operateur_preparation',
            'SUPERVISEUR_PREPARATION': 'superviseur',
            'ADMIN': 'admin'
        }
        return group_mapping.get(self.type_operateur, '')
    
    def sync_django_groups(self):
        """Synchronise les groupes Django avec le type d'opérateur"""
        from django.contrib.auth.models import Group
        
        # Supprimer l'utilisateur de tous les groupes d'opérateurs
        groups_to_remove = [
            'operateur_confirme',
            'operateur_logistique', 
            'operateur_preparation',
            'superviseur',
            'admin'
        ]
        
        for group_name in groups_to_remove:
            try:
                group = Group.objects.get(name=group_name)
                self.user.groups.remove(group)
            except Group.DoesNotExist:
                pass
        
        # Ajouter l'utilisateur au bon groupe
        target_group_name = self.get_group_name()
        if target_group_name:
            try:
                target_group = Group.objects.get(name=target_group_name)
                self.user.groups.add(target_group)
            except Group.DoesNotExist:
                # Créer le groupe s'il n'existe pas
                target_group = Group.objects.create(name=target_group_name)
                self.user.groups.add(target_group)
    
    def check_group_consistency(self):
        """Vérifie la cohérence entre le type d'opérateur et les groupes Django"""
        expected_group = self.get_group_name()
        if not expected_group:
            return False, f"Type d'opérateur '{self.type_operateur}' non reconnu"
        
        user_groups = [group.name for group in self.user.groups.all()]
        
        if expected_group not in user_groups:
            return False, f"Utilisateur pas dans le groupe '{expected_group}'"
        
        # Vérifier qu'il n'est pas dans d'autres groupes d'opérateurs
        operator_groups = [
            'operateur_confirme',
            'operateur_logistique',
            'operateur_preparation', 
            'superviseur',
            'admin'
        ]
        
        extra_groups = [group for group in user_groups if group in operator_groups and group != expected_group]
        if extra_groups:
            return False, f"Utilisateur dans des groupes supplémentaires: {extra_groups}"
        
        return True, "Cohérence OK"
    
    @classmethod
    def create_superviseur_from_user(cls, user, **kwargs):
        """Crée un superviseur depuis un utilisateur existant"""
        defaults = {
            'nom': user.last_name or '',
            'prenom': user.first_name or '',
            'mail': user.email or '',
            'type_operateur': 'SUPERVISEUR_PREPARATION',
            'actif': True
        }
        defaults.update(kwargs)
        
        # Créer ou mettre à jour l'opérateur
        operateur, created = cls.objects.get_or_create(
            user=user,
            defaults=defaults
        )
        
        if not created:
            # Mettre à jour le type d'opérateur
            operateur.type_operateur = 'SUPERVISEUR_PREPARATION'
            operateur.nom = defaults['nom']
            operateur.prenom = defaults['prenom']
            operateur.mail = defaults['mail']
            operateur.actif = defaults['actif']
            operateur.save()
        
        # Synchroniser les groupes Django
        operateur.sync_django_groups()
        
        return operateur
    
    @classmethod
    def get_all_types_display(cls):
        """Retourne tous les types d'opérateur avec leurs noms d'affichage"""
        return dict(cls.TYPE_OPERATEUR_CHOICES)



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
