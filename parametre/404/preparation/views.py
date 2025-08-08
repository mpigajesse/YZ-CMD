from django.shortcuts import render
from django.http import HttpResponseNotFound


def custom_404_preparation(request, exception=None):
    """
    Vue 404 personnalisée pour l'interface de préparation
    """
    context = {
        'error_code': '404',
        'error_title': 'Page non trouvée',
        'error_message': 'La page que vous recherchez n\'existe pas ou a été déplacée.',
        'interface_name': 'Opérateur Préparation',
        'interface_color': '#361f27',  # Brun foncé pour la préparation
        'back_url': '/operateur-preparation/',
        'back_text': 'Retour au tableau de bord Préparation'
    }
    return HttpResponseNotFound(
        render(request, 'parametre/404/preparation/404.html', context).content
    )
