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
] 