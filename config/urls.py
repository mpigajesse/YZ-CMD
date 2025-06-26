from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from .views import home_redirect, custom_logout
from . import views

urlpatterns = [
    # Redirection de la page d'accueil vers login de l'application
    path('', RedirectView.as_view(url='login/', permanent=False), name='home'),

    # Administration Django (standard)
    path('admin/', admin.site.urls),

    # Authentification de l'application
    path('login/', auth_views.LoginView.as_view(
        template_name='login/login.html',
        extra_context={'app_login': True}
    ), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('home/', home_redirect, name='app_home'),
    path('clear-middleware/', views.clear_middleware_messages, name='clear_middleware'),
    
    # APIs de diagnostic et correction (admin seulement)
    path('admin/diagnostic-clients/', views.diagnostic_clients_ajax, name='diagnostic_clients_ajax'),
    path('admin/corriger-clients/', views.corriger_clients_ajax, name='corriger_clients_ajax'),

    # URLs des applications (avec leurs préfixes clairs)
    path('commande/', include('commande.urls')),
    path('article/', include('article.urls')),
    path('client/', include('client.urls')),
    path('operateur-confirme/', include('operatConfirme.urls')),
    # Redirection pour compatibilité avec d'anciens liens
    path('operatConfirme/', RedirectView.as_view(url='/operateur-confirme/', permanent=True)),
    path('operateur-logistique/', include('operatLogistic.urls')),
    path('operateur-preparation/', include('Prepacommande.urls')),
    path('livraison/', include('livraison.urls')),
    path('parametre/', include('parametre.urls')),
    path('synchronisation/', include('synchronisation.urls')),
    path('kpis/', include('kpis.urls')),

    # Django browser reload (développement)
    path("__reload__/", include("django_browser_reload.urls")),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
