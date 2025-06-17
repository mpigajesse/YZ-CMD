from django.urls import path
from . import views

app_name = 'livraison'
 
urlpatterns = [
    path('', views.liste_livraisons, name='liste'),
    path('detail/<str:id>/', views.detail_livraison, name='detail'),
    path('creer/', views.creer_livraison, name='creer'),
] 