from django.urls import path
from . import views

app_name = 'article'
 
urlpatterns = [
    # Pages principales
    path('', views.liste_articles, name='liste'),
    path('detail/<int:id>/', views.detail_article, name='detail'),
    path('modifier/<int:id>/', views.modifier_article, name='modifier'),
    path('creer/', views.creer_article, name='creer_article'),
    path('supprimer/<int:id>/', views.supprimer_article, name='supprimer_article'),
    path('supprimer-masse/', views.supprimer_articles_masse, name='supprimer_articles_masse'),
    
    # Filtres par catégorie
    path('categorie/<str:categorie>/', views.articles_par_categorie, name='categorie'),
    
    # Gestion du stock
    path('stock-faible/', views.stock_faible, name='stock_faible'),
    path('rupture-stock/', views.rupture_stock, name='rupture_stock'),
    
    # Gestion des promotions
    path('promotions/', views.liste_promotions, name='liste_promotions'),
    path('promotions/detail/<int:id>/', views.detail_promotion, name='detail_promotion'),
    path('promotions/creer/', views.creer_promotion, name='creer_promotion'),
    path('promotions/modifier/<int:id>/', views.modifier_promotion, name='modifier_promotion'),
    path('promotions/supprimer/<int:id>/', views.supprimer_promotion, name='supprimer_promotion'),
    path('promotions/activer-desactiver/<int:id>/', views.activer_desactiver_promotion, name='activer_desactiver_promotion'),
] 