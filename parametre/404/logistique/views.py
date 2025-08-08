from django.shortcuts import render
from django.http import HttpResponseNotFound


def custom_404_logistique(request, exception=None):
    """
    Vue 404 personnalisée pour l'interface logistique
    """
    context = {
        'error_code': '404',
        'error_title': 'Page non trouvée',
        'error_message': 'La page que vous recherchez n\'existe pas ou a été déplacée.',
        'interface_name': 'Opérateur Logistique',
        'interface_color': '#0B1D51',  # Bleu marine pour la logistique
        'back_url': '/operateur-logistique/',
        'back_text': 'Retour au tableau de bord Logistique'
    }
    return HttpResponseNotFound(
        render(request, 'parametre/404/logistique/404.html', context).content
    )
