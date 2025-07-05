from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Min, Max, Sum
from django.contrib.auth.models import User, Group
from django.contrib import messages
from .models import Region, Ville, Operateur, HistoriqueMotDePasse
from article.models import Article
from commande.models import Commande, EtatCommande, EnumEtatCmd
from django.contrib.messages import success, error
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash # Required for password change

@login_required
def dashboard(request):
    """Page d'accueil de l'interface administrateur"""
    return render(request, 'composant_generale/admin/home.html')

@staff_member_required
@login_required
def liste_operateurs(request):
    """Liste des opérateurs"""
    operateurs = Operateur.objects.select_related('user').order_by('nom', 'prenom').exclude(type_operateur='ADMIN')
    
    # Statistiques pour les cartes
    total_operateurs = Operateur.objects.exclude(type_operateur='ADMIN').count()
    operateurs_actifs = Operateur.objects.filter(actif=True).exclude(type_operateur='ADMIN').count()
    operateurs_inactifs = Operateur.objects.filter(actif=False).exclude(type_operateur='ADMIN').count()
    administrateurs = Operateur.objects.filter(type_operateur='ADMIN').count()
    
    # Filtrage par type si spécifié
    type_filter = request.GET.get('type')
    if type_filter:
        operateurs = operateurs.filter(type_operateur=type_filter)
    
    # Recherche
    search = request.GET.get('search')
    if search:
        operateurs = operateurs.filter(
            Q(nom__icontains=search) | 
            Q(prenom__icontains=search) |
            Q(mail__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(operateurs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'type_filter': type_filter,
        'search': search,
        'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN'],
        'total_operateurs': total_operateurs,
        'operateurs_actifs': operateurs_actifs,
        'operateurs_inactifs': operateurs_inactifs,
        'administrateurs': administrateurs,
    }
    return render(request, 'parametre/liste_operateurs.html', context)

@staff_member_required
@login_required
def creer_operateur(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        mail = request.POST.get('mail')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')
        type_operateur = request.POST.get('type_operateur')

        # Validation de base
        if not all([username, password, nom, prenom, mail, type_operateur]):
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return render(request, 'parametre/creer_operateur.html', {'form_data': request.POST, 'types_operateur': Operateur.TYPE_OPERATEUR_CHOICES})
        
        if type_operateur == 'ADMIN':
            messages.error(request, "Les opérateurs de type 'Administrateur' ne peuvent pas être créés via ce formulaire.")
            return render(request, 'parametre/creer_operateur.html', {'form_data': request.POST, 'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN']})

        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return render(request, 'parametre/creer_operateur.html', {'form_data': request.POST, 'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN']})
        
        if User.objects.filter(email=mail).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return render(request, 'parametre/creer_operateur.html', {'form_data': request.POST, 'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN']})

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
                type_operateur=type_operateur,
                telephone=telephone,
                adresse=adresse
            )
            operateur.save()

            # Ajouter l'utilisateur au groupe correspondant au type d'opérateur
            group_name_map = {
                'CONFIRMATION': 'operateur_confirme',
                'LOGISTIQUE': 'operateur_logistique',
                'ADMIN': 'administrateur', # Assurez-vous que ce groupe existe
            }
            group_name = group_name_map.get(type_operateur)
            if group_name:
                group, created = Group.objects.get_or_create(name=group_name)
                user.groups.add(group)

            messages.success(request, f"L'opérateur {prenom} {nom} ({type_operateur}) a été créé avec succès.")
            return redirect('app_admin:liste_operateurs')

        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la création de l'opérateur : {e}")
            if 'user' in locals() and user.pk:
                user.delete()
            return render(request, 'parametre/creer_operateur.html', {'form_data': request.POST, 'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN']})

    return render(request, 'parametre/creer_operateur.html', {'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN']})

@staff_member_required
@login_required
def liste_regions(request):
    """Liste des régions avec statistiques"""
    regions = Region.objects.annotate(
        nb_villes=Count('villes'),
        tarif_moyen=Avg('villes__frais_livraison')
    ).order_by('nom_region')
    
    # Recherche
    search = request.GET.get('search')
    if search:
        regions = regions.filter(nom_region__icontains=search)
    
    # Pagination
    paginator = Paginator(regions, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'total_regions': Region.objects.count(),
        'total_villes': Ville.objects.count(),
    }
    return render(request, 'parametre/liste_regions.html', context)

@staff_member_required
@login_required
def detail_region(request, region_id):
    """Détail d'une région avec ses villes"""
    region = get_object_or_404(Region, id=region_id)
    villes = region.villes.order_by('nom')
    
    # Statistiques de la région
    stats = {
        'nb_villes': villes.count(),
        'tarif_min': villes.aggregate(min_tarif=Min('frais_livraison'))['min_tarif'],
        'tarif_max': villes.aggregate(max_tarif=Max('frais_livraison'))['max_tarif'],
        'tarif_moyen': villes.aggregate(avg_tarif=Avg('frais_livraison'))['avg_tarif'],
    }
    
    # Recherche dans les villes
    search = request.GET.get('search')
    if search:
        villes = villes.filter(nom__icontains=search)
    
    # Pagination des villes
    paginator = Paginator(villes, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'region': region,
        'page_obj': page_obj,
        'stats': stats,
        'search': search,
    }
    return render(request, 'parametre/detail_region.html', context)

@staff_member_required
@login_required
def liste_villes(request):
    """Liste complète des villes"""
    villes = Ville.objects.select_related('region').order_by('region__nom_region', 'nom')
    
    # Filtrage par région
    region_filter = request.GET.get('region')
    if region_filter:
        villes = villes.filter(region_id=region_filter)
    
    # Filtrage par tarif
    tarif_min = request.GET.get('tarif_min')
    tarif_max = request.GET.get('tarif_max')
    if tarif_min:
        villes = villes.filter(frais_livraison__gte=tarif_min)
    if tarif_max:
        villes = villes.filter(frais_livraison__lte=tarif_max)
    
    # Recherche
    search = request.GET.get('search')
    if search:
        villes = villes.filter(
            Q(nom__icontains=search) | 
            Q(region__nom_region__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(villes, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Liste des régions pour le filtre
    regions = Region.objects.order_by('nom_region')
    
    context = {
        'page_obj': page_obj,
        'regions': regions,
        'region_filter': region_filter,
        'tarif_min': tarif_min,
        'tarif_max': tarif_max,
        'search': search,
    }
    return render(request, 'parametre/liste_villes.html', context)

@staff_member_required
@login_required
def synchronisation(request):
    """Page de synchronisation"""
    return render(request, 'parametre/synchronisation.html')

@staff_member_required
@login_required
def logs(request):
    """Page des logs système"""
    return render(request, 'parametre/logs.html')

@staff_member_required
@login_required
def detail_operateur(request, pk):
    """Afficher les détails d'un opérateur avec ses commandes affectées"""
    operateur = get_object_or_404(Operateur.objects.select_related('user'), pk=pk)
    
    # Récupérer les commandes affectées à cet opérateur
    from commande.models import EtatCommande, Commande
    from django.db.models import Sum, Count, Q
    from django.core.paginator import Paginator
    
    # Commandes actuellement affectées à cet opérateur
    commandes_affectees = Commande.objects.filter(
        etats__operateur=operateur,
        etats__date_fin__isnull=True
    ).distinct().order_by('-date_cmd')
    
    # Historique de toutes les commandes traitées par cet opérateur
    commandes_historique = Commande.objects.filter(
        etats__operateur=operateur
    ).distinct().order_by('-date_cmd')
    
    # Statistiques
    total_commandes_affectees = commandes_affectees.count()
    total_commandes_traitees = commandes_historique.count()
    
    # Montant total des commandes affectées
    montant_total_affectees = commandes_affectees.aggregate(
        total=Sum('total_cmd')
    )['total'] or 0
    
    # Montant total de toutes les commandes traitées
    montant_total_traitees = commandes_historique.aggregate(
        total=Sum('total_cmd')
    )['total'] or 0
    
    # Statistiques par état pour cet opérateur
    etats_stats = EtatCommande.objects.filter(
        operateur=operateur
    ).values(
        'enum_etat__libelle', 'enum_etat__couleur'
    ).annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Historique des modifications de mots de passe
    historique_mots_de_passe = HistoriqueMotDePasse.objects.filter(
        operateur=operateur
    ).select_related('administrateur').order_by('-date_modification')[:10]  # Les 10 dernières modifications
    
    # Dernière modification de mot de passe
    derniere_modification_mdp = historique_mots_de_passe.first() if historique_mots_de_passe.exists() else None
    
    # Pagination pour les commandes affectées
    paginator = Paginator(commandes_affectees, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Recherche dans les commandes affectées
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_affectees = commandes_affectees.filter(
            Q(num_cmd__icontains=search_query) |
            Q(id_yz__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query)
        )
        paginator = Paginator(commandes_affectees, 10)
        page_obj = paginator.get_page(page_number)
    
    context = {
        'operateur': operateur,
        'page_obj': page_obj,
        'search_query': search_query,
        'total_commandes_affectees': total_commandes_affectees,
        'total_commandes_traitees': total_commandes_traitees,
        'montant_total_affectees': montant_total_affectees,
        'montant_total_traitees': montant_total_traitees,
        'etats_stats': etats_stats,
        'historique_mots_de_passe': historique_mots_de_passe,
        'derniere_modification_mdp': derniere_modification_mdp,
    }
    return render(request, 'parametre/detail_operateur.html', context)

@staff_member_required
@login_required
def modifier_operateur(request, pk):
    """Modifier un opérateur existant"""
    operateur = get_object_or_404(Operateur.objects.select_related('user'), pk=pk)
    user = operateur.user

    if request.method == 'POST':
        username = request.POST.get('username')
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        mail = request.POST.get('mail')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')
        type_operateur = request.POST.get('type_operateur')
        actif = request.POST.get('actif') == 'on'
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Validation de base
        if not all([username, nom, prenom, mail, type_operateur]):
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return render(request, 'parametre/modifier_operateur.html', {'operateur': operateur, 'form_data': request.POST, 'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN']})
        
        if type_operateur == 'ADMIN':
            messages.error(request, "Les opérateurs de type 'Administrateur' ne peuvent pas être gérés via ce formulaire.")
            return render(request, 'parametre/modifier_operateur.html', {'operateur': operateur, 'form_data': request.POST, 'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN']})

        # Vérifier si le nom d'utilisateur ou l'email existe déjà pour un AUTRE utilisateur
        if User.objects.filter(username=username).exclude(pk=user.pk).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà pour un autre utilisateur.")
            return render(request, 'parametre/modifier_operateur.html', {'operateur': operateur, 'form_data': request.POST, 'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN']})
        
        if User.objects.filter(email=mail).exclude(pk=user.pk).exists():
            messages.error(request, "Cet email est déjà utilisé par un autre utilisateur.")
            return render(request, 'parametre/modifier_operateur.html', {'operateur': operateur, 'form_data': request.POST, 'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN']})

        # Validation du mot de passe
        if password or confirm_password:
            if password != confirm_password:
                messages.error(request, "Les mots de passe ne correspondent pas.")
                return render(request, 'parametre/modifier_operateur.html', {'operateur': operateur, 'form_data': request.POST, 'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN']})
            if password and len(password) < 8:
                messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
                return render(request, 'parametre/modifier_operateur.html', {'operateur': operateur, 'form_data': request.POST, 'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN']})

        try:
            # Mettre à jour l'utilisateur Django
            user.username = username
            user.email = mail
            user.first_name = prenom
            user.last_name = nom
            user.is_active = actif
            if password:
                user.set_password(password)
            user.save()

            # Mettre à jour le profil Operateur
            operateur.nom = nom
            operateur.prenom = prenom
            operateur.mail = mail
            operateur.type_operateur = type_operateur
            operateur.telephone = telephone
            operateur.adresse = adresse
            operateur.actif = actif
            operateur.save()
            
            # Gérer l'appartenance aux groupes
            group_name_map = {
                'CONFIRMATION': 'operateur_confirme',
                'LOGISTIQUE': 'operateur_logistique',
            }
            
            # Retirer l'utilisateur de tous les groupes d'opérateur précédents
            for group_name in group_name_map.values():
                group = Group.objects.filter(name=group_name).first()
                if group and user.groups.filter(name=group_name).exists():
                    user.groups.remove(group)

            # Ajouter l'utilisateur au nouveau groupe correspondant au type d'opérateur
            new_group_name = group_name_map.get(type_operateur)
            if new_group_name:
                group, created = Group.objects.get_or_create(name=new_group_name)
                user.groups.add(group)

            messages.success(request, f"L'opérateur {prenom} {nom} a été modifié avec succès.")
            return redirect('app_admin:liste_operateurs')

        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la modification de l'opérateur : {e}")

    context = {
        'operateur': operateur,
        'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN'],
        'form_data': {
            'username': operateur.user.username,
            'nom': operateur.nom,
            'prenom': operateur.prenom,
            'mail': operateur.mail,
            'telephone': operateur.telephone,
            'adresse': operateur.adresse,
            'type_operateur': operateur.type_operateur,
            'actif': 'on' if operateur.actif else '',
        }
    }
    return render(request, 'parametre/modifier_operateur.html', context)

@staff_member_required
@login_required
def supprimer_operateur(request, pk):
    """Supprimer un opérateur"""
    if request.method == 'POST':
        operateur = get_object_or_404(Operateur, pk=pk)
        user = operateur.user

        try:
            # Supprimer l'opérateur et l'utilisateur associé
            user.delete()
            messages.success(request, f"L'opérateur {operateur.prenom} {operateur.nom} a été supprimé avec succès.")
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la suppression de l'opérateur : {e}")

    return redirect('app_admin:liste_operateurs')

@require_POST
@staff_member_required
@login_required
def supprimer_operateurs_masse(request):
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucun opérateur sélectionné pour la suppression.")
        return redirect('app_admin:liste_operateurs')

    try:
        operateurs_a_supprimer = Operateur.objects.filter(pk__in=selected_ids)
        count = operateurs_a_supprimer.count()
        for operateur in operateurs_a_supprimer:
            user_to_delete = operateur.user
            operateur.delete()
            user_to_delete.delete()
        messages.success(request, f"{count} opérateur(s) supprimé(s) avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('app_admin:liste_operateurs')

@staff_member_required
@login_required
def modifier_region(request, pk):
    region = get_object_or_404(Region, pk=pk)
    if request.method == 'POST':
        nom_region = request.POST.get('nom_region')
        if nom_region:
            region.nom_region = nom_region
            region.save()
            messages.success(request, "La région a été modifiée avec succès.")
            return redirect('app_admin:detail_region', region_id=region.pk)
        else:
            messages.error(request, "Le nom de la région ne peut pas être vide.")
    context = {
        'region': region
    }
    return render(request, 'parametre/modifier_region.html', context)

@staff_member_required
@login_required
def creer_region(request):
    if request.method == 'POST':
        nom_region = request.POST.get('nom_region')
        if nom_region:
            if Region.objects.filter(nom_region__iexact=nom_region).exists():
                messages.error(request, "Une région avec ce nom existe déjà.")
            else:
                Region.objects.create(nom_region=nom_region)
                messages.success(request, f"La région '{nom_region}' a été créée avec succès.")
                return redirect('app_admin:liste_regions')
        else:
            messages.error(request, "Le nom de la région ne peut pas être vide.")
    return render(request, 'parametre/creer_region.html')

@staff_member_required
@login_required
def modifier_ville(request, pk):
    ville = get_object_or_404(Ville, pk=pk)
    regions = Region.objects.all().order_by('nom_region')

    if request.method == 'POST':
        nom_ville = request.POST.get('nom')
        frais_livraison = request.POST.get('frais_livraison')
        frequence_livraison = request.POST.get('frequence_livraison')
        region_id = request.POST.get('region')

        if not all([nom_ville, frais_livraison, frequence_livraison, region_id]):
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
        else:
            try:
                region = get_object_or_404(Region, pk=region_id)
                ville.nom = nom_ville
                ville.frais_livraison = float(frais_livraison)
                ville.frequence_livraison = frequence_livraison
                ville.region = region
                ville.save()
                messages.success(request, f"La ville '{nom_ville}' a été modifiée avec succès.")
                return redirect('app_admin:liste_villes')
            except ValueError:
                messages.error(request, "Les frais de livraison doivent être un nombre valide.")
            except Exception as e:
                messages.error(request, f"Une erreur est survenue lors de la modification de la ville : {e}")

    context = {
        'ville': ville,
        'regions': regions,
        'formatted_frais_livraison': f'{ville.frais_livraison:.2f}' if ville.frais_livraison is not None else ''
    }
    return render(request, 'parametre/modifier_ville.html', context)

@staff_member_required
@login_required
def creer_ville(request):
    regions = Region.objects.all().order_by('nom_region')
    if request.method == 'POST':
        nom_ville = request.POST.get('nom')
        frais_livraison = request.POST.get('frais_livraison')
        frequence_livraison = request.POST.get('frequence_livraison')
        region_id = request.POST.get('region')

        if not all([nom_ville, frais_livraison, frequence_livraison, region_id]):
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
        else:
            try:
                region = get_object_or_404(Region, pk=region_id)
                if Ville.objects.filter(nom__iexact=nom_ville, region=region).exists():
                    messages.error(request, "Une ville avec ce nom existe déjà dans cette région.")
                else:
                    Ville.objects.create(
                        nom=nom_ville,
                        frais_livraison=float(frais_livraison),
                        frequence_livraison=frequence_livraison,
                        region=region
                    )
                    messages.success(request, f"La ville '{nom_ville}' a été créée avec succès.")
                    return redirect('app_admin:liste_villes')
            except ValueError:
                messages.error(request, "Les frais de livraison doivent être un nombre valide.")
            except Exception as e:
                messages.error(request, f"Une erreur est survenue lors de la création de la ville : {e}")

    context = {
        'regions': regions,
    }
    return render(request, 'parametre/creer_ville.html', context)

@staff_member_required
@login_required
def supprimer_ville(request, pk):
    ville = get_object_or_404(Ville, pk=pk)
    if request.method == 'POST':
        try:
            ville.delete()
            messages.success(request, f"La ville '{ville.nom}' a été supprimée avec succès.")
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la suppression de la ville : {e}")
        return redirect('app_admin:liste_villes')
    return redirect('app_admin:liste_villes')

@require_POST
@staff_member_required
@login_required
def supprimer_villes_masse(request):
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucune ville sélectionnée pour la suppression.")
        return redirect('app_admin:liste_villes')

    try:
        count = Ville.objects.filter(pk__in=selected_ids).delete()[0]
        messages.success(request, f"{count} ville(s) supprimée(s) avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('app_admin:liste_villes')

@staff_member_required
@login_required
def supprimer_region(request, pk):
    region = get_object_or_404(Region, pk=pk)
    if request.method == 'POST':
        try:
            region.delete()
            messages.success(request, f"La région '{region.nom_region}' a été supprimée avec succès.")
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la suppression de la région : {e}")
        return redirect('app_admin:liste_regions')
    return redirect('app_admin:liste_regions')

@require_POST
@staff_member_required
@login_required
def supprimer_regions_masse(request):
    selected_ids = request.POST.getlist('ids[]')
    if not selected_ids:
        messages.error(request, "Aucune région sélectionnée pour la suppression.")
        return redirect('app_admin:liste_regions')

    try:
        # On récupère les régions, puis on les supprime
        count = Region.objects.filter(pk__in=selected_ids).delete()[0]
        messages.success(request, f"{count} région(s) supprimée(s) avec succès.")
    except Exception as e:
        messages.error(request, f"Une erreur est survenue lors de la suppression en masse : {e}")
    
    return redirect('app_admin:liste_regions')

@staff_member_required
@login_required
def detail_ville(request, pk):
    ville = get_object_or_404(Ville, pk=pk)
    context = {
        'ville': ville
    }
    return render(request, 'parametre/detail_ville.html', context)

@staff_member_required
@login_required
def admin_profile(request):
    try:
        operateur = Operateur.objects.get(user=request.user)
    except Operateur.DoesNotExist:
        operateur = None
    context = {
        'user': request.user,
        'operateur': operateur,
    }
    return render(request, 'parametre/admin_profile.html', context)

@staff_member_required
@login_required
def modifier_admin_profile(request):
    try:
        operateur = Operateur.objects.get(user=request.user)
    except Operateur.DoesNotExist:
        # If admin doesn't have an Operateur profile, create one.
        # This might happen if the admin was created directly via Django admin and not as an Operateur.
        operateur = Operateur.objects.create(
            user=request.user,
            nom=request.user.last_name if request.user.last_name else '',
            prenom=request.user.first_name if request.user.first_name else '',
            mail=request.user.email,
            type_operateur='ADMIN'
        )

    if request.method == 'POST':
        # Handle User fields
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.save()

        # Handle Operateur fields
        operateur.telephone = request.POST.get('telephone')
        operateur.adresse = request.POST.get('adresse')
        if 'photo' in request.FILES:
            operateur.photo = request.FILES['photo']
        elif request.POST.get('clear_photo') == 'on': # For clearing existing photo
            operateur.photo = None

        operateur.save()

        messages.success(request, "Votre profil a été mis à jour avec succès.")
        return redirect('app_admin:profile')

    context = {
        'user': request.user,
        'operateur': operateur,
    }
    return render(request, 'parametre/modifier_admin_profile.html', context)

@staff_member_required
@login_required
def changer_mot_de_passe_admin(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important! Keeps the user logged in
            messages.success(request, 'Votre mot de passe a été mis à jour avec succès !')
            return redirect('app_admin:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'parametre/changer_mot_de_passe_admin.html', {'form': form})

@staff_member_required
@login_required
def modifier_mot_de_passe_operateur(request, pk):
    """Permet à l'admin de modifier le mot de passe d'un opérateur"""
    operateur = get_object_or_404(Operateur, pk=pk)
    
    if request.method == 'POST':
        nouveau_mot_de_passe = request.POST.get('nouveau_mot_de_passe')
        confirmer_mot_de_passe = request.POST.get('confirmer_mot_de_passe')
        
        # Validation
        if not nouveau_mot_de_passe:
            messages.error(request, "Le nouveau mot de passe est obligatoire.")
            return render(request, 'parametre/modifier_mot_de_passe_operateur.html', {'operateur': operateur})
        
        if len(nouveau_mot_de_passe) < 6:
            messages.error(request, "Le mot de passe doit contenir au moins 6 caractères.")
            return render(request, 'parametre/modifier_mot_de_passe_operateur.html', {'operateur': operateur})
        
        if nouveau_mot_de_passe != confirmer_mot_de_passe:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'parametre/modifier_mot_de_passe_operateur.html', {'operateur': operateur})
        
        try:
            # Changer le mot de passe
            user = operateur.user
            user.set_password(nouveau_mot_de_passe)
            user.save()
            
            # Enregistrer dans l'historique
            def get_client_ip(request):
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                return ip
            
            HistoriqueMotDePasse.objects.create(
                operateur=operateur,
                administrateur=request.user,
                adresse_ip=get_client_ip(request),
                commentaire=f"Mot de passe modifié par l'administrateur {request.user.get_full_name() or request.user.username}"
            )
            
            messages.success(request, f"Le mot de passe de {operateur.prenom} {operateur.nom} a été modifié avec succès.")
            return redirect('app_admin:detail_operateur', pk=operateur.pk)
            
        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la modification du mot de passe : {str(e)}")
    
    context = {
        'operateur': operateur,
    }
    return render(request, 'parametre/modifier_mot_de_passe_operateur.html', context)

@staff_member_required
@login_required
def gestion_mots_de_passe(request):
    """Vue pour la gestion globale des mots de passe des opérateurs"""
    operateurs = Operateur.objects.select_related('user').prefetch_related('historique_mots_de_passe').exclude(type_operateur='ADMIN').order_by('nom', 'prenom')
    
    # Recherche
    search = request.GET.get('search')
    if search:
        operateurs = operateurs.filter(
            Q(nom__icontains=search) | 
            Q(prenom__icontains=search) |
            Q(mail__icontains=search)
        )
    
    # Filtrage par type
    type_filter = request.GET.get('type')
    if type_filter:
        operateurs = operateurs.filter(type_operateur=type_filter)
    
    # Pagination
    paginator = Paginator(operateurs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'type_filter': type_filter,
        'types_operateur': [choice for choice in Operateur.TYPE_OPERATEUR_CHOICES if choice[0] != 'ADMIN'],
    }
    return render(request, 'parametre/gestion_mots_de_passe.html', context)
