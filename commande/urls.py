from django.urls import path
from . import views

app_name = 'commande'
 
urlpatterns = [
    path('', views.liste_commandes, name='liste'),
    path('detail/<str:pk>/', views.detail_commande, name='detail'),
    path('creer/', views.creer_commande, name='creer'),
    path('modifier/<int:pk>/', views.modifier_commande, name='modifier'),

    path('etats/', views.gestion_etats, name='gestion_etats'),
    # URLs CRUD pour la gestion des états
    path('etats/ajouter/', views.ajouter_etat, name='ajouter_etat'),
    path('etats/modifier/<int:etat_id>/', views.modifier_etat, name='modifier_etat'),
    path('etats/supprimer/<int:etat_id>/', views.supprimer_etat, name='supprimer_etat'),
    path('etats/couleur/<int:etat_id>/', views.changer_couleur_etat, name='changer_couleur_etat'),
    path('etats/monter/<int:etat_id>/', views.monter_etat, name='monter_etat'),
    path('etats/descendre/<int:etat_id>/', views.descendre_etat, name='descendre_etat'),
    # URLs pour les pages de gestion par état
    path('non-affectees/', views.commandes_non_affectees, name='non_affectees'),
    path('affectees/', views.commandes_affectees, name='affectees'),
    path('a-traiter/', views.commandes_a_traiter, name='a_traiter'),
    path('annulees/', views.commandes_annulees, name='annulees'),
    path('confirmees/', views.commandes_confirmees, name='confirmees'),
    path('preparees/', views.commandes_preparees, name='preparees'),
    path('suivi-confirmations/', views.suivi_confirmations, name='suivi_confirmations'),
    path('suivi-preparations/', views.suivi_preparations, name='suivi_preparations'),
    path('affecter-preparation/<int:commande_id>/', views.affecter_preparation, name='affecter_preparation'),
    path('affecter-preparation-multiple/', views.affecter_preparation_multiple, name='affecter_preparation_multiple'),
    path('affecter-livraison/<int:commande_id>/', views.affecter_livraison, name='affecter_livraison'),
    path('affecter-livraison-multiple/', views.affecter_livraison_multiple, name='affecter_livraison_multiple'),
    # URLs pour l'affectation et changement de statut
    path('affecter/', views.affecter_commandes, name='affecter_commandes'),
    path('desaffecter/', views.desaffecter_commandes, name='desaffecter_commandes'),
    path('desaffecter/<int:commande_id>/', views.desaffecter_commande_unique, name='desaffecter_commande_unique'),
    path('changer-statut/', views.changer_statut_commandes, name='changer_statut_commandes'),
    path('changer-statut/<int:commande_id>/', views.changer_statut_commande_unique, name='changer_statut_commande_unique'),
    path('annuler/<int:pk>/', views.annuler_commande, name='annuler_commande'),
    path('statistiques-motifs/', views.statistiques_motifs_annulation, name='statistiques_motifs'),
    # Maintenance
    path('maintenance-etats/', views.nettoyer_etats_doublons, name='maintenance_etats'),
    # Paniers
    path('paniers/', views.liste_paniers, name='paniers'),
    # API
    path('api/commande/<int:commande_id>/panier/', views.api_panier_commande, name='api_panier_commande'),
]