from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def liste_livraisons(request):
    """Liste des livraisons"""
    return render(request, 'livraison/liste.html')

@login_required
def detail_livraison(request, id):
    """Détail d'une livraison"""
    # TODO: Récupérer la livraison par id
    return render(request, 'livraison/detail.html', {'id': id})

@login_required
def creer_livraison(request):
    """Créer une nouvelle livraison"""
    # Logique pour créer une livraison (sera implémentée plus tard)
    return render(request, 'livraison/creer.html') # Vous devrez créer ce template
