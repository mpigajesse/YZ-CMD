from django.urls import path
from . import views
from .dashboard_360 import views as views_360

app_name = 'app_admin'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('operateurs/', views.liste_operateurs, name='liste_operateurs'),
    path('operateurs/creer/', views.creer_operateur, name='creer_operateur'),
    path('operateurs/detail/<int:pk>/', views.detail_operateur, name='detail_operateur'),
    

    path('regions/', views.liste_regions, name='liste_regions'),
    path('regions/creer/', views.creer_region, name='creer_region'),
    path('regions/<int:region_id>/', views.detail_region, name='detail_region'),
    path('regions/modifier/<int:pk>/', views.modifier_region, name='modifier_region'),
    path('regions/supprimer/<int:pk>/', views.supprimer_region, name='supprimer_region'),
    path('regions/supprimer-masse/', views.supprimer_regions_masse, name='supprimer_regions_masse'),
    
    path('villes/', views.liste_villes, name='liste_villes'),
    path('villes/creer/', views.creer_ville, name='creer_ville'),
    path('villes/detail/<int:pk>/', views.detail_ville, name='detail_ville'),
    path('villes/modifier/<int:pk>/', views.modifier_ville, name='modifier_ville'),
    path('villes/supprimer/<int:pk>/', views.supprimer_ville, name='supprimer_ville'),
    path('villes/supprimer-masse/', views.supprimer_villes_masse, name='supprimer_villes_masse'),
    path('operateurs/modifier/<int:pk>/', views.modifier_operateur, name='modifier_operateur'),
    path('operateurs/supprimer/<int:pk>/', views.supprimer_operateur, name='supprimer_operateur'),
    path('operateurs/supprimer-masse/', views.supprimer_operateurs_masse, name='supprimer_operateurs_masse'),
    path('profile/', views.admin_profile, name='profile'),
    path('profile/modifier/', views.modifier_admin_profile, name='modifier_profile'),
    path('profile/changer-mot-de-passe/', views.changer_mot_de_passe_admin, name='changer_mot_de_passe'),
    
    # Gestion des mots de passe des opérateurs
    path('operateurs/mots-de-passe/', views.gestion_mots_de_passe, name='gestion_mots_de_passe'),
    path('operateurs/<int:pk>/modifier-mot-de-passe/', views.modifier_mot_de_passe_operateur, name='modifier_mot_de_passe_operateur'),
    
    # Vue 360
    path('vue360/', views_360.page_360, name='page_360'),
    path('export-csv/', views_360.export_all_data_csv, name='export_all_data_csv'),
    path('export-excel/', views_360.export_all_data_excel, name='export_all_data_excel'),
] 