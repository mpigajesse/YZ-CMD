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
    
    # URLs Répartition des Commandes (déplacées depuis Prepacommande)
    path('repartition/automatique/', views.repartition_automatique, name='repartition_automatique'),
    path('repartition/details-region/', views.details_region_view, name='details_region'),
    path('repartition/modal-data/', views.get_modal_data_ajax, name='get_modal_data_ajax'),
    
    # URLs Service Après-Vente pour Admin
    path('sav/commandes-retournees/', views.sav_commandes_retournees, name='sav_commandes_retournees'),
    path('sav/commandes-reportees/', views.sav_commandes_reportees, name='sav_commandes_reportees'),
    path('sav/livrees-partiellement/', views.sav_livrees_partiellement, name='sav_livrees_partiellement'),
    path('sav/annulees/', views.sav_annulees_sav, name='sav_annulees'),
    path('sav/livrees-avec-changement/', views.sav_livrees_avec_changement, name='sav_livrees_avec_changement'),
    path('sav/livrees/', views.sav_livrees, name='sav_livrees'),
    path('sav/creer-nouvelle-commande/<int:commande_id>/', views.sav_creer_nouvelle_commande, name='sav_creer_nouvelle_commande'),
    path('sav/renvoyer-preparation/<int:commande_id>/', views.sav_renvoyer_preparation, name='sav_renvoyer_preparation'),
    
    # URLs API Recherche SAV
    path('sav/search/api/', views.sav_search_api, name='sav_search_api'),
    
    # URLs Dashboard 360
    path('vue360/', views_360.page_360, name='page_360'),
    path('export-csv/', views_360.export_all_data_csv, name='export_all_data_csv'),
    path('export-excel/', views_360.export_all_data_excel, name='export_all_data_excel'),
    
    # URLs API Temps Réel Vue 360
    path('vue360/api/realtime-data/', views_360.vue_360_realtime_data, name='vue_360_realtime_data'),
    path('vue360/api/statistics-update/', views_360.vue_360_statistics_update, name='vue_360_statistics_update'),
    path('vue360/api/etats-tracking/', views_360.vue_360_etats_tracking, name='vue_360_etats_tracking'),
    path('vue360/api/panier-tracking/', views_360.vue_360_panier_tracking, name='vue_360_panier_tracking'),
    

    
    # URLs Barre de Recherche Globale
    path('recherche-globale/', views.global_search_view, name='global_search'),
    path('recherche-globale/api/', views.global_search_api, name='global_search_api'),
    path('recherche-globale/suggestions/', views.search_suggestions_api, name='search_suggestions_api'),
] 