from django.urls import path
from . import views
from .service_apres_vente import views as sav_views
from .stock import views as stock_views

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
    # URLs d'exportation
    path('export/toutes-regions/excel/', views.export_all_regions_excel, name='export_all_regions_excel'),
    path('export/toutes-regions/csv/', views.export_all_regions_csv, name='export_all_regions_csv'),
    path('export/region/<str:nom_region>/excel/', views.export_region_excel, name='export_region_excel'),
    path('export/region/<str:nom_region>/csv/', views.export_region_csv, name='export_region_csv'),
    # URL pour le SAV
    path('commande/<int:commande_id>/changer-etat-sav/', sav_views.changer_etat_livraison, name='changer_etat_sav'),
    # URLs pour les listes SAV
    path('sav/reportees/', sav_views.commandes_reportees, name='commandes_reportees'),
    path('sav/livrees-partiellement/', sav_views.commandes_livrees_partiellement, name='commandes_livrees_partiellement'),
    path('sav/avec-changement/', sav_views.commandes_livrees_avec_changement, name='commandes_livrees_avec_changement'),
    path('sav/annulees/', sav_views.commandes_annulees_sav, name='commandes_annulees_sav'),
    path('sav/commandes-annulees/', sav_views.commandes_annulees_sav, name='commandes_annulees_sav'),
    path('sav/livrees/', sav_views.commandes_livrees, name='commandes_livrees'),
    # Nouvelles URLs pour la gestion de stock
    path('stock/articles/', stock_views.liste_articles, name='stock_articles'),
    path('stock/article/creer/', stock_views.creer_article, name='creer_article'),
    path('stock/article/<int:article_id>/', stock_views.detail_article, name='detail_article'),
    path('stock/article/modifier/<int:article_id>/', stock_views.modifier_article, name='modifier_article'),
    path('stock/articles/ajuster/<int:article_id>/', stock_views.ajuster_stock, name='ajuster_stock'),
    path('stock/mouvements/', stock_views.mouvements_stock, name='stock_mouvements'),
    path('stock/alertes/', stock_views.alertes_stock, name='stock_alertes'),
    path('stock/statistiques/', stock_views.statistiques_stock, name='stock_statistiques'),
    path('stock/statistiques/export/', stock_views.export_statistiques_stock, name='export_statistiques_stock'),
] 
