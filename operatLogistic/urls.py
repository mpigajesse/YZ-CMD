from django.urls import path
from . import views

app_name = 'operatLogistic'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('home/', views.dashboard, name='dashboard'),
    path('commandes/', views.liste_commandes, name='liste_commandes'),
    path('commande/<int:commande_id>/', views.detail_commande, name='detail_commande'),
    path('repartition/', views.repartition, name='repartition'),
    path('repartition/region/<str:nom_region>/', views.details_region, name='details_region'),
    path('parametre/', views.parametre, name='parametre'),
    path('creer-operateur/', views.creer_operateur_logistique, name='creer_operateur'),
    path('profile/', views.profile_logistique, name='profile'),
    path('profile/modifier/', views.modifier_profile_logistique, name='modifier_profile'),
    path('profile/changer-mot-de-passe/', views.changer_mot_de_passe_logistique, name='changer_mot_de_passe'),
    path('commande/<int:commande_id>/livrer/', views.marquer_livree, name='marquer_livree'),
    path('commande/<int:commande_id>/probleme/', views.signaler_probleme, name='signaler_probleme'),
    # URLs d'exportation
    path('export/toutes-regions/excel/', views.export_all_regions_excel, name='export_all_regions_excel'),
    path('export/toutes-regions/csv/', views.export_all_regions_csv, name='export_all_regions_csv'),
    path('export/region/<str:nom_region>/excel/', views.export_region_excel, name='export_region_excel'),
    path('export/region/<str:nom_region>/csv/', views.export_region_csv, name='export_region_csv'),
] 
