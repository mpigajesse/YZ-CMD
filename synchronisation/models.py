from django.db import models
from django.utils import timezone

class GoogleSheetConfig(models.Model):
    """Configuration pour la connexion à Google Sheets"""
    sheet_url = models.URLField(verbose_name="URL de la feuille Google Sheet")
    sheet_name = models.CharField(max_length=100, verbose_name="Nom de la feuille")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Nouveau champ pour optimiser la synchronisation incrémentale
    last_processed_row = models.IntegerField(
        default=0, 
        verbose_name="Dernière ligne traitée",
        help_text="Numéro de la dernière ligne traitée lors de la synchronisation précédente"
    )
    
    def __str__(self):
        return f"{self.sheet_name} ({self.sheet_url})"
    
    @property
    def last_sync(self):
        """Retourne la date de la dernière synchronisation réussie"""
        latest_log = self.sync_logs.filter(status__in=['success', 'partial']).first()
        return latest_log.sync_date if latest_log else None
    
    @property
    def last_sync_status(self):
        """Retourne le statut de la dernière synchronisation"""
        latest_log = self.sync_logs.first()
        return latest_log.status if latest_log else None
    
    @property
    def last_sync_records(self):
        """Retourne le nombre d'enregistrements de la dernière synchronisation"""
        latest_log = self.sync_logs.filter(status__in=['success', 'partial']).first()
        return latest_log.records_imported if latest_log else 0
    
    @property
    def next_sync_start_row(self):
        """Retourne la ligne de départ pour la prochaine synchronisation"""
        return self.last_processed_row + 1
    
    class Meta:
        verbose_name = "Configuration Google Sheet"
        verbose_name_plural = "Configurations Google Sheet"

class SyncLog(models.Model):
    """Logs de synchronisation avec Google Sheets"""
    STATUS_CHOICES = [
        ('success', 'Succès'),
        ('error', 'Erreur'),
        ('partial', 'Partiel'),
    ]
    
    sync_date = models.DateTimeField(auto_now_add=True, verbose_name="Date de synchronisation")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name="Statut")
    records_imported = models.IntegerField(default=0, verbose_name="Enregistrements importés")
    errors = models.TextField(blank=True, null=True, verbose_name="Erreurs")
    sheet_config = models.ForeignKey(GoogleSheetConfig, on_delete=models.CASCADE, related_name='sync_logs')
    triggered_by = models.CharField(max_length=100, verbose_name="Déclenché par")
    
    # Nouveaux champs pour les détails d'exécution
    start_time = models.DateTimeField(null=True, blank=True, verbose_name="Heure de début")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="Heure de fin")
    total_rows = models.IntegerField(null=True, blank=True, verbose_name="Total lignes dans la feuille")
    processed_rows = models.IntegerField(null=True, blank=True, verbose_name="Lignes traitées")
    skipped_rows = models.IntegerField(null=True, blank=True, verbose_name="Lignes ignorées")
    sheet_title = models.CharField(max_length=200, null=True, blank=True, verbose_name="Titre de la feuille")
    execution_details = models.JSONField(null=True, blank=True, verbose_name="Détails d'exécution")
    
    # Nouveaux champs pour les statistiques détaillées
    new_orders_created = models.IntegerField(default=0, verbose_name="Nouvelles commandes créées")
    existing_orders_updated = models.IntegerField(default=0, verbose_name="Commandes existantes mises à jour") 
    existing_orders_skipped = models.IntegerField(default=0, verbose_name="Commandes existantes inchangées")
    duplicate_orders_found = models.IntegerField(default=0, verbose_name="Doublons détectés et évités")
    protected_orders_count = models.IntegerField(default=0, verbose_name="Commandes protégées contre la régression d'état")
    
    def __str__(self):
        return f"Synchronisation du {self.sync_date.strftime('%d/%m/%Y %H:%M')} - {self.get_status_display()}"
    
    @property
    def duration(self):
        """Calcule la durée de la synchronisation"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds()
        return None
    
    @property
    def duration_formatted(self):
        """Retourne la durée formatée"""
        duration = self.duration
        if duration is None:
            return "Non calculée"
        
        if duration < 60:
            return f"{duration:.1f}s"
        elif duration < 3600:
            minutes = duration // 60
            seconds = duration % 60
            return f"{int(minutes)}m {seconds:.0f}s"
        else:
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            return f"{int(hours)}h {int(minutes)}m"
    
    @property
    def processing_speed(self):
        """Calcule la vitesse de traitement en lignes par seconde"""
        if self.duration and self.duration > 0 and self.processed_rows:
            return self.processed_rows / self.duration
        return 0
    
    @property
    def processing_speed_formatted(self):
        """Retourne la vitesse de traitement formatée"""
        speed = self.processing_speed
        if speed == 0:
            return "Non calculée"
        elif speed < 1:
            return f"{speed:.2f} lignes/s"
        else:
            return f"{speed:.1f} lignes/s"
    
    class Meta:
        verbose_name = "Log de synchronisation"
        verbose_name_plural = "Logs de synchronisation"
        ordering = ['-sync_date']
