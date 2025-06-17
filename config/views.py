from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse, NoReverseMatch

@login_required
def home_redirect(request):
    """
    Redirige l'utilisateur vers sa page home spécifique selon son type
    """
    user = request.user
    
    # Vérifier si c'est un opérateur de confirmation
    if user.groups.filter(name='operateur_confirme').exists():
        return redirect(reverse('operatConfirme:home'))
    
    # Vérifier si c'est un opérateur logistique
    elif user.groups.filter(name='operateur_logistique').exists():
        return redirect(reverse('operatLogistic:home'))
    
    # Par défaut, rediriger vers l'interface paramètres (admin)
    else:
        return redirect(reverse('app_admin:home'))

@login_required
def test_admin_url(request):
    try:
        url = reverse('admin:liste_operateurs')
        message = f"URL for admin:liste_operateurs resolved successfully: {url}"
    except NoReverseMatch as e:
        message = f"Failed to resolve admin:liste_operateurs: {e}"
    return render(request, 'test_url.html', {'message': message}) 