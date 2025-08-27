from django.urls import path
from . import views
from .service_apres_vente import views as sav_views
from .barre_recherche_globale import views as search_views

app_name = 'operatLogistic'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('home/', views.dashboard, name='dashboard'),
    path('commandes/', views.liste_commandes, name='liste_commandes'),
    path('commande/<int:commande_id>/', views.detail_commande, name='detail_commande'),

    path('parametre/', views.parametre, name='parametre'),
    path('profile/', views.profile_logistique, name='profile'),
    path('profile/modifier/', views.modifier_profile_logistique, name='modifier_profile'),
    path('commande/<int:commande_id>/livrer/', views.marquer_livree, name='marquer_livree'),
    path('commande/<int:commande_id>/probleme/', views.signaler_probleme, name='signaler_probleme'),

    # URL pour le SAV
    path('commande/<int:commande_id>/changer-etat-sav/', views.changer_etat_sav, name='changer_etat_sav'),
    
    # URLs pour les nouvelles fonctionnalités
    path('commande/<int:commande_id>/creer-envoi/', views.creer_envoi, name='creer_envoi'),
    path('commande/<int:commande_id>/rafraichir-articles/', views.rafraichir_articles, name='rafraichir_articles'),
    path('commande/<int:commande_id>/creer-commande-sav/', views.creer_commande_sav, name='creer_commande_sav'),
    
    # URLs pour les opérations sur les articles
    path('commande/<int:commande_id>/ajouter-article/', views.ajouter_article, name='ajouter_article'),
    path('commande/<int:commande_id>/modifier-quantite/', views.modifier_quantite_article, name='modifier_quantite_article'),
    path('commande/<int:commande_id>/supprimer-article/', views.supprimer_article, name='supprimer_article'),
    
    # URL pour renvoyer en préparation
    path('commande/<int:commande_id>/renvoyer-preparation/', views.renvoyer_en_preparation, name='renvoyer_preparation'),
    
    # URL pour la livraison partielle
    path('commande/<int:commande_id>/livraison-partielle/', views.livraison_partielle, name='livraison_partielle'),
    
    # URL pour voir les commandes renvoyées en préparation
    path('commandes-renvoyees-preparation/', views.commandes_renvoyees_preparation, name='commandes_renvoyees_preparation'),
    
    # API pour les articles
    path('api/articles/', views.api_articles, name='api_articles'),
    path('api/commande/<int:commande_id>/panier/', views.api_panier_commande, name='api_panier_commande'),
    path('api/article/<int:article_id>/stock/', views.api_verifier_stock_article, name='api_verifier_stock_article'),

    
    # URLs pour les listes SAV
    path('sav/reportees/', sav_views.commandes_reportees, name='commandes_reportees'),
    path('sav/livrees-partiellement/', sav_views.commandes_livrees_partiellement, name='commandes_livrees_partiellement'),
    path('sav/avec-changement/', sav_views.commandes_livrees_avec_changement, name='commandes_livrees_avec_changement'),
    path('sav/retournees/', sav_views.commandes_retournees, name='commandes_retournees'),
    path('sav/livrees/', sav_views.commandes_livrees, name='commandes_livrees'),
    
    # URLs pour la recherche globale
    path('recherche-globale/', search_views.global_search_view, name='global_search'),
    path('recherche-globale/api/', search_views.global_search_api, name='global_search_api'),
    path('recherche-globale/suggestions/', search_views.search_suggestions_api, name='search_suggestions_api'),
] 
