from django.urls import path
from . import views

app_name = 'preparation_404'

urlpatterns = [
    path('404/', views.custom_404_preparation, name='404'),
]
