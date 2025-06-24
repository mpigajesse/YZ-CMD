from django.urls import path
from . import views

app_name = 'Prepacommande'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home_redirect'),
    path('liste-prepa/', views.liste_prepa, name='liste_prepa'),
    path('profile/', views.profile_view, name='profile'),
    path('modifier-profile/', views.modifier_profile_view, name='modifier_profile'),
    path('changer-mot-de-passe/', views.changer_mot_de_passe_view, name='changer_mot_de_passe'),
    path('detail-prepa/<int:pk>/', views.detail_prepa, name='detail_prepa'),
    path('etiquettes/', views.etiquette_view, name='etiquette'),

    path('api/commande/<int:commande_id>/produits/', views.api_commande_produits, name='api_commande_produits'),
    path('api/commande/<int:commande_id>/changer-etat-preparation/', views.api_changer_etat_preparation, name='api_changer_etat_preparation'),
] 