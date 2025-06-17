from django.urls import path
from . import views

app_name = 'operatConfirme'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('home/', views.dashboard, name='dashboard'),
    path('commandes/', views.liste_commandes, name='liste_commandes'),
    path('parametre/', views.parametre, name='parametre'),
    path('creer-operateur/', views.creer_operateur_confirme, name='creer_operateur'),
    path('profile/', views.profile_confirme, name='profile'),
    path('profile/modifier/', views.modifier_profile_confirme, name='modifier_profile'),
    path('profile/changer-mot-de-passe/', views.changer_mot_de_passe_confirme, name='changer_mot_de_passe'),
] 