from django.urls import path
from . import views

app_name = 'kpis'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    
    # APIs pour données KPIs
    path('api/ventes/', views.ventes_data, name='ventes_data'),
    path('api/evolution-ca/', views.evolution_ca_data, name='evolution_ca_data'),
    path('api/top-modeles/', views.top_modeles_data, name='top_modeles_data'),
    path('api/performance-regions/', views.performance_regions_data, name='performance_regions_data'),
    path('api/clients/', views.clients_data, name='clients_data'),
    path('api/vue-quantitative/', views.vue_quantitative_data, name='vue_quantitative_data'),
    path('performance-operateurs-data/', views.performance_operateurs_data, name='performance_operateurs_data'),
    path('operator-history/', views.operator_history_data, name='operator_history_data'),
    path('api/operator-realtime-times/', views.operator_realtime_times_data, name='operator_realtime_times_data'),
    path('export/performance-operateurs/csv/', views.export_performance_operateurs_csv, name='export_performance_operateurs_csv'),
    path('export/performance-operateurs/excel/', views.export_performance_operateurs_excel, name='export_performance_operateurs_excel'),
    path('export/etat-commandes/csv/', views.export_etat_commandes_csv, name='export_etat_commandes_csv'),
    path('export/etat-commandes/excel/', views.export_etat_commandes_excel, name='export_etat_commandes_excel'),
]
