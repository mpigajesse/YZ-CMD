from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from commande.models import Commande, EtatCommande, EnumEtatCmd
from django.db import transaction

@login_required
@require_POST
def changer_etat_livraison(request, commande_id):
    """
    Vue générique pour changer l'état de livraison d'une commande
    par un opérateur logistique.
    """
    try:
        commande = Commande.objects.get(id=commande_id)
        operateur = request.user.profil_operateur
        
        # Vérifier que l'opérateur est bien un opérateur logistique
        if not operateur or not operateur.is_logistique:
            messages.error(request, "Accès non autorisé.")
            return redirect('operatLogistic:detail_commande', commande_id=commande_id)

        nouvel_etat_libelle = request.POST.get('nouvel_etat')
        commentaire = request.POST.get('commentaire')

        if not nouvel_etat_libelle or not commentaire:
            messages.error(request, "L'état et le commentaire sont obligatoires.")
            return redirect('operatLogistic:detail_commande', commande_id=commande_id)
            
        # Logique de changement d'état
        with transaction.atomic():
            # 1. Trouver et terminer l'état actuel
            etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
            if etat_actuel:
                etat_actuel.date_fin = timezone.now()
                etat_actuel.save()

            # 2. Créer le nouvel état
            nouvel_etat_enum = EnumEtatCmd.objects.get(libelle=nouvel_etat_libelle)
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=nouvel_etat_enum,
                operateur=operateur,
                commentaire=commentaire
            )
        
        messages.success(request, f"L'état de la commande {commande.id_yz} a été mis à jour avec succès.")
        
        # Redirection intelligente vers la page appropriée selon l'action SAV
        if nouvel_etat_libelle == 'Livrée':
            return redirect('operatLogistic:commandes_livrees')
        elif nouvel_etat_libelle == 'Reportée':
            return redirect('operatLogistic:commandes_reportees')
        elif nouvel_etat_libelle == 'Livrée Partiellement':
            return redirect('operatLogistic:commandes_livrees_partiellement')
        elif nouvel_etat_libelle == 'Livrée avec changement':
            return redirect('operatLogistic:commandes_livrees_avec_changement')
        elif nouvel_etat_libelle == 'Annulée (SAV)':
            return redirect('operatLogistic:commandes_annulees_sav')
        else:
            # Fallback vers la page de détail de la commande
            return redirect('operatLogistic:detail_commande', commande_id=commande_id)

    except Commande.DoesNotExist:
        messages.error(request, "Commande non trouvée.")
        return redirect('operatLogistic:home')
    except EnumEtatCmd.DoesNotExist:
        messages.error(request, "L'état demandé n'existe pas.")
        return redirect('operatLogistic:detail_commande', commande_id=commande_id)
    except Exception as e:
        messages.error(request, f"Une erreur est survenue : {e}")
        return redirect('operatLogistic:detail_commande', commande_id=commande_id)

def _render_sav_list(request, queryset, page_title, page_subtitle):
    """Fonction helper pour rendre les templates des listes SAV."""
    context = {
        'commandes': queryset,
        'page_title': page_title,
        'page_subtitle': page_subtitle,
    }
    return render(request, 'operatLogistic/sav/liste_commandes_sav.html', context)

@login_required
def commandes_reportees(request):
    """Affiche les commandes dont la livraison est reportée."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Reportée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville').prefetch_related(
        'etats__enum_etat', 'etats__operateur'
    ).order_by('-etats__date_debut').distinct()
    return _render_sav_list(request, commandes, 'Commandes Reportées', 'Liste des livraisons reportées.')

@login_required
def commandes_livrees_partiellement(request):
    """Affiche les commandes livrées partiellement."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée Partiellement',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville').prefetch_related(
        'etats__enum_etat', 'etats__operateur'
    ).order_by('-etats__date_debut').distinct()
    return _render_sav_list(request, commandes, 'Commandes Livrées Partiellement', 'Liste des commandes livrées en partie.')

@login_required
def commandes_livrees_avec_changement(request):
    """Affiche les commandes livrées avec un changement d'article."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée avec changement',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville').prefetch_related(
        'etats__enum_etat', 'etats__operateur'
    ).order_by('-etats__date_debut').distinct()
    return _render_sav_list(request, commandes, 'Commandes avec Changement', 'Liste des commandes livrées avec un article différent.')

@login_required
def commandes_annulees_sav(request):
    """Affiche les commandes annulées au stade de la livraison."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Annulée (SAV)',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville').prefetch_related(
        'etats__enum_etat', 'etats__operateur'
    ).order_by('-etats__date_debut').distinct()
    return _render_sav_list(request, commandes, 'Commandes Annulées (SAV)', 'Liste des commandes annulées lors de la livraison.')

@login_required
def commandes_livrees(request):
    """Affiche les commandes livrées avec succès."""
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville').prefetch_related(
        'etats__enum_etat', 'etats__operateur'
    ).order_by('-etats__date_debut').distinct()
    return _render_sav_list(request, commandes, 'Commandes Livrées', 'Liste des commandes livrées avec succès.') 