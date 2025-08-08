from django.urls import path
from . import views

app_name = 'admin_404'

urlpatterns = [
    path('404/', views.custom_404_admin, name='404'),
]
