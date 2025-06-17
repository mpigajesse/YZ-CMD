from django.urls import path
from . import views

app_name = 'synchronisation'

urlpatterns = [
    path('dashboard/', views.sync_dashboard, name='dashboard'),
    path('sync-now/<int:config_id>/', views.sync_now, name='sync_now'),
    path('configs/', views.config_list, name='config_list'),
    path('configs/create/', views.config_create, name='config_create'),
    path('configs/edit/<int:pk>/', views.config_edit, name='config_edit'),
    path('configs/delete/<int:pk>/', views.config_delete, name='config_delete'),
    path('configs/delete-bulk/', views.delete_configs_bulk, name='delete_configs_bulk'),
    path('configs/test/<int:config_id>/', views.test_connection, name='test_connection'),
    path('logs/', views.sync_logs, name='logs'),
    path('logs/<int:log_id>/', views.sync_log_detail, name='log_detail'),
    path('logs/delete/<int:log_id>/', views.log_delete, name='log_delete'),
    path('logs/delete-bulk/', views.delete_logs_bulk, name='delete_logs_bulk'),
]
