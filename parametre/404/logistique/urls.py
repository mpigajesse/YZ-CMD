from django.urls import path
from . import views

app_name = 'logistique_404'

urlpatterns = [
    path('404/', views.custom_404_logistique, name='404'),
]
