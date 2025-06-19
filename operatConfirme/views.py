from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from commande.models import Commande
from django.contrib import messages
from django.contrib.auth.models import User, Group
from parametre.models import Operateur # Assurez-vous que ce chemin est correct
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm # Importez PasswordChangeForm
from django.http import JsonResponse
import json
from django.utils import timezone
from commande.models import Commande, EtatCommande, EnumEtatCmd
from datetime import datetime, timedelta
from django.db.models import Sum

# Create your views here.

@login_required
def dashboard(request):
    """Page d'accueil de l'interface opérateur de confirmation"""
    from commande.models import Commande, EtatCommande
    from django.utils import timezone
    from datetime import datetime, timedelta
    from django.db.models import Sum
    
    try:
        # Récupérer le profil opérateur de l'utilisateur connecté
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de confirmation non trouvé.")
        return redirect('login')
    
    # Dates pour les calculs de périodes
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    
    # Récupérer les commandes affectées à cet opérateur
    commandes_affectees = Commande.objects.filter(
        etats__operateur=operateur,
        etats__date_fin__isnull=True  # États actifs (non terminés)
    ).distinct()
    
    # Statistiques des commandes affectées à cet opérateur
    stats = {}
    
    # Commandes en attente de confirmation (affectées mais pas encore en cours de confirmation)
    stats['commandes_en_attente'] = commandes_affectees.filter(
        etats__enum_etat__libelle='Affectée',
        etats__date_fin__isnull=True
    ).count()
    
    # Commandes en cours de confirmation
    stats['commandes_en_cours'] = commandes_affectees.filter(
        etats__enum_etat__libelle='En cours de confirmation',
        etats__date_fin__isnull=True
    ).count()
    
    # Commandes confirmées par cet opérateur (toutes)
    commandes_confirmees_all = Commande.objects.filter(
        etats__operateur=operateur,
        etats__enum_etat__libelle='Confirmée'
    ).distinct()
    
    stats['commandes_confirmees'] = commandes_confirmees_all.count()
    
    # Commandes confirmées aujourd'hui
    stats['commandes_confirmees_aujourd_hui'] = commandes_confirmees_all.filter(
        etats__date_debut__date=today
    ).count()
    
    # Commandes confirmées cette semaine
    stats['commandes_confirmees_semaine'] = commandes_confirmees_all.filter(
        etats__date_debut__date__gte=week_start
    ).count()
    
    # Valeur totale des commandes confirmées
    valeur_totale = commandes_confirmees_all.aggregate(
        total=Sum('total_cmd')
    )['total'] or 0
    stats['valeur_totale_confirmees'] = valeur_totale
    
    # Commandes marquées erronées par cet opérateur
    stats['commandes_erronnees'] = Commande.objects.filter(
        etats__operateur=operateur,
        etats__enum_etat__libelle='Erronée'
    ).distinct().count()
    
    stats['total_commandes'] = commandes_affectees.count()
    
    # Taux de performance
    if stats['total_commandes'] > 0:
        stats['taux_confirmation'] = round((stats['commandes_confirmees'] / stats['total_commandes']) * 100, 1)
    else:
        stats['taux_confirmation'] = 0
    
    context = {
        'operateur': operateur,
        **stats  # Ajouter toutes les statistiques au contexte
    }
    
    return render(request, 'composant_generale/operatConfirme/home.html', context)

@login_required
def liste_commandes(request):
    """Liste des commandes affectées à l'opérateur de confirmation connecté"""
    from django.core.paginator import Paginator
    from django.db.models import Q, Count, Sum
    from commande.models import Commande, EtatCommande
    
    try:
        # Récupérer le profil opérateur de l'utilisateur connecté
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de confirmation non trouvé.")
        return redirect('login')
    
    # Récupérer TOUTES les commandes affectées à cet opérateur (Affectées + En cours de confirmation)
    commandes_affectees = Commande.objects.filter(
        etats__operateur=operateur,
        etats__date_fin__isnull=True  # États actifs (non terminés)
    ).distinct().select_related(
        'client', 'ville', 'ville__region'
    ).prefetch_related(
        'etats__enum_etat', 'paniers__article'
    ).order_by('-date_cmd', '-date_creation')
    
    # Recherche
    search_query = request.GET.get('search', '').strip()
    if search_query:
        commandes_affectees = commandes_affectees.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query) |
            Q(ville__nom__icontains=search_query) |
            Q(adresse__icontains=search_query)
        )
    
    # Statistiques des commandes affectées à cet opérateur
    stats = {}
    
    # Commandes en attente de confirmation (affectées mais pas encore en cours de confirmation)
    stats['commandes_en_attente'] = commandes_affectees.filter(
        etats__enum_etat__libelle='Affectée',
        etats__date_fin__isnull=True
    ).count()
    
    # Commandes en cours de confirmation
    stats['commandes_en_cours'] = commandes_affectees.filter(
        etats__enum_etat__libelle='En cours de confirmation',
        etats__date_fin__isnull=True
    ).count()
    
    # Commandes confirmées par cet opérateur
    stats['commandes_confirmees'] = Commande.objects.filter(
        etats__operateur=operateur,
        etats__enum_etat__libelle='Confirmée'
    ).count()
    
    # Commandes marquées erronées par cet opérateur
    stats['commandes_erronnees'] = Commande.objects.filter(
        etats__operateur=operateur,
        etats__enum_etat__libelle='Erronée'
    ).count()
    
    stats['total_commandes'] = commandes_affectees.count()
    
    # Pagination
    paginator = Paginator(commandes_affectees, 15)  # 15 commandes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'operateur': operateur,
        **stats  # Ajouter toutes les statistiques au contexte
    }
    
    return render(request, 'operatConfirme/liste_commande.html', context)

@login_required
def confirmer_commande_ajax(request, commande_id):
    """Confirme une commande spécifique via AJAX depuis la page de confirmation"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.http import JsonResponse
    from django.utils import timezone
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            commentaire = data.get('commentaire', '')
        except:
            commentaire = ''
    
    try:
        # Récupérer l'opérateur
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Profil d\'opérateur de confirmation non trouvé.'})
    
    try:
        commande = Commande.objects.get(id=commande_id)
        
        # Vérifier que la commande est affectée à cet opérateur
        etat_actuel = commande.etat_actuel
        if not (etat_actuel and etat_actuel.operateur == operateur):
            return JsonResponse({'success': False, 'message': 'Cette commande ne vous est pas affectée.'})
        
        # Créer le nouvel état "confirmée"
        enum_confirmee = EnumEtatCmd.objects.get(libelle='Confirmée')
        
        # Fermer l'état actuel
        etat_actuel.date_fin = timezone.now()
        etat_actuel.save()
        
        # Créer le nouvel état
        EtatCommande.objects.create(
            commande=commande,
            enum_etat=enum_confirmee,
            operateur=operateur,
            date_debut=timezone.now(),
            commentaire=commentaire
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Commande {commande.id_yz} confirmée avec succès.'
        })
        
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande non trouvée.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@login_required
def confirmer_commande(request, commande_id):
    """Confirmer une commande"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.utils import timezone
    from django.http import JsonResponse
    
    if request.method == 'POST':
        try:
            # Récupérer l'opérateur
            operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            
            # Récupérer la commande
            commande = Commande.objects.get(pk=commande_id)
            
            # Vérifier que la commande est bien affectée à cet opérateur
            etat_actuel = commande.etats.filter(
                operateur=operateur,
                date_fin__isnull=True
            ).first()
            
            if not etat_actuel:
                messages.error(request, "Cette commande ne vous est pas affectée.")
                return redirect('operatConfirme:liste_commandes')
            
            # Terminer l'état actuel
            etat_actuel.terminer_etat(operateur)
            
            # Créer un nouvel état "confirmée"
            enum_confirmee = EnumEtatCmd.objects.get(libelle='Confirmée')
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=enum_confirmee,
                operateur=operateur,
                commentaire=request.POST.get('commentaire', '')
            )
            
            messages.success(request, f"Commande {commande.id_yz} confirmée avec succès.")
            
            # Réponse JSON pour AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Commande confirmée'})
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la confirmation : {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)})
    
    return redirect('operatConfirme:liste_commandes')

@login_required
def marquer_erronnee(request, commande_id):
    """Marquer une commande comme erronée"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.utils import timezone
    from django.http import JsonResponse
    
    if request.method == 'POST':
        try:
            # Récupérer l'opérateur
            operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            
            # Récupérer la commande
            commande = Commande.objects.get(pk=commande_id)
            
            # Vérifier que la commande est bien affectée à cet opérateur
            etat_actuel = commande.etats.filter(
                operateur=operateur,
                date_fin__isnull=True
            ).first()
            
            if not etat_actuel:
                messages.error(request, "Cette commande ne vous est pas affectée.")
                return redirect('operatConfirme:liste_commandes')
            
            # Terminer l'état actuel
            etat_actuel.terminer_etat(operateur)
            
            # Créer un nouvel état "erronée"
            enum_erronnee = EnumEtatCmd.objects.get(libelle='Erronée')
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=enum_erronnee,
                operateur=operateur,
                commentaire=request.POST.get('motif', '')
            )
            
            messages.success(request, f"Commande {commande.id_yz} marquée comme erronée.")
            
            # Réponse JSON pour AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Commande marquée comme erronée'})
                
        except Exception as e:
            messages.error(request, f"Erreur lors de l'opération : {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)})
    
    return redirect('operatConfirme:liste_commandes')

@login_required
def parametre(request):
    """Page des paramètres opérateur confirmation"""
    return render(request, 'operatConfirme/parametre.html')

@login_required
def commandes_confirmees(request):
    """Vue pour afficher les commandes confirmées par l'opérateur connecté"""
    try:
        # Récupérer l'objet Operateur correspondant à l'utilisateur connecté
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
        
        # Récupérer seulement les commandes confirmées par cet opérateur
        mes_commandes_confirmees = Commande.objects.filter(
            etats__enum_etat__libelle='Confirmée',
            etats__date_fin__isnull=True,
            etats__operateur=operateur  # Utiliser l'objet Operateur
        ).select_related('client', 'ville', 'ville__region').prefetch_related('etats', 'operations').distinct()
        
        # Tri par date de confirmation (plus récentes en premier)
        mes_commandes_confirmees = mes_commandes_confirmees.order_by('-etats__date_debut')
        
    except Operateur.DoesNotExist:
        # Si l'utilisateur n'est pas un opérateur, liste vide
        mes_commandes_confirmees = Commande.objects.none()
    
    # Breadcrumb
    breadcrumb_items = [
        {'label': 'Gestion de Commandes', 'url': None, 'icon': 'clipboard-check'},
        {'label': 'Mes Confirmées', 'url': None, 'icon': 'check-circle'}
    ]
    
    context = {
        'mes_commandes_confirmees': mes_commandes_confirmees,
        'breadcrumb_items': breadcrumb_items,
    }
    
    return render(request, 'operatConfirme/commandes_confirmees.html', context)

@login_required
def creer_operateur_confirme(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        mail = request.POST.get('mail')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        # Validation de base (vous pouvez ajouter des validations plus robustes ici)
        if not all([username, password, nom, prenom, mail]):
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return render(request, 'composant_generale/creer_operateur.html', {'form_data': request.POST})
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return render(request, 'composant_generale/creer_operateur.html', {'form_data': request.POST})
        
        if User.objects.filter(email=mail).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return render(request, 'composant_generale/creer_operateur.html', {'form_data': request.POST})

        try:
            # Créer l'utilisateur Django
            user = User.objects.create_user(
                username=username,
                email=mail,
                password=password,
                first_name=prenom,
                last_name=nom
            )
            user.save()

            # Créer le profil Operateur
            operateur = Operateur.objects.create(
                user=user,
                nom=nom,
                prenom=prenom,
                mail=mail,
                type_operateur='CONFIRMATION',
                telephone=telephone,
                adresse=adresse
            )
            operateur.save()

            # Ajouter l'utilisateur au groupe 'operateur_confirme'
            group, created = Group.objects.get_or_create(name='operateur_confirme')
            user.groups.add(group)

            messages.success(request, f"L'opérateur de confirmation {prenom} {nom} a été créé avec succès.")
            return redirect('app_admin:liste_operateurs') # Rediriger vers la liste des opérateurs

        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la création de l'opérateur : {e}")
            # Si l'utilisateur a été créé mais pas l'opérateur, le supprimer pour éviter les orphelins
            if 'user' in locals() and user.pk: 
                user.delete()
            return render(request, 'composant_generale/creer_operateur.html', {'form_data': request.POST})

    return render(request, 'composant_generale/creer_operateur.html')

@login_required
def profile_confirme(request):
    """Page de profil pour l'opérateur de confirmation"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur non trouvé.")
        return redirect('login') # Rediriger vers la page de connexion ou une page d'erreur
    return render(request, 'operatConfirme/profile.html', {'operateur': operateur})

@login_required
def modifier_profile_confirme(request):
    """Page de modification de profil pour l'opérateur de confirmation"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur non trouvé.")
        return redirect('login')

    user = request.user

    if request.method == 'POST':
        # Récupérer les données du formulaire
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        # Validation de base
        if not all([first_name, last_name, email]):
            messages.error(request, "Le prénom, le nom et l'email sont obligatoires.")
            return render(request, 'operatConfirme/modifier_profile.html', {'operateur': operateur, 'user': user})

        # Vérifier si l'email est déjà utilisé par un autre utilisateur (sauf l'utilisateur actuel)
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            messages.error(request, "Cet email est déjà utilisé par un autre compte.")
            return render(request, 'operatConfirme/modifier_profile.html', {'operateur': operateur, 'user': user})
        
        try:
            # Mettre à jour l'objet User
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()

            # Mettre à jour l'objet Operateur
            operateur.nom = last_name # Mettre à jour le nom de famille de l'opérateur
            operateur.prenom = first_name # Mettre à jour le prénom de l'opérateur
            operateur.mail = email
            operateur.telephone = telephone
            operateur.adresse = adresse
            # Gérer le téléchargement de la photo
            if 'photo' in request.FILES:
                operateur.photo = request.FILES['photo']
            elif request.POST.get('photo-clear'): # Si une case à cocher pour supprimer la photo est présente
                operateur.photo = None

            # Ne pas modifier type_operateur ou actif
            operateur.save()

            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('operatConfirme:profile')

        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la mise à jour : {e}")

    return render(request, 'operatConfirme/modifier_profile.html', {'operateur': operateur, 'user': user})

@login_required
def changer_mot_de_passe_confirme(request):
    """Page de changement de mot de passe pour l'opérateur de confirmation"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important! Pour garder l'utilisateur connecté
            messages.success(request, 'Votre mot de passe a été mis à jour avec succès !')
            return redirect('operatConfirme:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'operatConfirme/changer_mot_de_passe.html', {'form': form})

@login_required
def detail_commande(request, commande_id):
    """Aperçu détaillé d'une commande avec possibilité de modification"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse
    
    try:
        # Récupérer l'opérateur
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de confirmation non trouvé.")
        return redirect('login')
    
    # Récupérer la commande avec toutes les relations
    commande = get_object_or_404(
        Commande.objects.select_related(
            'client', 'ville', 'ville__region'
        ).prefetch_related(
            'paniers__article', 'etats__enum_etat', 'etats__operateur'
        ),
        pk=commande_id
    )
    
    # Vérifier que la commande est bien affectée à cet opérateur
    etat_actuel = commande.etats.filter(
        operateur=operateur,
        date_fin__isnull=True
    ).first()
    
    if not etat_actuel:
        messages.error(request, "Cette commande ne vous est pas affectée.")
        return redirect('operatConfirme:liste_commandes')
    
    # Traitement de la modification si POST
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'modifier_commande':
            # Modifier les champs modifiables
            nouvelle_adresse = request.POST.get('adresse', '').strip()
            nouveau_telephone = request.POST.get('telephone', '').strip()
            commentaire = request.POST.get('commentaire', '').strip()
            
            # Mise à jour des champs
            if nouvelle_adresse:
                commande.adresse = nouvelle_adresse
            
            if nouveau_telephone:
                commande.client.numero_tel = nouveau_telephone
                commande.client.save()
            
            commande.save()
            
            # Ajouter un commentaire si fourni
            if commentaire:
                etat_actuel.commentaire = commentaire
                etat_actuel.save()
            
            messages.success(request, "Commande mise à jour avec succès.")
            
            # Réponse JSON pour AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Commande mise à jour'})
        
        elif action == 'confirmer':
            return confirmer_commande(request, commande_id)
        
        elif action == 'marquer_erronnee':
            return marquer_erronnee(request, commande_id)
    
    # Calculer le sous-total des articles
    total_articles = sum(panier.sous_total for panier in commande.paniers.all())
    
    context = {
        'commande': commande,
        'etat_actuel': etat_actuel,
        'operateur': operateur,
        'total_articles': total_articles,
        'historique_etats': commande.historique_etats
    }
    
    return render(request, 'operatConfirme/detail_commande.html', context)

@login_required
def confirmation(request):
    """Page dédiée à la confirmation des commandes"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.http import JsonResponse
    from django.utils import timezone
    
    try:
        # Récupérer l'opérateur
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de confirmation non trouvé.")
        return redirect('login')
    
    # Récupérer les commandes "Affectées" ET "En cours de confirmation"
    commandes_a_confirmer = Commande.objects.filter(
        etats__operateur=operateur,
        etats__date_fin__isnull=True,  # États actifs (non terminés)
        etats__enum_etat__libelle__in=['Affectée', 'En cours de confirmation']  # Affectées ET en cours
    ).select_related(
        'client', 'ville', 'ville__region'
    ).prefetch_related(
        'paniers__article', 'etats__enum_etat'
    ).distinct().order_by('-date_cmd', '-date_creation')
    
    context = {
        'operateur': operateur,
        'commandes_a_confirmer': commandes_a_confirmer,
    }
    
    return render(request, 'operatConfirme/confirmation.html', context)

@login_required
def lancer_confirmations(request):
    """Lance le processus de confirmation automatique pour l'opérateur"""
    from django.http import JsonResponse
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    
    if request.method == 'POST':
        try:
            # Récupérer l'opérateur
            operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            
            # Récupérer toutes les commandes affectées à cet opérateur qui sont en attente
            commandes_a_traiter = Commande.objects.filter(
                etats__operateur=operateur,
                etats__date_fin__isnull=True,
                etats__enum_etat__libelle='affectee'
            ).distinct()
            
            # Compteur pour les commandes traitées
            commandes_traitees = 0
            erreurs = []
            
            for commande in commandes_a_traiter:
                try:
                    # Récupérer l'état actuel
                    etat_actuel = commande.etats.filter(
                        operateur=operateur,
                        date_fin__isnull=True
                    ).first()
                    
                    if etat_actuel:
                        # Terminer l'état actuel
                        etat_actuel.terminer_etat(operateur)
                        
                        # Créer un nouvel état "en cours de confirmation"
                        enum_en_cours = EnumEtatCmd.objects.get_or_create(
                            libelle='en_cours_confirmation',
                            defaults={'ordre': 2, 'couleur': '#3B82F6'}
                        )[0]
                        
                        EtatCommande.objects.create(
                            commande=commande,
                            enum_etat=enum_en_cours,
                            operateur=operateur,
                            commentaire='Processus de confirmation automatique lancé'
                        )
                        
                        commandes_traitees += 1
                        
                except Exception as e:
                    erreurs.append(f"Commande {commande.id_yz}: {str(e)}")
            
            # Préparer la réponse
            if erreurs:
                message = f"{commandes_traitees} commandes traitées avec {len(erreurs)} erreurs."
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'commandes_traitees': commandes_traitees,
                    'erreurs': erreurs
                })
            else:
                message = f"Processus lancé avec succès ! {commandes_traitees} commandes mises en cours de confirmation."
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'commandes_traitees': commandes_traitees
                })
                
        except Operateur.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': "Profil d'opérateur non trouvé."
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f"Erreur lors du traitement: {str(e)}"
            })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def selectionner_operation(request):
    """Vue AJAX pour sélectionner une opération pour une commande"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            commande_id = data.get('commande_id')
            type_operation = data.get('type_operation')
            commentaire = data.get('commentaire', '')
            
            if not commande_id or not type_operation:
                return JsonResponse({
                    'success': False,
                    'message': 'Données manquantes'
                })
            
            # Récupérer l'opérateur
            operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            
            # Récupérer la commande
            commande = Commande.objects.get(id=commande_id)
            
            # Vérifier que la commande est en cours de confirmation par cet opérateur
            etat_actuel = commande.etats.filter(
                operateur=operateur,
                date_fin__isnull=True,
                enum_etat__libelle='En cours de confirmation'
            ).first()
            
            if not etat_actuel:
                return JsonResponse({
                    'success': False,
                    'message': 'Cette commande n\'est pas en cours de confirmation par vous'
                })
            
            # Supprimer l'ancienne opération si elle existe pour cette commande
            from commande.models import Operation
            Operation.objects.filter(
                commande=commande,
                operateur=operateur,
                type_operation__in=[
                    'AUCUNE_ACTION', 'APPEL_1', 'APPEL_2', 'APPEL_3', 'APPEL_4',
                    'APPEL_5', 'APPEL_6', 'APPEL_7', 'APPEL_8', 'ENVOI_SMS',
                    'ENVOI_MSG', 'PROPOSITION_ABONNEMENT', 'PROPOSITION_REDUCTION'
                ]
            ).delete()
            
            # Créer la nouvelle opération
            conclusion = commentaire if commentaire else f"Opération sélectionnée : {dict(Operation.TYPE_OPERATION_CHOICES)[type_operation]}"
            
            operation = Operation.objects.create(
                commande=commande,
                type_operation=type_operation,
                conclusion=conclusion,
                operateur=operateur
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Opération "{operation.get_type_operation_display()}" sélectionnée',
                'operation_display': operation.get_type_operation_display()
            })
            
        except Operateur.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Profil d\'opérateur non trouvé'
            })
        except Commande.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Commande non trouvée'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})

@login_required
def confirmer_commandes_ajax(request):
    """Vue AJAX pour confirmer plusieurs commandes en masse"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            commande_ids = data.get('commande_ids', [])
            
            if not commande_ids:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucune commande sélectionnée'
                })
            
            # Vérifier que l'opérateur est bien de type confirmation
            if not hasattr(request.user, 'operateurconfirme'):
                return JsonResponse({
                    'success': False,
                    'message': 'Accès non autorisé'
                })
            
            operateur = request.user.operateurconfirme
            confirmed_count = 0
            
            # État "confirmée"
            try:
                etat_confirmee = EnumEtatCmd.objects.get(libelle='confirmee')
            except EnumEtatCmd.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'État "confirmée" non trouvé dans le système'
                })
            
            for commande_id in commande_ids:
                try:
                    # Récupérer la commande
                    commande = Commande.objects.get(
                        id=commande_id,
                        etats__operateur=operateur,
                        etats__date_fin__isnull=True
                    )
                    
                    # Récupérer l'état actuel (non terminé) de cette commande pour cet opérateur
                    etat_actuel = commande.etats.filter(
                        operateur=operateur,
                        date_fin__isnull=True
                    ).first()
                    
                    if etat_actuel:
                        # Terminer l'état actuel
                        etat_actuel.date_fin = timezone.now()
                        etat_actuel.save()
                        
                        # Créer le nouvel état "confirmée"
                        EtatCommande.objects.create(
                            commande=commande,
                            enum_etat=etat_confirmee,
                            operateur=operateur,
                            date_debut=timezone.now(),
                            commentaire=f"Commande confirmée via confirmation en masse"
                        )
                        
                        confirmed_count += 1
                
                except Commande.DoesNotExist:
                    continue  # Ignorer les commandes non trouvées
                except Exception as e:
                    continue  # Ignorer les erreurs individuelles
            
            if confirmed_count > 0:
                return JsonResponse({
                    'success': True,
                    'message': f'{confirmed_count} commande(s) confirmée(s) avec succès'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucune commande n\'a pu être confirmée'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Données JSON invalides'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors de la confirmation: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    })

@login_required
def lancer_confirmation(request, commande_id):
    """Vue pour lancer la confirmation d'une commande (Affectée -> En cours de confirmation)"""
    if request.method == 'POST':
        try:
            # Récupérer l'opérateur de confirmation
            try:
                operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            except Operateur.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Profil d\'opérateur de confirmation non trouvé'
                })
            
            # Récupérer la commande
            try:
                commande = Commande.objects.get(id=commande_id)
            except Commande.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Commande non trouvée'
                })
            
            # Vérifier que la commande est dans l'état "Affectée"
            etat_actuel = commande.etats.filter(
                operateur=operateur,
                date_fin__isnull=True
            ).first()
            
            if not etat_actuel:
                return JsonResponse({
                    'success': False,
                    'message': 'Cette commande ne vous est pas affectée'
                })
            
            if etat_actuel.enum_etat.libelle.lower() == 'en cours de confirmation':
                return JsonResponse({
                    'success': True,
                    'message': 'La commande est déjà en cours de confirmation'
                })
            
            if etat_actuel.enum_etat.libelle.lower() != 'affectée':
                return JsonResponse({
                    'success': False,
                    'message': f'Cette commande est déjà en état "{etat_actuel.enum_etat.libelle}" et ne peut pas être mise en cours de confirmation'
                })
            
            # États requis
            try:
                etat_en_cours = EnumEtatCmd.objects.get(libelle='En cours de confirmation')
            except EnumEtatCmd.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'État "En cours de confirmation" non trouvé dans le système'
                })
            
            # Terminer l'état actuel
            etat_actuel.date_fin = timezone.now()
            etat_actuel.save()
            
            # Créer le nouvel état "En cours de confirmation"
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_en_cours,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire="Confirmation lancée par l'opérateur"
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Confirmation lancée avec succès pour la commande {commande.id_yz}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors du lancement de la confirmation: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    })

@login_required
def lancer_confirmations_masse(request):
    """Vue AJAX pour lancer la confirmation de plusieurs commandes en masse"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            commande_ids = data.get('commande_ids', [])
            
            if not commande_ids:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucune commande sélectionnée'
                })
            
            # Récupérer l'opérateur de confirmation
            try:
                operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            except Operateur.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Profil d\'opérateur de confirmation non trouvé'
                })
            
            launched_count = 0
            
            # État "En cours de confirmation"
            try:
                etat_en_cours = EnumEtatCmd.objects.get(libelle='En cours de confirmation')
            except EnumEtatCmd.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'État "En cours de confirmation" non trouvé dans le système'
                })
            
            for commande_id in commande_ids:
                try:
                    # Récupérer la commande
                    commande = Commande.objects.get(
                        id=commande_id,
                        etats__operateur=operateur,
                        etats__date_fin__isnull=True
                    )
                    
                    # Récupérer l'état actuel (non terminé) de cette commande pour cet opérateur
                    etat_actuel = commande.etats.filter(
                        operateur=operateur,
                        date_fin__isnull=True
                    ).first()
                    
                    # Vérifier que la commande est dans l'état "Affectée"
                    if etat_actuel and etat_actuel.enum_etat.libelle.lower() == 'affectée':
                        # Terminer l'état actuel
                        etat_actuel.date_fin = timezone.now()
                        etat_actuel.save()
                        
                        # Créer le nouvel état "En cours de confirmation"
                        EtatCommande.objects.create(
                            commande=commande,
                            enum_etat=etat_en_cours,
                            operateur=operateur,
                            date_debut=timezone.now(),
                            commentaire="Confirmation lancée en masse"
                        )
                        
                        launched_count += 1
                
                except Commande.DoesNotExist:
                    continue  # Ignorer les commandes non trouvées
                except Exception as e:
                    continue  # Ignorer les erreurs individuelles
            
            if launched_count > 0:
                return JsonResponse({
                    'success': True,
                    'message': f'{launched_count} confirmation(s) lancée(s) avec succès'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucune commande n\'a pu être mise en cours de confirmation'
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Données JSON invalides'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors du lancement: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    })

@login_required
def annuler_lancement_confirmation(request, commande_id):
    """Vue pour annuler le lancement de confirmation d'une commande (En cours de confirmation -> Affectée)"""
    if request.method == 'POST':
        try:
            # Récupérer l'opérateur de confirmation
            try:
                operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            except Operateur.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Profil d\'opérateur de confirmation non trouvé'
                })
            
            # Récupérer la commande
            try:
                commande = Commande.objects.get(id=commande_id)
            except Commande.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Commande non trouvée'
                })
            
            # Vérifier que la commande est dans l'état "En cours de confirmation"
            etat_actuel = commande.etats.filter(
                operateur=operateur,
                date_fin__isnull=True
            ).first()
            
            if not etat_actuel:
                return JsonResponse({
                    'success': False,
                    'message': 'Cette commande ne vous est pas affectée'
                })
            
            if etat_actuel.enum_etat.libelle.lower() == 'affectée':
                return JsonResponse({
                    'success': True,
                    'message': 'La commande est déjà en état "Affectée"'
                })
            
            if etat_actuel.enum_etat.libelle.lower() != 'en cours de confirmation':
                return JsonResponse({
                    'success': False,
                    'message': f'Cette commande est en état "{etat_actuel.enum_etat.libelle}" et ne peut pas être remise en "Affectée"'
                })
            
            # État "Affectée"
            try:
                etat_affectee = EnumEtatCmd.objects.get(libelle='Affectée')
            except EnumEtatCmd.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'État "Affectée" non trouvé dans le système'
                })
            
            # Terminer l'état actuel
            etat_actuel.date_fin = timezone.now()
            etat_actuel.save()
            
            # Créer le nouvel état "Affectée"
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_affectee,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire="Lancement de confirmation annulé par l'opérateur"
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Lancement annulé avec succès pour la commande {commande.id_yz}. La commande est remise en état "Affectée".'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors de l\'annulation: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    })

@login_required
def relancer_confirmation(request, commande_id):
    """Vue pour relancer la confirmation d'une commande (Confirmée -> En cours de confirmation)"""
    if request.method == 'POST':
        try:
            # Récupérer l'opérateur de confirmation
            try:
                operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
            except Operateur.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Profil d\'opérateur de confirmation non trouvé'
                })
            
            # Récupérer la commande
            try:
                commande = Commande.objects.get(id=commande_id)
            except Commande.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Commande non trouvée'
                })
            
            # Vérifier que la commande est dans l'état "Confirmée"
            etat_actuel = commande.etat_actuel
            
            if not etat_actuel:
                return JsonResponse({
                    'success': False,
                    'message': 'Aucun état trouvé pour cette commande'
                })
            
            if etat_actuel.enum_etat.libelle != 'Confirmée':
                return JsonResponse({
                    'success': False,
                    'message': f'Cette commande est en état "{etat_actuel.enum_etat.libelle}" et ne peut pas être relancée'
                })
            
            # État "En cours de confirmation"
            try:
                etat_en_cours = EnumEtatCmd.objects.get(libelle='En cours de confirmation')
            except EnumEtatCmd.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'État "En cours de confirmation" non trouvé dans le système'
                })
            
            # Terminer l'état actuel
            etat_actuel.date_fin = timezone.now()
            etat_actuel.save()
            
            # Créer le nouvel état "En cours de confirmation"
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_en_cours,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire="Confirmation relancée par l'opérateur"
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Confirmation relancée avec succès pour la commande {commande.id_yz}.'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur lors du relancement: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Méthode non autorisée'
    })

@login_required
def modifier_commande(request, commande_id):
    """Page de modification complète d'une commande pour les opérateurs de confirmation"""
    from commande.models import Commande
    from parametre.models import Ville
    
    try:
        # Récupérer l'opérateur
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de confirmation non trouvé.")
        return redirect('login')
    
    # Récupérer la commande
    commande = get_object_or_404(Commande, id=commande_id)
    
    # Vérifier que la commande est affectée à cet opérateur
    etat_actuel = commande.etats.filter(
        operateur=operateur,
        date_fin__isnull=True
    ).first()
    
    if not etat_actuel:
        messages.error(request, "Cette commande ne vous est pas affectée.")
        return redirect('operatConfirme:confirmation')
    
    if request.method == 'POST':
        try:
            # Mise à jour des informations client
            commande.client.nom = request.POST.get('client_nom', '').strip()
            commande.client.prenom = request.POST.get('client_prenom', '').strip()
            commande.client.numero_tel = request.POST.get('client_telephone', '').strip()
            commande.client.save()
            
            # Mise à jour de la date de commande
            date_cmd = request.POST.get('date_cmd')
            if date_cmd:
                from datetime import datetime
                commande.date_cmd = datetime.strptime(date_cmd, '%Y-%m-%d').date()
            
            # Mise à jour de la ville et de l'adresse
            ville_id = request.POST.get('ville_livraison')
            if ville_id:
                nouvelle_ville = Ville.objects.get(id=ville_id)
                commande.ville = nouvelle_ville
            
            adresse = request.POST.get('adresse_livraison', '').strip()
            if adresse:
                commande.adresse = adresse
            
            commande.save()
            
            messages.success(request, 'Commande modifiée avec succès.')
            return redirect('operatConfirme:modifier_commande', commande_id=commande_id)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la modification : {str(e)}')
    
    # Récupérer toutes les villes pour la liste déroulante
    villes = Ville.objects.select_related('region').order_by('region__nom_region', 'nom')
    
    context = {
        'commande': commande,
        'operateur': operateur,
        'villes': villes,
    }
    
    return render(request, 'operatConfirme/modifier_commande.html', context)


