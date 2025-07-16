from django.shortcuts               import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib                 import messages
from django.db.models               import Q
from django.core.paginator          import Paginator

from parametre.models import Operateur
from commande.models  import Commande


@login_required
def dashboard(request):
    """Page d'accueil de l'interface opérateur logistique."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    # Statistiques simples pour le dashboard
    en_preparation    = Commande.objects.filter(etats__enum_etat__libelle='En préparation', etats__date_fin__isnull=True).distinct().count()
    prets_expedition  = Commande.objects.filter(etats__enum_etat__libelle='Préparée',        etats__date_fin__isnull=True).distinct().count()
    expedies          = Commande.objects.filter(etats__enum_etat__libelle='En cours de livraison', etats__date_fin__isnull=True).distinct().count()
    
    context = {
        'operateur'        : operateur,
        'en_preparation'   : en_preparation,
        'prets_expedition' : prets_expedition,
        'expedies'         : expedies,
        'page_title'       : 'Tableau de Bord Logistique',
    }
    return render(request, 'composant_generale/operatLogistic/home.html', context)


@login_required
def liste_commandes(request):
    """Liste des commandes affectées à cet opérateur logistique."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    commandes_list = Commande.objects.filter(
        etats__enum_etat__libelle='En cours de livraison',
        etats__operateur=operateur,
        etats__date_fin__isnull=True
    ).select_related('client', 'ville__region').distinct().order_by('-etats__date_debut')
    
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_list = commandes_list.filter(
            Q(id_yz__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query)
        )
    
    paginator   = Paginator(commandes_list, 20)
    page_number = request.GET.get('page')
    page_obj    = paginator.get_page(page_number)
    
    context = {
        'page_obj'        : page_obj,
        'search_query'    : search_query,
        'total_commandes' : commandes_list.count(),
        'page_title'      : 'Commandes en Livraison',
    }
    return render(request, 'operatLogistic/liste_commande.html', context)


@login_required
def detail_commande(request, commande_id):
    """Détails d'une commande pour l'opérateur logistique."""
    commande = get_object_or_404(Commande, id=commande_id)
    # Idéalement, ajouter une vérification pour s'assurer que l'opérateur a le droit de voir cette commande
    context = {
        'commande'   : commande,
        'page_title' : f'Détail Commande {commande.id_yz}',
    }
    return render(request, 'operatLogistic/detail_commande.html', context)


# Vues pour le profil, à compléter si nécessaire
@login_required
def profile_logistique(request):
    return render(request, 'operatLogistic/profile.html')


@login_required
def modifier_profile_logistique(request):
    messages.info(request, "Cette fonctionnalité est en cours de développement.")
    return redirect('operatLogistic:profile')


@login_required
def changer_mot_de_passe_logistique(request):
    messages.info(request, "Cette fonctionnalité est en cours de développement.")
    return redirect('operatLogistic:profile')


@login_required
def parametre(request):
    return render(request, 'operatLogistic/parametre.html')


@login_required
def marquer_livree(request, commande_id):
    messages.info(request, "Cette fonctionnalité est en cours de développement.")
    return redirect('operatLogistic:detail_commande', commande_id=commande_id)


@login_required
def signaler_probleme(request, commande_id):
    messages.info(request, "Cette fonctionnalité est en cours de développement.")
    return redirect('operatLogistic:detail_commande', commande_id=commande_id)


@login_required
def changer_etat_sav(request, commande_id):
    messages.info(request, "Cette fonctionnalité est en cours de développement.")
    return redirect('operatLogistic:detail_commande', commande_id=commande_id)
