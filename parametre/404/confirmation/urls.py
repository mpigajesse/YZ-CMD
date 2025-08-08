from django.urls import path
from . import views

app_name = 'confirmation_404'

urlpatterns = [
    path('404/', views.custom_404_confirmation, name='404'),
]
