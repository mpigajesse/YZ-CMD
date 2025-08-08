from django.shortcuts import render
from django.http import HttpResponseNotFound


def custom_404_admin(request, exception=None):
    """
    Vue 404 personnalisée pour l'interface admin
    """
    context = {
        'error_code': '404',
        'error_title': 'Page non trouvée',
        'error_message': 'La page que vous recherchez n\'existe pas ou a été déplacée.',
        'interface_name': 'Administration',
        'interface_color': '#1f2937',  # Gris foncé pour l'admin
        'back_url': '/admin/',
        'back_text': 'Retour au tableau de bord Admin'
    }
    return HttpResponseNotFound(
        render(request, 'parametre/404/admin/404.html', context).content
    )
