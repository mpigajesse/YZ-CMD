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