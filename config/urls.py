from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from .views import home_redirect, custom_logout, get_csrf_token_view, check_csrf_status
from . import views
from commande.views import api_panier_commande

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
    
    # Routes pour la gestion CSRF
    path('api/csrf/token/', get_csrf_token_view, name='get_csrf_token'),
    path('api/csrf/status/', check_csrf_status, name='check_csrf_status'),
    
    # APIs de diagnostic et correction (admin seulement)
    path('admin/diagnostic-clients/', views.diagnostic_clients_ajax, name='diagnostic_clients_ajax'),
    path('admin/corriger-clients/', views.corriger_clients_ajax, name='corriger_clients_ajax'),
    
    # API pour panier commande
    path('api/commande/<int:commande_id>/panier/', api_panier_commande, name='api_panier_commande'),

    # URLs des applications (avec leurs préfixes clairs)
    path('commande/', include('commande.urls')),
    path('article/', include('article.urls')),
    path('client/', include('client.urls')),
    path('operateur-confirme/', include('operatConfirme.urls')),
    # Redirection pour compatibilité avec d'anciens liens
    path('operatConfirme/', RedirectView.as_view(url='/operateur-confirme/', permanent=True)),
    path('operateur-logistique/', include('operatLogistic.urls')),
    path('operateur-preparation/', include('Prepacommande.urls')),
    path('Superpreparation/', include('Superpreparation.urls')),
    path('livraison/', include('livraison.urls')),
    path('parametre/', include('parametre.urls')),
    path('synchronisation/', include('synchronisation.urls')),
    path('kpis/', include('kpis.urls')),
    # Notifications app supprimée
    
    # Pages 404 personnalisées par interface
    path('404/admin/', include('parametre.404.admin.urls')),
    path('404/confirmation/', include('parametre.404.confirmation.urls')),
    path('404/preparation/', include('parametre.404.preparation.urls')),
    path('404/logistique/', include('parametre.404.logistique.urls')),

    # Django browser reload (développement)
    path("__reload__/", include("django_browser_reload.urls")),
]

# Servir les fichiers media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
