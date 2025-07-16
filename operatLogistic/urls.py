from django.urls import path
from . import views
from .service_apres_vente import views as sav_views

app_name = 'operatLogistic'

urlpatterns = [
    path('', views.dashboard, name='home'),
    path('home/', views.dashboard, name='dashboard'),
    path('commandes/', views.liste_commandes, name='liste_commandes'),
    path('commande/<int:commande_id>/', views.detail_commande, name='detail_commande'),

    path('parametre/', views.parametre, name='parametre'),
    path('profile/', views.profile_logistique, name='profile'),
    path('profile/modifier/', views.modifier_profile_logistique, name='modifier_profile'),
    path('profile/changer-mot-de-passe/', views.changer_mot_de_passe_logistique, name='changer_mot_de_passe'),
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
    
    # API pour les articles
    path('api/articles/', views.api_articles, name='api_articles'),
    
    # URLs pour les listes SAV
    path('sav/reportees/', sav_views.commandes_reportees, name='commandes_reportees'),
    path('sav/livrees-partiellement/', sav_views.commandes_livrees_partiellement, name='commandes_livrees_partiellement'),
    path('sav/avec-changement/', sav_views.commandes_livrees_avec_changement, name='commandes_livrees_avec_changement'),
    path('sav/annulees/', sav_views.commandes_annulees_sav, name='commandes_annulees_sav'),
    path('sav/commandes-annulees/', sav_views.commandes_annulees_sav, name='commandes_annulees_sav'),
    path('sav/retournees/', sav_views.commandes_retournees, name='commandes_retournees'),
    path('sav/livrees/', sav_views.commandes_livrees, name='commandes_livrees'),
] 
