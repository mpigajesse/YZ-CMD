from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from .models import GoogleSheetConfig, SyncLog
from .google_sheet_sync import GoogleSheetSync
from django.utils import timezone
from .forms import GoogleSheetConfigForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

def is_admin(user):
    """Vérifie si l'utilisateur est un administrateur"""
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin)
def sync_dashboard(request):
    """Tableau de bord de synchronisation pour l'administrateur"""
    configs = GoogleSheetConfig.objects.filter(is_active=True)
    recent_logs = SyncLog.objects.all().order_by('-sync_date')[:10]
    nb_erreurs = SyncLog.objects.filter(status='error').order_by('-sync_date')[:10].count()
    
    context = {
        'configs': configs,
        'recent_logs': recent_logs,
        'nb_erreurs': nb_erreurs,
    }
    return render(request, 'synchronisation/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def sync_now(request, config_id):
    """Déclenche une synchronisation manuelle"""
    config = get_object_or_404(GoogleSheetConfig, pk=config_id, is_active=True)
    
    # Créer une instance de synchronisation et l'exécuter
    syncer = GoogleSheetSync(config, triggered_by=request.user.username)
    success = syncer.sync()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Réponse AJAX
        return JsonResponse({
            'success': success,
            'records_imported': syncer.records_imported,
            'errors': syncer.errors,
            'timestamp': timezone.now().strftime('%d/%m/%Y %H:%M:%S')
        })
    else:
        # Réponse normale avec redirection
        if success:
            messages.success(
                request, 
                f"Synchronisation réussie. {syncer.records_imported} enregistrements importés."
            )
        else:
            messages.error(
                request, 
                f"Erreur lors de la synchronisation. Consultez les logs pour plus de détails."
            )
        return redirect('synchronisation:dashboard')

@login_required
def config_list(request):
    """Liste des configurations de synchronisation"""
    # Récupérer les paramètres de filtrage
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    # Récupérer toutes les configurations
    configs = GoogleSheetConfig.objects.all().order_by('-created_at')
    
    # Calculer les statistiques
    total_configs = configs.count()
    active_count = configs.filter(is_active=True).count()
    inactive_count = configs.filter(is_active=False).count()
    
    # Appliquer les filtres
    if search_query:
        configs = configs.filter(
            models.Q(sheet_name__icontains=search_query) |
            models.Q(sheet_url__icontains=search_query)
        )
    
    if status_filter == 'active':
        configs = configs.filter(is_active=True)
    elif status_filter == 'inactive':
        configs = configs.filter(is_active=False)
    
    context = {
        'configs': configs,
        'search_query': search_query,
        'status_filter': status_filter,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'total_configs': total_configs,
    }
    return render(request, 'synchronisation/config_list.html', context)

@login_required
def config_create(request):
    """Création d'une nouvelle configuration"""
    if request.method == 'POST':
        form = GoogleSheetConfigForm(request.POST)
        if form.is_valid():
            config = form.save()
            messages.success(request, "Configuration créée avec succès.")
            return redirect('synchronisation:config_list')
    else:
        form = GoogleSheetConfigForm()
    
    return render(request, 'synchronisation/config_form.html', {'form': form, 'action': 'Créer'})

@login_required
def config_edit(request, pk):
    """Modification d'une configuration"""
    config = get_object_or_404(GoogleSheetConfig, pk=pk)
    
    if request.method == 'POST':
        form = GoogleSheetConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Configuration mise à jour avec succès.")
            return redirect('synchronisation:config_list')
    else:
        form = GoogleSheetConfigForm(instance=config)
    
    return render(request, 'synchronisation/config_form.html', {'form': form, 'action': 'Modifier'})

@login_required
def config_delete(request, pk):
    """Suppression d'une configuration"""
    config = get_object_or_404(GoogleSheetConfig, pk=pk)
    
    if request.method == 'POST':
        config.delete()
        messages.success(request, "Configuration supprimée avec succès.")
        return redirect('synchronisation:config_list')
    
    return render(request, 'synchronisation/config_confirm_delete.html', {'config': config})

@login_required
def sync_logs(request):
    """Affichage des logs de synchronisation"""
    # Récupérer les paramètres de filtrage
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    # Récupérer tous les logs, triés par date décroissante
    logs = SyncLog.objects.all().order_by('-sync_date')
    
    # Calculer les statistiques
    total_logs = logs.count()
    success_count = logs.filter(status='success').count()
    error_count = logs.filter(status='error').count()
    pending_count = logs.filter(status='pending').count()
    
    # Appliquer les filtres
    if search_query:
        logs = logs.filter(
            models.Q(sheet_config__sheet_name__icontains=search_query) |
            models.Q(triggered_by__icontains=search_query) |
            models.Q(errors__icontains=search_query)
        )
    
    if status_filter:
        logs = logs.filter(status=status_filter)
    
    if date_filter:
        from datetime import datetime
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            logs = logs.filter(sync_date__date=filter_date)
        except ValueError:
            pass  # Ignorer les dates invalides
    
    # Pagination
    paginator = Paginator(logs, 15)  # 15 logs par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'logs': logs,  # Pour les statistiques
        'search_query': search_query,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'success_count': success_count,
        'error_count': error_count,
        'pending_count': pending_count,
        'total_logs': total_logs,
    }
    return render(request, 'synchronisation/sync_logs.html', context)

@login_required
@user_passes_test(is_admin)
def sync_log_detail(request, log_id):
    """Détail d'un log de synchronisation"""
    log = get_object_or_404(SyncLog, pk=log_id)
    return render(request, 'synchronisation/log_detail.html', {'log': log})

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def delete_configs_bulk(request):
    """Suppression en masse des configurations"""
    if request.method != 'POST':
        messages.error(request, "Méthode non autorisée.")
        return redirect('synchronisation:config_list')
    
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucune configuration sélectionnée pour la suppression.")
        return redirect('synchronisation:config_list')

    try:
        count = GoogleSheetConfig.objects.filter(pk__in=selected_ids).delete()[0]
        messages.success(request, f"{count} configuration(s) supprimée(s) avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('synchronisation:config_list')

@require_POST
@login_required
@user_passes_test(is_admin)
@csrf_exempt
def delete_logs_bulk(request):
    """Suppression en masse des logs"""
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucun log sélectionné pour la suppression.")
        return redirect('synchronisation:logs')

    try:
        count = SyncLog.objects.filter(pk__in=selected_ids).delete()[0]
        messages.success(request, f"{count} log(s) supprimé(s) avec succès.")
    except Exception as e:
        logger.error(f"Une erreur est survenue lors de la suppression en masse : {e}")
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('synchronisation:logs')

@csrf_exempt
@login_required
@user_passes_test(is_admin)
def log_delete(request, log_id):
    """Suppression individuelle d'un log"""
    log = get_object_or_404(SyncLog, pk=log_id)
    
    if request.method == 'POST':
        log.delete()
        messages.success(request, "Log supprimé avec succès.")
        return redirect('synchronisation:logs')
    
    return redirect('synchronisation:logs')

@login_required
@user_passes_test(is_admin)
def test_connection(request, config_id):
    """Test de connexion à Google Sheets"""
    config = get_object_or_404(GoogleSheetConfig, pk=config_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Si c'est une requête POST avec des données JSON (depuis le formulaire), les utiliser
            if request.method == 'POST' and request.content_type == 'application/json':
                import json
                data = json.loads(request.body)
                test_url = data.get('sheet_url', config.sheet_url)
                test_sheet_name = data.get('sheet_name', config.sheet_name)
            else:
                # Utiliser les données de la configuration existante
                test_url = config.sheet_url
                test_sheet_name = config.sheet_name
            
            # Créer une configuration temporaire pour le test
            temp_config = GoogleSheetConfig(
                sheet_url=test_url,
                sheet_name=test_sheet_name
            )
            
            # Créer une instance de synchronisation pour tester
            syncer = GoogleSheetSync(temp_config, triggered_by=request.user.username)
            
            # Tester l'authentification
            client = syncer.authenticate()
            if not client:
                return JsonResponse({
                    'success': False,
                    'error': 'Erreur d\'authentification avec l\'API Google Sheets.',
                    'details': syncer.errors
                })
            
            # Tester l'ouverture de la feuille
            try:
                spreadsheet = client.open_by_url(test_url)
                worksheet = spreadsheet.worksheet(test_sheet_name)
                
                # Récupérer quelques informations sur la feuille
                all_values = worksheet.get_all_values()
                total_rows = len(all_values)
                headers = all_values[0] if all_values else []
                
                return JsonResponse({
                    'success': True,
                    'message': f'Connexion réussie !',
                    'details': {
                        'spreadsheet_title': spreadsheet.title,
                        'worksheet_name': worksheet.title,
                        'total_rows': total_rows,
                        'total_columns': len(headers),
                        'headers': headers[:5] if headers else [],  # Premiers 5 en-têtes
                        'has_data': total_rows > 1
                    }
                })
                
            except Exception as sheet_error:
                return JsonResponse({
                    'success': False,
                    'error': f'Erreur d\'accès à la feuille "{test_sheet_name}"',
                    'details': [
                        str(sheet_error),
                        'Vérifiez que le nom de la feuille est correct',
                        'Vérifiez que la feuille Google Sheets est partagée publiquement'
                    ]
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Erreur lors du test de connexion',
                'details': [str(e)]
            })
    
    # Si ce n'est pas une requête AJAX, rediriger
    return redirect('synchronisation:config_edit', pk=config_id)
