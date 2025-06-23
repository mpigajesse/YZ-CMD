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
] 
