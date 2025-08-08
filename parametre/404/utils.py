from django.shortcuts import redirect
from django.urls import reverse


def redirect_to_interface_404(request, interface_type='admin'):
    """
    Redirige vers la page 404 appropriée selon l'interface
    
    Args:
        request: L'objet request Django
        interface_type: Type d'interface ('admin', 'confirmation', 'preparation', 'logistique')
    
    Returns:
        HttpResponseRedirect vers la page 404 appropriée
    """
    interface_mapping = {
        'admin': 'admin_404:404',
        'confirmation': 'confirmation_404:404',
        'preparation': 'preparation_404:404',
        'logistique': 'logistique_404:404'
    }
    
    url_name = interface_mapping.get(interface_type, 'admin_404:404')
    return redirect(reverse(url_name))


def detect_interface_from_path(request_path):
    """
    Détecte le type d'interface basé sur le chemin de la requête
    
    Args:
        request_path: Le chemin de la requête (request.path)
    
    Returns:
        str: Le type d'interface détecté
    """
    if '/operateur-confirme/' in request_path or '/operatConfirme/' in request_path:
        return 'confirmation'
    elif '/operateur-preparation/' in request_path or '/Prepacommande/' in request_path:
        return 'preparation'
    elif '/operateur-logistique/' in request_path or '/operatLogistic/' in request_path:
        return 'logistique'
    elif '/parametre/' in request_path or '/admin/' in request_path:
        return 'admin'
    else:
        return 'admin'  # Par défaut


def get_custom_404_view(request):
    """
    Retourne la vue 404 appropriée selon l'interface détectée
    
    Args:
        request: L'objet request Django
    
    Returns:
        HttpResponse: La réponse 404 personnalisée
    """
    interface_type = detect_interface_from_path(request.path)
    
    if interface_type == 'confirmation':
        from .confirmation.views import custom_404_confirmation
        return custom_404_confirmation(request)
    elif interface_type == 'preparation':
        from .preparation.views import custom_404_preparation
        return custom_404_preparation(request)
    elif interface_type == 'logistique':
        from .logistique.views import custom_404_logistique
        return custom_404_logistique(request)
    else:
        from .admin.views import custom_404_admin
        return custom_404_admin(request)
