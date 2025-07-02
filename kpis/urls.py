from django.urls import path
from . import views

app_name = 'kpis'

urlpatterns = [# Documentation
    path('documentation/', views.documentation, name='documentation'),
    
    # Présentation des paramètres
    path('presentation-parametres/', views.presentation_parametres, name='presentation_parametres'),
    
    # Configuration des paramètres KPIs
    path('configurations/', views.configurations, name='configurations'),
      # APIs pour données KPIs
    path('api/vue-generale/', views.vue_generale_data, name='vue_generale_data'),
    path('api/ventes/', views.ventes_data, name='ventes_data'),
    path('api/evolution-ca/', views.evolution_ca_data, name='evolution_ca_data'),
    path('api/top-modeles/', views.top_modeles_data, name='top_modeles_data'),
    path('api/performance-regions/', views.performance_regions_data, name='performance_regions_data'),
    path('api/clients/', views.clients_data, name='clients_data'),
    path('api/vue-quantitative/', views.vue_quantitative_data, name='vue_quantitative_data'),
    
    # APIs pour configuration
    path('api/configurations/', views.get_configurations, name='get_configurations'),
    path('api/configurations/save/', views.save_configurations, name='save_configurations'),
    path('api/configurations/reset/', views.reset_configurations, name='reset_configurations'),
]
