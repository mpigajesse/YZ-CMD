from django.urls import path
from . import views

app_name = 'kpis'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard_home, name='dashboard'),
    
    # APIs pour données KPIs
    path('api/vue-generale/', views.vue_generale_data, name='vue_generale_data'),
    path('api/ventes/', views.ventes_data, name='ventes_data'),
    path('api/evolution-ca/', views.evolution_ca_data, name='evolution_ca_data'),
    path('api/top-modeles/', views.top_modeles_data, name='top_modeles_data'),
]
