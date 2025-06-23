from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse, NoReverseMatch
from parametre.models import Operateur

@login_required
def home_redirect(request):
    """
    Redirige l'utilisateur vers sa page home spécifique selon son type
    """
    user = request.user
    
    # Vérifier si l'utilisateur a un profil opérateur
    try:
        operateur = Operateur.objects.get(user=user, actif=True)
        
        # Redirection selon le type d'opérateur
        if operateur.type_operateur == 'PREPARATION':
            return redirect(reverse('Prepacommande:home'))
        elif operateur.type_operateur == 'CONFIRMATION':
            return redirect(reverse('operatConfirme:home'))
        elif operateur.type_operateur == 'LOGISTIQUE':
            return redirect(reverse('operatLogistic:home'))
        elif operateur.type_operateur == 'ADMIN':
            return redirect(reverse('app_admin:home'))
        else:
            # Type d'opérateur non reconnu
            return redirect(reverse('app_admin:home'))
    
    except Operateur.DoesNotExist:
        # Si pas de profil opérateur, vérifier les groupes Django (ancien système)
        if user.groups.filter(name='operateur_confirme').exists():
            return redirect(reverse('operatConfirme:home'))
        elif user.groups.filter(name='operateur_logistique').exists():
            return redirect(reverse('operatLogistic:home'))
        else:
            # Par défaut, rediriger vers l'interface admin
            return redirect(reverse('app_admin:home'))

@login_required
def test_admin_url(request):
    try:
        url = reverse('admin:liste_operateurs')
        message = f"URL for admin:liste_operateurs resolved successfully: {url}"
    except NoReverseMatch as e:
        message = f"Failed to resolve admin:liste_operateurs: {e}"
    return render(request, 'test_url.html', {'message': message}) 

@login_required 
def clear_middleware_messages(request):
    """Vue utilitaire pour forcer le nettoyage des messages MWI-001"""
    from django.contrib import messages
    
    # Nettoyer les flags de session
    keys_to_remove = [key for key in request.session.keys() if key.startswith('middleware_redirect')]
    for key in keys_to_remove:
        del request.session[key]
    
    # Nettoyer les messages MWI-001
    storage = messages.get_messages(request)
    messages_to_keep = []
    messages_cleaned = 0
    
    for message in storage:
        if not ("MWI-001" in str(message) and "Accès non autorisé" in str(message)):
            messages_to_keep.append(message)
        else:
            messages_cleaned += 1
    
    # Remettre seulement les messages à garder
    storage.used = True
    for message in messages_to_keep:
        messages.add_message(request, message.level, message.message, message.tags)
    
    messages.success(request, f"✅ Nettoyage terminé. {messages_cleaned} message(s) MWI-001 supprimé(s).")
    
    # Rediriger vers la page d'accueil appropriée selon le type d'utilisateur
    return home_redirect(request) 