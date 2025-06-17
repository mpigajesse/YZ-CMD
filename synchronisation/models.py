from django.db import models
from django.utils import timezone

class GoogleSheetConfig(models.Model):
    """Configuration pour la connexion à Google Sheets"""
    sheet_url = models.URLField(verbose_name="URL de la feuille Google Sheet")
    sheet_name = models.CharField(max_length=100, verbose_name="Nom de la feuille")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.sheet_name} ({self.sheet_url})"
    
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
    
    def __str__(self):
        return f"Synchronisation du {self.sync_date.strftime('%d/%m/%Y %H:%M')} - {self.get_status_display()}"
    
    class Meta:
        verbose_name = "Log de synchronisation"
        verbose_name_plural = "Logs de synchronisation"
        ordering = ['-sync_date']
