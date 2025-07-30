from django.contrib import admin
from .models import GoogleSheetConfig, SyncLog

@admin.register(GoogleSheetConfig)
class GoogleSheetConfigAdmin(admin.ModelAdmin):
    list_display = ('sheet_name', 'sheet_url', 'is_active', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('sheet_name', 'sheet_url')
    ordering = ('-updated_at',)

@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    list_display = ('sync_date', 'sheet_config', 'status', 'records_imported', 'triggered_by')
    list_filter = ('status', 'sync_date', 'sheet_config')
    search_fields = ('triggered_by', 'errors')
    ordering = ('-sync_date',)
    readonly_fields = ('sync_date', 'sheet_config', 'status', 'records_imported', 'errors', 'triggered_by')
