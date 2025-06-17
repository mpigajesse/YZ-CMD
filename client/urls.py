from django.urls import path
from . import views

app_name = 'client'

urlpatterns = [
    path('liste/', views.liste_clients, name='liste'),
    path('creer/', views.creer_client, name='creer'),
    path('<int:pk>/detail/', views.detail_client, name='detail'),
    path('<int:pk>/modifier/', views.modifier_client, name='modifier'),
    path('<int:pk>/supprimer/', views.supprimer_client, name='supprimer'),
    path('supprimer-masse/', views.supprimer_clients_masse, name='supprimer_clients_masse'),
] 