from django.urls import path
from . import views
from .barre_recherche_globale import views as search_views

app_name = 'operatConfirme'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('home/', views.dashboard, name='dashboard'),
    path('commandes/', views.liste_commandes, name='liste_commandes'),
    path('commandes/creer/', views.creer_commande, name='creer_commande'),
    path('confirmation/', views.confirmation, name='confirmation'),
    path('mes-commandes-confirmees/', views.commandes_confirmees, name='commandes_confirmees'),
    path('commandes/<int:commande_id>/', views.detail_commande, name='detail_commande'),
    path('commandes/<int:commande_id>/confirmer/', views.confirmer_commande, name='confirmer_commande'),
    path('commandes/<int:commande_id>/confirmer-ajax/', views.confirmer_commande_ajax, name='confirmer_commande_ajax'),
    path('confirmer-commandes-ajax/', views.confirmer_commandes_ajax, name='confirmer_commandes_ajax'),
    path('commandes/<int:commande_id>/erronnee/', views.marquer_erronnee, name='marquer_erronnee'),
    path('lancer-confirmations/', views.lancer_confirmations, name='lancer_confirmations'),
    path('parametre/', views.parametre, name='parametre'),
    path('creer-operateur/', views.creer_operateur_confirme, name='creer_operateur'),
    path('profile/', views.profile_confirme, name='profile'),
    path('profile/modifier/', views.modifier_profile_confirme, name='modifier_profile'),
    path('profile/changer-mot-de-passe/', views.changer_mot_de_passe_confirme, name='changer_mot_de_passe'),
    path('commandes/<int:commande_id>/lancer-confirmation/', views.lancer_confirmation, name='lancer_confirmation'),
    path('commandes/<int:commande_id>/annuler-commande/', views.annuler_commande_confirmation, name='annuler_commande_confirmation'),
    path('lancer-confirmations-masse/', views.lancer_confirmations_masse, name='lancer_confirmations_masse'),
    path('selectionner-operation/', views.selectionner_operation, name='selectionner_operation'),
    path('commandes/<int:commande_id>/modifier/', views.modifier_commande, name='modifier_commande'),
    path('api/articles-disponibles/', views.api_articles_disponibles, name='api_articles_disponibles'),
    path('api/commentaires-disponibles/', views.api_commentaires_disponibles, name='api_commentaires_disponibles'),
    path('api/commandes/<int:commande_id>/operations/', views.api_operations_commande, name='api_operations_commande'),
    path('api/commande/<int:commande_id>/panier/', views.api_panier_commande, name='api_panier_commande'),
    path('commandes/<int:commande_id>/diagnostiquer-compteur/', views.diagnostiquer_compteur_commande, name='diagnostiquer_compteur'),
    path('api/commande/<int:commande_id>/rafraichir-articles/', views.rafraichir_articles_section, name='api_rafraichir_articles'),
    path('api/recherche-client-tel/', views.api_recherche_client_tel, name='api_recherche_client_tel'),
    path('api/recherche-article-ref/', views.api_recherche_article_ref, name='api_recherche_article_ref'),
    path('get-article-variants/<int:article_id>/', views.get_article_variants, name='get_article_variants'),
    
    # URLs pour la recherche globale
    path('recherche-globale/', search_views.global_search_view, name='global_search'),
    path('recherche-globale/api/', search_views.global_search_api, name='global_search_api'),
    path('recherche-globale/suggestions/', search_views.search_suggestions_api, name='search_suggestions_api'),
    
    # Notifications supprimées
] 