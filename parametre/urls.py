from django.urls import path
from . import views
from .dashboard_360 import views as views_360
from .dashboard_360.barre_recherche_globale import views as global_search_views

app_name = 'app_admin'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('operateurs/', views.liste_operateurs, name='liste_operateurs'),
    path('operateurs/ajax/', views.liste_operateurs_ajax, name='liste_operateurs_ajax'),
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
    
    # URLs Service Après-Vente pour Admin
    path('sav/commandes-retournees/', views.sav_commandes_retournees, name='sav_commandes_retournees'),
    path('sav/commandes-reportees/', views.sav_commandes_reportees, name='sav_commandes_reportees'),
    path('sav/livrees-partiellement/', views.sav_livrees_partiellement, name='sav_livrees_partiellement'),
    path('sav/annulees/', views.sav_annulees_sav, name='sav_annulees'),
    path('sav/livrees-avec-changement/', views.sav_livrees_avec_changement, name='sav_livrees_avec_changement'),
    path('sav/livrees/', views.sav_livrees, name='sav_livrees'),
    path('sav/creer-nouvelle-commande/<int:commande_id>/', views.sav_creer_nouvelle_commande, name='sav_creer_nouvelle_commande'),
    path('sav/renvoyer-preparation/<int:commande_id>/', views.sav_renvoyer_preparation, name='sav_renvoyer_preparation'),
    
    # URLs Dashboard 360
    path('vue360/', views_360.page_360, name='page_360'),
    path('export-csv/', views_360.export_all_data_csv, name='export_all_data_csv'),
    path('export-excel/', views_360.export_all_data_excel, name='export_all_data_excel'),
    
    # URLs Répartition
    path('repartition/automatique/', views.repartition_automatique, name='repartition_automatique'),
    path('repartition/details-region/', views.details_region_view, name='details_region'),
    path('repartition/get-modal-data-ajax/', views.get_modal_data_ajax, name='get_modal_data_ajax'),
    
    # URLs API Temps Réel Vue 360
    path('vue360/api/realtime-data/', views_360.vue_360_realtime_data, name='vue_360_realtime_data'),
    path('vue360/api/statistics-update/', views_360.vue_360_statistics_update, name='vue_360_statistics_update'),
    path('vue360/api/etats-tracking/', views_360.vue_360_etats_tracking, name='vue_360_etats_tracking'),
    path('vue360/api/panier-tracking/', views_360.vue_360_panier_tracking, name='vue_360_panier_tracking'),
    
    # URLs Barre de Recherche Globale
    path('global-search/', global_search_views.global_search_view, name='global_search'),
    path('global-search/api/', global_search_views.global_search_api, name='global_search_api'),
    path('global-search/suggestions/', global_search_views.search_suggestions_api, name='search_suggestions_api'),
    
    # URLs Gestion des Couleurs et Pointures
    path('gestion-articles/couleurs-pointures/', views.gestion_couleurs_pointures, name='gestion_couleurs_pointures'),
    path('gestion-articles/couleurs/creer/', views.creer_couleur, name='creer_couleur'),
    path('gestion-articles/couleurs/modifier/<int:couleur_id>/', views.modifier_couleur, name='modifier_couleur'),
    path('gestion-articles/couleurs/supprimer/<int:couleur_id>/', views.supprimer_couleur, name='supprimer_couleur'),
    path('gestion-articles/pointures/creer/', views.creer_pointure, name='creer_pointure'),
    path('gestion-articles/pointures/modifier/<int:pointure_id>/', views.modifier_pointure, name='modifier_pointure'),
    path('gestion-articles/pointures/supprimer/<int:pointure_id>/', views.supprimer_pointure, name='supprimer_pointure'),
] 