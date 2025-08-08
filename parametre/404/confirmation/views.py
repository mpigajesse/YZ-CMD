from django.shortcuts import render
from django.http import HttpResponseNotFound


def custom_404_confirmation(request, exception=None):
    """
    Vue 404 personnalisée pour l'interface de confirmation
    """
    context = {
        'error_code': '404',
        'error_title': 'Page non trouvée',
        'error_message': 'La page que vous recherchez n\'existe pas ou a été déplacée.',
        'interface_name': 'Opérateur Confirmation',
        'interface_color': '#4B352A',  # Brun pour la confirmation
        'back_url': '/operateur-confirme/',
        'back_text': 'Retour au tableau de bord Confirmation'
    }
    return HttpResponseNotFound(
        render(request, 'parametre/404/confirmation/404.html', context).content
    )
