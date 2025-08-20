from django.urls import path
from . import views 

app_name = 'Superpreparation'


urlpatterns = [
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home_redirect'),

     #Gestion des commandes 
    path('liste-prepa/', views.liste_prepa, name='liste_prepa'),
    path('commandes-a-imprimer/', views.commandes_a_imprimer, name='commandes_a_imprimer'),
    path('commandes-en-preparation/', views.commandes_en_preparation, name='commandes_en_preparation'),


   
    path('commandes-confirmees/', views.commandes_confirmees, name='commandes_confirmees'),
     path('livrees-partiellement/', views.commandes_livrees_partiellement, name='commandes_livrees_partiellement'),
    path('retournees/', views.commandes_retournees, name='commandes_retournees'),
    path('profile/', views.profile_view, name='profile'),
    path('modifier-profile/', views.modifier_profile_view, name='modifier_profile'),
    path('changer-mot-de-passe/', views.changer_mot_de_passe_view, name='changer_mot_de_passe'),
    path('detail-prepa/<int:pk>/', views.detail_prepa, name='detail_prepa'),
    path('etiquettes/', views.etiquette_view, name='etiquette'),
    # Impression supprimée (gérée par Gestion des étiquettes)
    path('modifier-commande/<int:commande_id>/', views.modifier_commande_prepa, name='modifier_commande'),

    path('api/commande/<int:commande_id>/produits/', views.api_commande_produits, name='api_commande_produits'),
    # path('api/commande/<int:commande_id>/changer-etat/', views.api_changer_etat_preparation, name='api_changer_etat_preparation'), # Supprimée - plus nécessaire
    path('api/articles-disponibles-prepa/', views.api_articles_disponibles_prepa, name='api_articles_disponibles_prepa'),
    path('api/commande/<int:commande_id>/panier/', views.api_panier_commande_prepa, name='api_panier_commande'),
    path('api/commande/<int:commande_id>/panier-livraison/', views.api_panier_commande_livraison, name='api_panier_commande_livraison'),
    path('api/commande/<int:commande_id>/articles-livree-partiellement/', views.api_articles_commande_livree_partiellement, name='api_articles_commande_livree_partiellement'),
    path('api/traiter-commande-retournee/<int:commande_id>/', views.traiter_commande_retournee_api, name='traiter_commande_retournee_api'),


    # URLs pour la gestion des articles pendant la préparation
    path('commande/<int:commande_id>/rafraichir-articles/', views.rafraichir_articles_commande_prepa, name='rafraichir_articles_commande_prepa'),
    path('commande/<int:commande_id>/ajouter-article/', views.ajouter_article_commande_prepa, name='ajouter_article_commande_prepa'),
    path('commande/<int:commande_id>/modifier-quantite/', views.modifier_quantite_article_prepa, name='modifier_quantite_article_prepa'),
    path('commande/<int:commande_id>/supprimer-article/', views.supprimer_article_commande_prepa, name='supprimer_article_commande_prepa'),
    path('commande/<int:commande_id>/prix-upsell/', views.api_prix_upsell_articles, name='api_prix_upsell_articles'),

    # URLs pour la gestion de stock
    path('stock/articles/', views.liste_articles, name='liste_articles'),
    path('stock/article/creer/', views.creer_article, name='creer_article'),
    path('stock/article/<int:article_id>/', views.detail_article, name='detail_article'),
    path('stock/article/<int:article_id>/modifier/', views.modifier_article, name='modifier_article'),
    path('stock/article/<int:article_id>/ajuster/', views.ajuster_stock, name='ajuster_stock'),
    path('stock/mouvements/', views.mouvements_stock, name='mouvements_stock'),
    path('stock/alertes/', views.alertes_stock, name='alertes_stock'),
    path('stock/statistiques/', views.statistiques_stock, name='statistiques_stock'),
    
    # === URLs SUPPRIMÉES : RÉPARTITION AUTOMATIQUE (DÉPLACÉES VERS ADMIN) ===
    # path('repartition-automatique/', views.repartition_automatique, name='repartition_automatique'),
    # path('repartition-commandes/', views.repartition_commandes, name='repartition_commandes'),
    # path('details-region/', views.details_region_view, name='details_region'),
    
    # === NOUVELLES URLs : EXPORTS CONSOLIDÉS ===
    path('export/region/<str:region_name>/csv/', views.export_region_consolidee_csv, name='export_region_consolidee_csv'),
    path('export/region/<str:region_name>/excel/', views.export_region_consolidee_excel, name='export_region_consolidee_excel'),
    path('export/ville/<int:ville_id>/csv/', views.export_ville_consolidee_csv, name='export_ville_consolidee_csv'),
    path('export/ville/<int:ville_id>/excel/', views.export_ville_consolidee_excel, name='export_ville_consolidee_excel'),



   

]
