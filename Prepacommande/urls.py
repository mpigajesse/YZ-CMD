from django.urls import path
from . import views

app_name = 'Prepacommande'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home_redirect'),
    path('liste-prepa/', views.liste_prepa, name='liste_prepa'),
    path('a-imprimer/', views.commandes_a_imprimer, name='commandes_a_imprimer'),
    path('en-preparation/', views.commandes_en_preparation, name='commandes_en_preparation'),
    path('profile/', views.profile_view, name='profile'),
    path('modifier-profile/', views.modifier_profile_view, name='modifier_profile'),
    path('changer-mot-de-passe/', views.changer_mot_de_passe_view, name='changer_mot_de_passe'),
    path('detail-prepa/<int:pk>/', views.detail_prepa, name='detail_prepa'),
    path('etiquettes/', views.etiquette_view, name='etiquette'),
    path('impression-etiquettes/', views.impression_etiquettes_view, name='impression_etiquettes'),
    path('modifier-commande/<int:commande_id>/', views.modifier_commande_prepa, name='modifier_commande'),

    path('api/commande/<int:commande_id>/produits/', views.api_commande_produits, name='api_commande_produits'),
    path('api/commande/<int:commande_id>/changer-etat-preparation/', views.api_changer_etat_preparation, name='api_changer_etat_preparation'),
    path('api/articles-disponibles-prepa/', views.api_articles_disponibles_prepa, name='api_articles_disponibles_prepa'),
    path('api/commande/<int:commande_id>/panier/', views.api_panier_commande_prepa, name='api_panier_commande'),
] 