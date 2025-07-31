from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Min, Max, Sum
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from .models import Region, Ville, Operateur, HistoriqueMotDePasse
from article.models import Article
from commande.models import Commande, EtatCommande, EnumEtatCmd
from django.contrib.messages import success, error
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash # Required for password change
from io import BytesIO
import csv

# Vérification de la disponibilité d'openpyxl pour les exports Excel
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

@login_required
def dashboard(request):
    """Page d'accueil de l'interface administrateur - Redirige vers le dashboard KPIs"""
    # Rediriger directement vers le dashboard KPIs pour les administrateurs
    if request.user.is_staff or hasattr(request.user, 'profil_operateur') and request.user.profil_operateur.type_operateur == 'ADMIN':
        return redirect('/kpis/')
    
    # Fallback vers l'ancien dashboard pour les autres types d'utilisateurs
    # Statistiques pour le dashboard
    stats = {
        'total_articles': Article.objects.count(),
        'articles_disponibles': Article.objects.filter(qte_disponible__gt=0).count(),
        'total_commandes': Commande.objects.count(),
        'total_operateurs': Operateur.objects.count(),
        'operateurs_actifs': Operateur.objects.filter(actif=True).count(),
    }
    
    # Ajouter les statistiques des états de commandes
    try:
        from commande.models import EtatCommande, EnumEtatCmd
        
        # Compter les commandes par état en utilisant les libellés des états
        commandes_non_affectees = EtatCommande.objects.filter(
            date_fin__isnull=True,
            enum_etat__libelle__icontains='Non affectée'
        ).count()
        
        commandes_affectees = EtatCommande.objects.filter(
            date_fin__isnull=True,
            enum_etat__libelle__icontains='Affectée'
        ).count()
        
        commandes_erronnees = EtatCommande.objects.filter(
            date_fin__isnull=True,
            enum_etat__libelle__icontains='Erronée'
        ).count()
        
        commandes_doublons = EtatCommande.objects.filter(
            date_fin__isnull=True,
            enum_etat__libelle__icontains='Doublon'
        ).count()
        
        # Commandes nouvelles = commandes sans état actuel
        commandes_avec_etat = EtatCommande.objects.filter(date_fin__isnull=True).values_list('commande_id', flat=True)
        commandes_nouvelles = Commande.objects.exclude(id__in=commandes_avec_etat).count()
        
        stats.update({
            'commandes_non_affectees': commandes_non_affectees,
            'commandes_affectees': commandes_affectees,
            'commandes_erronnees': commandes_erronnees,
            'commandes_doublons': commandes_doublons,
            'commandes_nouvelles': commandes_nouvelles,
        })
    except ImportError:
        # Si les modèles ne sont pas disponibles, mettre des valeurs par défaut
        stats.update({
            'commandes_non_affectees': 0,
            'commandes_affectees': 0,
            'commandes_erronnees': 0,
            'commandes_doublons': 0,
            'commandes_nouvelles': 0,
        })

    # Récupérer quelques opérateurs actifs pour l'affichage des initiales
    active_operators_for_display = Operateur.objects.filter(actif=True, user__is_superuser=False).order_by('id')[:3]

    context = {
        'stats': stats,
        'active_operators_for_display': active_operators_for_display,
    }
    return render(request, 'composant_generale/admin/home.html', context)

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

# ======================== VUES SERVICE APRÈS-VENTE POUR ADMIN ========================

@staff_member_required
@login_required
def sav_commandes_retournees(request):
    """Vue admin pour afficher les commandes retournées"""
    from commande.models import Commande, EtatCommande
    
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Retournée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Pagination
    paginator = Paginator(commandes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'Commandes Retournées',
        'subtitle': 'Commandes retournées par les clients ou opérateurs logistiques',
        'icon': 'fa-undo',
        'color': 'red'
    }
    return render(request, 'parametre/sav/liste_commandes_sav.html', context)

@staff_member_required
@login_required
def sav_commandes_reportees(request):
    """Vue admin pour afficher les commandes reportées"""
    from commande.models import Commande, EtatCommande
    
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Reportée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
            
    # Pagination
    paginator = Paginator(commandes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'Commandes Reportées',
        'subtitle': 'Commandes dont la livraison a été reportée',
        'icon': 'fa-clock',
        'color': 'orange'
    }
    return render(request, 'parametre/sav/liste_commandes_sav.html', context)

@staff_member_required
@login_required
def sav_livrees_partiellement(request):
    """Vue admin pour afficher les commandes livrées partiellement"""
    from commande.models import Commande, EtatCommande
    
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée Partiellement',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Pagination
    paginator = Paginator(commandes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'Commandes Livrées Partiellement',
        'subtitle': 'Commandes avec livraison partielle',
        'icon': 'fa-box-open',
        'color': 'yellow'
    }
    return render(request, 'parametre/sav/liste_commandes_sav.html', context)

@staff_member_required
@login_required
def sav_annulees_sav(request):
    """Vue admin pour afficher les commandes annulées au niveau SAV"""
    from commande.models import Commande, EtatCommande
    
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Annulée (SAV)',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Pagination
    paginator = Paginator(commandes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'Commandes Annulées (SAV)',
        'subtitle': 'Commandes annulées lors de la livraison',
        'icon': 'fa-times-circle',
        'color': 'gray'
    }
    return render(request, 'parametre/sav/liste_commandes_sav.html', context)

@staff_member_required
@login_required
def sav_livrees_avec_changement(request):
    """Vue admin pour afficher les commandes livrées avec changement"""
    from commande.models import Commande, EtatCommande
    
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée avec changement',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Pagination
    paginator = Paginator(commandes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'Commandes Livrées avec Changement',
        'subtitle': 'Commandes livrées avec modifications',
        'icon': 'fa-exchange-alt',
        'color': 'blue'
    }
    return render(request, 'parametre/sav/liste_commandes_sav.html', context)

@staff_member_required
@login_required
def sav_livrees(request):
    """Vue admin pour afficher les commandes livrées avec succès"""
    from commande.models import Commande, EtatCommande
    
    commandes = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée',
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related(
        'etats__enum_etat', 'etats__operateur', 'paniers__article'
    ).order_by('-etats__date_debut').distinct()
    
    # Pagination
    paginator = Paginator(commandes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'title': 'Commandes Livrées',
        'subtitle': 'Commandes livrées avec succès',
        'icon': 'fa-check-circle',
        'color': 'green'
    }
    return render(request, 'parametre/sav/liste_commandes_sav.html', context)

@staff_member_required
@login_required
@require_POST
def sav_creer_nouvelle_commande(request, commande_id):
    """Créer une nouvelle commande pour les articles défectueux retournés"""
    from commande.models import Commande, Panier, EtatCommande, EnumEtatCmd
    from django.db import transaction
    from django.utils import timezone
    import json
    
    try:
        commande_originale = get_object_or_404(Commande, id=commande_id)
        
        # Récupérer les articles défectueux depuis la requête POST
        articles_defectueux = json.loads(request.POST.get('articles_defectueux', '[]'))
        commentaire = request.POST.get('commentaire', '')
        
        if not articles_defectueux:
            messages.error(request, "Aucun article défectueux spécifié.")
            return redirect('app_admin:sav_commandes_retournees')
        
        with transaction.atomic():
            # Créer une nouvelle commande
            nouvelle_commande = Commande.objects.create(
                client=commande_originale.client,
                ville=commande_originale.ville,
                total_cmd=0,  # Sera recalculé
                num_cmd=f"SAV-{commande_originale.num_cmd}",
                id_yz=f"SAV-{commande_originale.id_yz}",
                is_upsell=False
            )
            
            total = 0
            # Créer les paniers pour les articles défectueux
            for article_data in articles_defectueux:
                article_id = article_data['article_id']
                quantite = int(article_data['quantite'])
                
                # Récupérer l'article original
                panier_original = commande_originale.paniers.filter(
                    article_id=article_id
                ).first()
                
                if panier_original:
                    Panier.objects.create(
                        commande=nouvelle_commande,
                        article=panier_original.article,
                        quantite=quantite,
                        sous_total=panier_original.article.prix_unitaire * quantite
                    )
                    total += panier_original.article.prix_unitaire * quantite
            
            # Mettre à jour le total de la commande
            nouvelle_commande.total_cmd = total
            nouvelle_commande.save()
            
            # Créer l'état initial "Non affectée"
            enum_etat = EnumEtatCmd.objects.get(libelle='Non affectée')
            EtatCommande.objects.create(
                commande=nouvelle_commande,
                enum_etat=enum_etat,
                operateur=request.user.profil_operateur,
                date_debut=timezone.now(),
                commentaire=f"Commande SAV créée pour articles défectueux. {commentaire}"
            )
            
            messages.success(request, 
                f"Nouvelle commande SAV créée avec succès : {nouvelle_commande.num_cmd}")
            return redirect('commande:detail', commande_id=nouvelle_commande.id)
            
    except Exception as e:
        messages.error(request, f"Erreur lors de la création de la commande SAV : {str(e)}")
        return redirect('app_admin:sav_commandes_retournees')

@staff_member_required
@login_required
@require_POST
def sav_renvoyer_preparation(request, commande_id):
    """Renvoyer la commande aux opérateurs de préparation suite aux modifications du client"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.db import transaction
    from django.utils import timezone
    
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        commentaire = request.POST.get('commentaire', '')
        modifications = request.POST.get('modifications', '')
        
        with transaction.atomic():
            # Fermer l'état actuel
            etat_actuel = commande.etat_actuel
            if etat_actuel:
                etat_actuel.date_fin = timezone.now()
                etat_actuel.save()
            
            # Créer un nouvel état "En préparation"
            enum_etat = EnumEtatCmd.objects.get(libelle='Préparation en cours')
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=enum_etat,
                operateur=request.user.profil_operateur,
                date_debut=timezone.now(),
                commentaire=f"Renvoyé en préparation suite à modification client. {modifications}. {commentaire}"
            )
            
            messages.success(request, 
                f"Commande {commande.num_cmd} renvoyée en préparation avec succès.")
            return redirect('commande:detail', commande_id=commande.id)
            
    except Exception as e:
        messages.error(request, f"Erreur lors du renvoi en préparation : {str(e)}")
        return redirect('app_admin:sav_commandes_retournees')

# ============================================================================
# VUES DE RÉPARTITION DES COMMANDES (DÉPLACÉES DEPUIS PREPACOMMANDE)
# ============================================================================

@staff_member_required
@login_required
def repartition_automatique(request):
    """Gestion de la répartition automatique des commandes - Interface Admin"""
    from parametre.models import Region, Ville, Operateur
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.db.models import Count, Sum
    from django.utils import timezone
    from datetime import timedelta
    
    # Obtenir les données pour les filtres
    regions = Region.objects.all()
    villes = Ville.objects.all()
    operateurs_confirmation = Operateur.objects.filter(type_operateur='CONFIRMATION', actif=True)
    
    # Commandes confirmées et en cours de traitement (qui arrivent de l'interface des opérateurs de confirmation)
    # Inclure: Confirmée, À imprimer, Préparée - toutes sont des commandes en attente de répartition/livraison
    commandes_confirmees = Commande.objects.filter(
        etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée"],
        etats__date_fin__isnull=True,
        ville__isnull=False,  # Exclure les commandes sans ville
        ville__region__isnull=False  # Exclure les commandes sans région
    ).select_related('ville', 'ville__region', 'client').prefetch_related('etats__operateur').distinct()
    
    # Commandes en cours de livraison (déjà réparties automatiquement)
    commandes_en_livraison = Commande.objects.filter(
        etats__enum_etat__libelle="En cours de livraison",
        etats__date_fin__isnull=True
    ).select_related('ville', 'ville__region', 'client').prefetch_related('etats__operateur').distinct()
    
    # Statistiques par région pour les commandes confirmées (en attente de répartition)
    stats_par_region_confirmees = commandes_confirmees.values(
        'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('ville__region__nom_region')
    
    # Statistiques par ville pour les commandes confirmées
    stats_par_ville_confirmees = commandes_confirmees.values(
        'ville__id', 'ville__nom', 'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('ville__region__nom_region', 'ville__nom')
    
    # Statistiques par région pour les commandes en livraison (déjà réparties)
    stats_par_region_livraison = commandes_en_livraison.values(
        'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('ville__region__nom_region')
    
    # Statistiques par ville pour les commandes en livraison
    stats_par_ville_livraison = commandes_en_livraison.values(
        'ville__id', 'ville__nom', 'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('ville__region__nom_region', 'ville__nom')
    
    # Statistiques des commandes PRÉPARÉES par région
    commandes_preparees = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_fin__isnull=True,
        ville__isnull=False,
        ville__region__isnull=False
    ).select_related('ville', 'ville__region')
    
    stats_preparees_par_region = commandes_preparees.values(
        'ville__region__nom_region'
    ).annotate(
        nb_commandes_preparees=Count('id')
    ).order_by('ville__region__nom_region')
    
    # Statistiques des commandes PRÉPARÉES par ville
    stats_preparees_par_ville = commandes_preparees.values(
        'ville__nom', 'ville__region__nom_region'
    ).annotate(
        nb_commandes_preparees=Count('id')
    ).order_by('ville__region__nom_region', 'ville__nom')
    
    # Créer des dictionnaires pour un accès rapide
    preparees_par_region = {stat['ville__region__nom_region']: stat['nb_commandes_preparees'] for stat in stats_preparees_par_region}
    preparees_par_ville = {(stat['ville__nom'], stat['ville__region__nom_region']): stat['nb_commandes_preparees'] for stat in stats_preparees_par_ville}
    
    # Calculer les totaux
    total_commandes_confirmees = commandes_confirmees.count()
    total_commandes_en_livraison = commandes_en_livraison.count()
    total_montant_confirmees = commandes_confirmees.aggregate(total=Sum('total_cmd'))['total'] or 0
    total_montant_livraison = commandes_en_livraison.aggregate(total=Sum('total_cmd'))['total'] or 0
    
    # Calculer le total des commandes préparées
    total_commandes_preparees = sum(preparees_par_region.values())
    
    # Statistiques générales
    operateurs_disponibles = operateurs_confirmation.count()
    regions_actives = regions.count()
    villes_actives = villes.count()
    
    # Historique des répartitions récentes (basé sur les changements d'état)
    historique_repartitions = []
    
    # Récupérer les changements d'état récents vers "En cours de livraison"
    changements_recents = EtatCommande.objects.filter(
        enum_etat__libelle='En cours de livraison',
        date_debut__gte=timezone.now() - timedelta(days=7)
    ).select_related('commande__ville__region', 'operateur').order_by('-date_debut')[:20]
    
    for changement in changements_recents:
        # Compter les commandes réparties dans cette session
        commandes_reparties = EtatCommande.objects.filter(
            enum_etat__libelle='En cours de livraison',
            date_debut__date=changement.date_debut.date(),
            operateur=changement.operateur
        ).count()
        
        historique_repartitions.append({
            'id': changement.id,
            'date_creation': changement.date_debut,
            'operateur': changement.operateur,
            'nom_operateur': get_operateur_display_name(changement.operateur),
            'region': changement.commande.ville.region if changement.commande.ville else None,
            'nb_commandes': commandes_reparties,
            'statut': 'TERMINE'
        })
    
    # Éviter les doublons dans l'historique
    historique_repartitions = list({item['date_creation'].date(): item for item in historique_repartitions}.values())
    historique_repartitions.sort(key=lambda x: x['date_creation'], reverse=True)
    
    # Préparer les commandes confirmées avec les noms d'opérateurs
    commandes_confirmees_list = []
    for commande in commandes_confirmees[:10]:  # Limiter aux 10 plus récentes
        etat_confirmation = commande.etats.filter(enum_etat__libelle='Confirmée', date_fin__isnull=True).first()
        if etat_confirmation:
            commandes_confirmees_list.append({
                'commande': commande,
                'nom_operateur': get_operateur_display_name(etat_confirmation.operateur),
                'date_confirmation': etat_confirmation.date_debut
            })
    
    # Générer automatiquement les données de prévisualisation pour afficher les répartitions
    preview_data = generer_preview_repartition_automatique(
        commandes_confirmees, operateurs_confirmation, 10, True, True
    )
    
    if request.method == 'POST':
        action = request.POST.get('action')
        region_id = request.POST.get('region')
        ville_id = request.POST.get('ville')
        max_commandes = int(request.POST.get('max_commandes', 10))
        equilibrer_charge = request.POST.get('equilibrer_charge') == 'on'
        prioriser_proximite = request.POST.get('prioriser_proximite') == 'on'
        
        # Filtrer les commandes selon les critères
        queryset = commandes_confirmees
        if region_id:
            queryset = queryset.filter(ville__region_id=region_id)
        if ville_id:
            queryset = queryset.filter(ville_id=ville_id)
        
        commandes = list(queryset[:max_commandes * operateurs_disponibles])
        
        if action == 'preview':
            # Générer la prévisualisation
            preview_data = generer_preview_repartition(
                commandes, operateurs_confirmation, max_commandes, 
                equilibrer_charge, prioriser_proximite
            )
        elif action == 'execute':
            # Exécuter la répartition
            resultat = executer_repartition(
                commandes, operateurs_confirmation, max_commandes,
                equilibrer_charge, prioriser_proximite, request.user
            )
            if resultat['success']:
                messages.success(request, f"Répartition réussie : {resultat['commandes_reparties']} commandes réparties")
                return redirect('app_admin:repartition_automatique')
            else:
                messages.error(request, f"Erreur lors de la répartition : {resultat['error']}")
    
    context = {
        'total_commandes': total_commandes_confirmees,
        'total_commandes_en_livraison': total_commandes_en_livraison,
        'total_montant_confirmees': total_montant_confirmees,
        'total_montant_livraison': total_montant_livraison,
        'total_commandes_preparees': total_commandes_preparees,
        'operateurs_disponibles': operateurs_disponibles,
        'regions_actives': regions_actives,
        'villes_actives': villes_actives,
        'regions': regions,
        'villes': villes,
        'preview_data': preview_data,
        'historique_repartitions': historique_repartitions,
        # Statistiques pour les commandes confirmées (en attente)
        'stats_par_region': stats_par_region_confirmees,
        'stats_par_ville': stats_par_ville_confirmees,
        'total_commandes_reparties': total_commandes_en_livraison,
        # Statistiques pour les commandes en livraison (déjà réparties)
        'stats_par_region_livraison': stats_par_region_livraison,
        'stats_par_ville_livraison': stats_par_ville_livraison,
            # Statistiques des commandes préparées
    'preparees_par_region': preparees_par_region,
    'preparees_par_ville': preparees_par_ville,
    'commandes_confirmees': commandes_confirmees,
    'commandes_confirmees_list': commandes_confirmees_list,
    'commandes_en_livraison': commandes_en_livraison,
    # Données de répartition automatique
    'repartition_par_operateur': preview_data,
    }
    
    return render(request, 'parametre/repartition_automatique.html', context)

def get_operateur_display_name(operateur):
    """Fonction utilitaire pour obtenir le nom d'affichage d'un opérateur"""
    if operateur:
        return f"{operateur.prenom} {operateur.nom}"
    return "Opérateur inconnu"

def generer_preview_repartition_automatique(commandes, operateurs, max_commandes, equilibrer_charge, prioriser_proximite):
    """Générer automatiquement une prévisualisation de la répartition par région et opération"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.db.models import Count, Q
    
    preview = {}
    
    # Grouper les commandes par région
    commandes_par_region = {}
    for commande in commandes:
        if commande.ville and commande.ville.region:
            region_nom = commande.ville.region.nom_region
            if region_nom not in commandes_par_region:
                commandes_par_region[region_nom] = []
            commandes_par_region[region_nom].append(commande)
    
    # Répartir les commandes par opérateur selon les régions
    operateurs_list = list(operateurs)
    operateur_index = 0
    
    for region_nom, commandes_region in commandes_par_region.items():
        # Répartir les commandes de cette région entre les opérateurs
        commandes_par_operateur = len(commandes_region) // len(operateurs_list) if operateurs_list else 0
        reste = len(commandes_region) % len(operateurs_list) if operateurs_list else 0
        
        for i, operateur in enumerate(operateurs_list):
            if operateur.id not in preview:
                preview[operateur.id] = {
                    'operateur': operateur,
                    'nom_operateur': get_operateur_display_name(operateur),
                    'commandes': [],
                    'nb_commandes': 0,
                    'regions': set()
                }
            
            # Calculer le nombre de commandes pour cet opérateur
            nb_commandes_operateur = commandes_par_operateur
            if i < reste:
                nb_commandes_operateur += 1
            
            # Prendre les commandes pour cet opérateur
            start_index = i * commandes_par_operateur + min(i, reste)
            end_index = start_index + nb_commandes_operateur
            
            commandes_operateur = commandes_region[start_index:end_index]
            
            # Ajouter les commandes à l'opérateur
            preview[operateur.id]['commandes'].extend(commandes_operateur)
            preview[operateur.id]['nb_commandes'] += len(commandes_operateur)
            preview[operateur.id]['regions'].add(region_nom)
    
    # Mettre à jour le nombre total de commandes pour chaque opérateur
    for operateur_id in preview:
        preview[operateur_id]['nb_commandes'] = len(preview[operateur_id]['commandes'])
        preview[operateur_id]['regions'] = list(preview[operateur_id]['regions'])
    
    return preview

def generer_preview_repartition(commandes, operateurs, max_commandes, equilibrer_charge, prioriser_proximite):
    """Générer une prévisualisation de la répartition"""
    preview = {}
    commandes_par_operateur = max_commandes
    
    if equilibrer_charge:
        total_commandes = len(commandes)
        nb_operateurs = len(operateurs)
        if nb_operateurs > 0:
            commandes_par_operateur = total_commandes // nb_operateurs
    
    for operateur in operateurs:
        preview[operateur.id] = {
            'operateur': operateur,
            'nom_operateur': get_operateur_display_name(operateur),
            'commandes': commandes[:commandes_par_operateur],
            'nb_commandes': min(len(commandes), commandes_par_operateur)
        }
        commandes = commandes[commandes_par_operateur:]
    
    return preview

def executer_repartition(commandes, operateurs, max_commandes, equilibrer_charge, prioriser_proximite, user):
    """Exécuter la répartition des commandes"""
    from commande.models import EtatCommande, EnumEtatCmd
    from django.db import transaction
    from django.utils import timezone
    
    try:
        with transaction.atomic():
            preview_data = generer_preview_repartition(commandes, operateurs, max_commandes, equilibrer_charge, prioriser_proximite)
            
            # Obtenir l'état "En cours de livraison"
            enum_etat_livraison = EnumEtatCmd.objects.get(libelle='En cours de livraison')
            
            commandes_reparties = 0
            
            for operateur_id, data in preview_data.items():
                operateur = data['operateur']
                
                for commande in data['commandes']:
                    # Fermer l'état actuel de la commande
                    etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
                    if etat_actuel:
                        etat_actuel.date_fin = timezone.now()
                        etat_actuel.save()
                    
                    # Créer le nouvel état "En cours de livraison"
                    EtatCommande.objects.create(
                        commande=commande,
                        enum_etat=enum_etat_livraison,
                        operateur=operateur,
                        date_debut=timezone.now(),
                        commentaire=f"Répartie automatiquement par {get_operateur_display_name(user.profil_operateur)}"
                    )
                    
                    commandes_reparties += 1
            
            return {
                'success': True,
                'commandes_reparties': commandes_reparties,
                'message': f"{commandes_reparties} commandes réparties avec succès"
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# === VUE RÉPARTITION MANUELLE SUPPRIMÉE ===
# La répartition manuelle a été supprimée car le système gère maintenant
# la répartition de manière intelligente, automatique et dynamique

@staff_member_required
@login_required
def details_region_view(request):
    """Vue détaillée par région pour la répartition - Interface Admin"""
    from parametre.models import Region, Ville, Operateur
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.db.models import Count, Sum
    from django.utils import timezone
    import csv
    
    # Obtenir les régions
    regions = Region.objects.all()
    
    # Commandes préparées uniquement (pour les exportations)
    commandes_preparees = Commande.objects.filter(
        etats__enum_etat__libelle="Préparée",
        etats__date_fin__isnull=True,
        ville__isnull=False,
        ville__region__isnull=False
    ).distinct()
    
    # Debug: Vérifier les états disponibles
    etats_disponibles = EnumEtatCmd.objects.values_list('libelle', flat=True)
    print(f"États disponibles: {list(etats_disponibles)}")
    print(f"Nombre de commandes préparées trouvées: {commandes_preparees.count()}")
    
    # Statistiques par région (toutes les commandes confirmées/préparées)
    stats_par_region = Commande.objects.filter(
        etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée", "En préparation"],
        etats__date_fin__isnull=True,
        ville__isnull=False,
        ville__region__isnull=False
    ).values(
        'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('ville__region__nom_region')
    
    print(f"Nombre de régions avec des statistiques: {stats_par_region.count()}")
    for stat in stats_par_region:
        print(f"Région {stat['ville__region__nom_region']}: {stat['nb_commandes']} commandes")
    
    # Debug: Vérifier toutes les commandes avec leurs états
    toutes_commandes = Commande.objects.filter(
        ville__isnull=False,
        ville__region__isnull=False
    ).prefetch_related('etats__enum_etat')[:10]
    
    print("=== DEBUG: 10 premières commandes avec leurs états ===")
    for cmd in toutes_commandes:
        etat_actuel = cmd.etats.filter(date_fin__isnull=True).first()
        print(f"Commande {cmd.id}: {cmd.ville.region.nom_region if cmd.ville and cmd.ville.region else 'N/A'} - État: {etat_actuel.enum_etat.libelle if etat_actuel else 'Aucun état'}")
    
    # Statistiques par ville (toutes les commandes confirmées/préparées)
    stats_par_ville = Commande.objects.filter(
        etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée", "En préparation"],
        etats__date_fin__isnull=True,
        ville__isnull=False,
        ville__region__isnull=False
    ).values(
        'ville__id', 'ville__nom', 'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('ville__region__nom_region', 'ville__nom')
    
    # Calculer les totaux
    total_commandes = sum(stat['nb_commandes'] for stat in stats_par_region)
    total_montant = sum(stat['total_montant'] for stat in stats_par_region)
    
    # Gestion des exportations
    export_type = request.GET.get('export')
    region_filter = request.GET.get('region')
    
    if export_type and commandes_preparees.exists():
        if export_type == 'csv_region':
            return export_stats_region_csv(stats_par_region)
        elif export_type == 'excel_region' and OPENPYXL_AVAILABLE:
            return export_stats_region_excel(stats_par_region)
        elif export_type == 'csv_region_detail' and region_filter:
            return export_region_detail_csv(region_filter)
        elif export_type == 'excel_region_detail' and region_filter and OPENPYXL_AVAILABLE:
            return export_region_detail_excel(region_filter)
        elif export_type == 'csv_ville':
            return export_stats_ville_csv(stats_par_ville)
        elif export_type == 'excel_ville' and OPENPYXL_AVAILABLE:
            return export_stats_ville_excel(stats_par_ville)
        elif export_type == 'csv_combine':
            return export_stats_combine_csv(stats_par_region, stats_par_ville)
        elif export_type == 'excel_combine' and OPENPYXL_AVAILABLE:
            return export_stats_combine_excel(stats_par_region, stats_par_ville)
    
    # Calculer les données pour les modales
    # Top 10 des villes
    top_10_villes = stats_par_ville.order_by('-nb_commandes')[:10]
    
    # Répartition par région (pourcentage)
    total_commandes_calc = sum(stat['nb_commandes'] for stat in stats_par_region)
    stats_region_avec_pourcentage = []
    for stat in stats_par_region:
        pourcentage = (stat['nb_commandes'] / total_commandes_calc * 100) if total_commandes_calc > 0 else 0
        stats_region_avec_pourcentage.append({
            'region': stat['ville__region__nom_region'],
            'nb_commandes': stat['nb_commandes'],
            'total_montant': stat['total_montant'],
            'pourcentage': round(pourcentage, 1)
        })
    
    # Statistiques globales pour les modales
    stats_globales = {
        'total_commandes': total_commandes,
        'total_montant': total_montant,
        'nb_regions_actives': len(stats_par_region),
        'nb_villes_actives': len(stats_par_ville),
        'moyenne_commandes_par_region': round(total_commandes / len(stats_par_region), 1) if stats_par_region else 0,
        'moyenne_commandes_par_ville': round(total_commandes / len(stats_par_ville), 1) if stats_par_ville else 0,
    }
    
    context = {
        'regions': regions,
        'stats_par_region': stats_par_region,
        'stats_par_ville': stats_par_ville,
        'total_commandes': total_commandes,
        'total_montant': total_montant,
        'commandes_preparees_exist': commandes_preparees.exists(),
        'openpyxl_available': OPENPYXL_AVAILABLE,
        # Données pour les modales
        'top_10_villes': top_10_villes,
        'stats_region_avec_pourcentage': stats_region_avec_pourcentage,
        'stats_globales': stats_globales,
    }
    
    return render(request, 'parametre/details_region.html', context)

@staff_member_required
@login_required
def get_modal_data_ajax(request):
    """Vue AJAX pour récupérer les données des modales en temps réel"""
    from parametre.models import Region, Ville, Operateur
    from commande.models import Commande, EtatCommande, EnumEtatCmd
    from django.db.models import Count, Sum
    from django.utils import timezone
    import json
    
    # Récupérer les mêmes données que dans details_region_view
    stats_par_region = Commande.objects.filter(
        etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée", "En préparation"],
        etats__date_fin__isnull=True,
        ville__isnull=False,
        ville__region__isnull=False
    ).values(
        'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('ville__region__nom_region')
    
    stats_par_ville = Commande.objects.filter(
        etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée", "En préparation"],
        etats__date_fin__isnull=True,
        ville__isnull=False,
        ville__region__isnull=False
    ).values(
        'ville__id', 'ville__nom', 'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('ville__region__nom_region', 'ville__nom')
    
    # Calculer les totaux
    total_commandes = sum(stat['nb_commandes'] for stat in stats_par_region)
    total_montant = sum(stat['total_montant'] for stat in stats_par_region)
    
    # Top 10 des villes
    top_10_villes = list(stats_par_ville.order_by('-nb_commandes')[:10])
    
    # Répartition par région (pourcentage)
    total_commandes_calc = sum(stat['nb_commandes'] for stat in stats_par_region)
    stats_region_avec_pourcentage = []
    for stat in stats_par_region:
        pourcentage = (stat['nb_commandes'] / total_commandes_calc * 100) if total_commandes_calc > 0 else 0
        stats_region_avec_pourcentage.append({
            'region': stat['ville__region__nom_region'],
            'nb_commandes': stat['nb_commandes'],
            'total_montant': float(stat['total_montant']) if stat['total_montant'] else 0,
            'pourcentage': round(pourcentage, 1)
        })
    
    # Statistiques globales
    stats_globales = {
        'total_commandes': total_commandes,
        'total_montant': float(total_montant) if total_montant else 0,
        'nb_regions_actives': len(stats_par_region),
        'nb_villes_actives': len(stats_par_ville),
        'moyenne_commandes_par_region': round(total_commandes / len(stats_par_region), 1) if stats_par_region else 0,
        'moyenne_commandes_par_ville': round(total_commandes / len(stats_par_ville), 1) if stats_par_ville else 0,
        'derniere_mise_a_jour': timezone.now().strftime('%d/%m/%Y à %H:%M')
    }
    
    data = {
        'top_10_villes': top_10_villes,
        'stats_region_avec_pourcentage': stats_region_avec_pourcentage,
        'stats_globales': stats_globales,
        'success': True
    }
    
    return JsonResponse(data)

# Vues de recherche globale
@staff_member_required
@login_required
def global_search_view(request):
    """Vue principale pour la barre de recherche globale"""
    return render(request, 'parametre/dashboard_360/barre_recherche_globale/global_search.html')


@staff_member_required
@login_required
def global_search_api(request):
    """API pour la recherche globale en temps réel"""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', 'all')
    
    if not query or len(query) < 2:
        return JsonResponse({
            'success': False,
            'message': 'Requête trop courte',
            'results': []
        })
    
    results = {
        'commandes': [],
        'operateurs': [],
        'regions': [],
        'villes': [],
        'articles': [],
        'statistiques': []
    }
    
    try:
        # Recherche dans les commandes
        if category in ['all', 'commandes']:
            results['commandes'] = search_commandes_global(query)
        
        # Recherche dans les opérateurs
        if category in ['all', 'operateurs']:
            results['operateurs'] = search_operateurs_global(query)
        
        # Recherche dans les régions
        if category in ['all', 'regions']:
            results['regions'] = search_regions_global(query)
        
        # Recherche dans les villes
        if category in ['all', 'villes']:
            results['villes'] = search_villes_global(query)
        
        # Recherche dans les articles
        if category in ['all', 'articles']:
            results['articles'] = search_articles_global(query)
        
        # Recherche dans les statistiques
        if category in ['all', 'statistiques']:
            results['statistiques'] = search_statistiques_global(query)
        
        return JsonResponse({
            'success': True,
            'query': query,
            'results': results,
            'total_results': sum(len(v) for v in results.values())
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Erreur lors de la recherche: {str(e)}',
            'results': []
        })


def search_commandes_global(query):
    """Recherche avancée dans les commandes"""
    commandes = []
    
    # Recherche par ID exact
    if query.isdigit():
        try:
            cmd = Commande.objects.get(id=int(query))
            commandes.append({
                'id': cmd.id,
                'type': 'commande',
                'title': f'Commande #{cmd.id}',
                'subtitle': f'Client: {cmd.client.nom if cmd.client else "N/A"} - {cmd.total_cmd} DH',
                'status': get_commande_status_global(cmd),
                'url': f'/commande/detail/{cmd.id}/',
                'icon': 'fas fa-shopping-cart',
                'priority': 1,
                'highlight': 'ID exact'
            })
        except Commande.DoesNotExist:
            pass
    
    # Recherche par client (nom, prénom, email, téléphone)
    commandes_client = Commande.objects.filter(
        Q(client__nom__icontains=query) |
        Q(client__prenom__icontains=query) |
        Q(client__email__icontains=query) |
        Q(client__numero_tel__icontains=query) |
        Q(client__adresse__icontains=query)
    ).select_related('client', 'ville', 'ville__region')[:8]
    
    for cmd in commandes_client:
        commandes.append({
            'id': cmd.id,
            'type': 'commande',
            'title': f'Commande #{cmd.id}',
            'subtitle': f'Client: {cmd.client.nom} {cmd.client.prenom if cmd.client.prenom else ""} - {cmd.total_cmd} DH',
            'status': get_commande_status_global(cmd),
            'url': f'/commande/detail/{cmd.id}/',
            'icon': 'fas fa-shopping-cart',
            'priority': 2,
            'highlight': 'Client'
        })
    
    # Recherche par géographie (ville, région)
    commandes_geo = Commande.objects.filter(
        Q(ville__nom__icontains=query) |
        Q(ville__region__nom_region__icontains=query)
    ).select_related('client', 'ville', 'ville__region')[:8]
    
    for cmd in commandes_geo:
        commandes.append({
            'id': cmd.id,
            'type': 'commande',
            'title': f'Commande #{cmd.id}',
            'subtitle': f'{cmd.ville.nom} ({cmd.ville.region.nom_region}) - {cmd.total_cmd} DH',
            'status': get_commande_status_global(cmd),
            'url': f'/commande/detail/{cmd.id}/',
            'icon': 'fas fa-shopping-cart',
            'priority': 3,
            'highlight': 'Géographie'
        })
    
    # Recherche par montant et plages
    if any(keyword in query.lower() for keyword in ['dh', 'montant', 'prix', 'euro', '€']):
        try:
            import re
            montant_match = re.search(r'(\d+(?:[.,]\d+)?)', query)
            if montant_match:
                montant = float(montant_match.group(1).replace(',', '.'))
                commandes_montant = Commande.objects.filter(total_cmd__gte=montant)[:5]
                for cmd in commandes_montant:
                    commandes.append({
                        'id': cmd.id,
                        'type': 'commande',
                        'title': f'Commande #{cmd.id}',
                        'subtitle': f'Montant: {cmd.total_cmd} DH - {cmd.client.nom if cmd.client else "N/A"}',
                        'status': get_commande_status_global(cmd),
                        'url': f'/commande/detail/{cmd.id}/',
                        'icon': 'fas fa-shopping-cart',
                        'priority': 4,
                        'highlight': 'Montant'
                    })
        except:
            pass
    
    # Recherche par statut
    status_keywords = {
        'confirmée': 'Confirmée',
        'confirmé': 'Confirmée',
        'préparée': 'Préparée',
        'préparé': 'Préparée',
        'livrée': 'Livrée',
        'livré': 'Livrée',
        'annulée': 'Annulée',
        'annulé': 'Annulée',
        'nouvelle': 'Nouvelle',
        'en cours': 'En cours',
        'en preparation': 'En préparation'
    }
    
    for keyword, status in status_keywords.items():
        if keyword in query.lower():
            commandes_status = Commande.objects.filter(
                etats__enum_etat__libelle__icontains=status,
                etats__date_fin__isnull=True
            ).select_related('client', 'ville')[:5]
            
            for cmd in commandes_status:
                commandes.append({
                    'id': cmd.id,
                    'type': 'commande',
                    'title': f'Commande #{cmd.id}',
                    'subtitle': f'Statut: {status} - {cmd.client.nom if cmd.client else "N/A"}',
                    'status': get_commande_status_global(cmd),
                    'url': f'/commande/detail/{cmd.id}/',
                    'icon': 'fas fa-shopping-cart',
                    'priority': 5,
                    'highlight': 'Statut'
                })
            break
    
    # Recherche par date (aujourd'hui, cette semaine, ce mois)
    date_keywords = {
        'aujourd\'hui': timezone.now().date(),
        'hier': timezone.now().date() - timedelta(days=1),
        'cette semaine': timezone.now().date() - timedelta(days=7),
        'ce mois': timezone.now().date() - timedelta(days=30)
    }
    
    for keyword, date in date_keywords.items():
        if keyword in query.lower():
            commandes_date = Commande.objects.filter(
                date_cmd__date=date
            ).select_related('client', 'ville')[:5]
            
            for cmd in commandes_date:
                commandes.append({
                    'id': cmd.id,
                    'type': 'commande',
                    'title': f'Commande #{cmd.id}',
                    'subtitle': f'Date: {cmd.date_cmd.strftime("%d/%m/%Y")} - {cmd.client.nom if cmd.client else "N/A"}',
                    'status': get_commande_status_global(cmd),
                    'url': f'/commande/detail/{cmd.id}/',
                    'icon': 'fas fa-shopping-cart',
                    'priority': 6,
                    'highlight': 'Date'
                })
            break
    
    return commandes[:15]


def search_operateurs_global(query):
    """Recherche avancée dans les opérateurs"""
    operateurs = []
    
    # Recherche par nom/prénom/username/email
    operateurs_nom = Operateur.objects.filter(
        Q(user__first_name__icontains=query) |
        Q(user__last_name__icontains=query) |
        Q(user__username__icontains=query) |
        Q(user__email__icontains=query) |
        Q(nom__icontains=query) |
        Q(prenom__icontains=query) |
        Q(mail__icontains=query) |
        Q(telephone__icontains=query)
    ).select_related('user')[:8]
    
    for op in operateurs_nom:
        operateurs.append({
            'id': op.id,
            'type': 'operateur',
            'title': f'{op.user.first_name} {op.user.last_name}',
            'subtitle': f'{op.get_type_operateur_display()} - {op.region.nom_region if op.region else "N/A"}',
            'status': 'Actif' if op.actif else 'Inactif',
            'url': f'/parametre/operateurs/detail/{op.id}/',
            'icon': 'fas fa-user',
            'priority': 1,
            'highlight': 'Nom'
        })
    
    # Recherche par type d'opérateur
    type_keywords = {
        'preparation': 'PRÉPARATION',
        'préparation': 'PRÉPARATION',
        'logistique': 'LOGISTIQUE',
        'confirmation': 'CONFIRMATION',
        'admin': 'ADMIN',
        'administrateur': 'ADMIN'
    }
    
    for keyword, type_op in type_keywords.items():
        if keyword in query.lower():
            operateurs_type = Operateur.objects.filter(type_operateur=type_op).select_related('user', 'region')[:5]
            for op in operateurs_type:
                operateurs.append({
                    'id': op.id,
                    'type': 'operateur',
                    'title': f'{op.user.first_name} {op.user.last_name}',
                    'subtitle': f'{op.get_type_operateur_display()} - {op.region.nom_region if op.region else "N/A"}',
                    'status': 'Actif' if op.actif else 'Inactif',
                    'url': f'/parametre/operateurs/detail/{op.id}/',
                    'icon': 'fas fa-user',
                    'priority': 2,
                    'highlight': 'Type'
                })
            break
    
    # Recherche par statut (actif/inactif)
    if 'actif' in query.lower():
        operateurs_actifs = Operateur.objects.filter(actif=True).select_related('user', 'region')[:5]
        for op in operateurs_actifs:
            operateurs.append({
                'id': op.id,
                'type': 'operateur',
                'title': f'{op.user.first_name} {op.user.last_name}',
                'subtitle': f'{op.get_type_operateur_display()} - {op.region.nom_region if op.region else "N/A"}',
                'status': 'Actif',
                'url': f'/parametre/operateurs/detail/{op.id}/',
                'icon': 'fas fa-user',
                'priority': 3,
                'highlight': 'Actif'
            })
    elif 'inactif' in query.lower():
        operateurs_inactifs = Operateur.objects.filter(actif=False).select_related('user', 'region')[:5]
        for op in operateurs_inactifs:
            operateurs.append({
                'id': op.id,
                'type': 'operateur',
                'title': f'{op.user.first_name} {op.user.last_name}',
                'subtitle': f'{op.get_type_operateur_display()} - {op.region.nom_region if op.region else "N/A"}',
                'status': 'Inactif',
                'url': f'/parametre/operateurs/detail/{op.id}/',
                'icon': 'fas fa-user',
                'priority': 3,
                'highlight': 'Inactif'
            })
    
    return operateurs[:12]


def search_regions_global(query):
    """Recherche avancée dans les régions"""
    regions = []
    
    # Recherche par nom de région
    regions_match = Region.objects.filter(
        Q(nom_region__icontains=query)
    )[:8]
    
    for region in regions_match:
        # Compter les commandes de cette région
        nb_commandes = Commande.objects.filter(
            ville__region=region,
            etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée", "En préparation"],
            etats__date_fin__isnull=True
        ).count()
        
        # Calculer le montant total
        total_montant = Commande.objects.filter(
            ville__region=region,
            etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée", "En préparation"],
            etats__date_fin__isnull=True
        ).aggregate(total=Sum('total_cmd'))['total'] or 0
        
        regions.append({
            'id': region.id,
            'type': 'region',
            'title': region.nom_region,
            'subtitle': f'{nb_commandes} commandes - {total_montant:,.0f} DH',
            'status': 'Active' if nb_commandes > 0 else 'Inactive',
            'url': f'/parametre/repartition/details-region/?region={region.nom_region}',
            'icon': 'fas fa-map',
            'priority': 1,
            'highlight': 'Région'
        })
    
    return regions


def search_villes_global(query):
    """Recherche avancée dans les villes"""
    villes = []
    
    # Recherche par nom de ville ou région
    villes_match = Ville.objects.filter(
        Q(nom__icontains=query) |
        Q(region__nom_region__icontains=query)
    ).select_related('region')[:8]
    
    for ville in villes_match:
        # Compter les commandes de cette ville
        nb_commandes = Commande.objects.filter(
            ville=ville,
            etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée", "En préparation"],
            etats__date_fin__isnull=True
        ).count()
        
        # Calculer le montant total
        total_montant = Commande.objects.filter(
            ville=ville,
            etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée", "En préparation"],
            etats__date_fin__isnull=True
        ).aggregate(total=Sum('total_cmd'))['total'] or 0
        
        villes.append({
            'id': ville.id,
            'type': 'ville',
            'title': ville.nom,
            'subtitle': f'{ville.region.nom_region} - {nb_commandes} commandes - {total_montant:,.0f} DH',
            'status': 'Active' if nb_commandes > 0 else 'Inactive',
            'url': f'/parametre/repartition/details-region/?ville={ville.nom}',
            'icon': 'fas fa-map-marker-alt',
            'priority': 1,
            'highlight': 'Ville'
        })
    
    return villes


def search_articles_global(query):
    """Recherche avancée dans les articles"""
    articles = []
    
    # Recherche par nom, référence, description
    articles_match = Article.objects.filter(
        Q(nom__icontains=query) |
        Q(reference__icontains=query) |
        Q(description__icontains=query) |
        Q(categorie__icontains=query)
    )[:8]
    
    for article in articles_match:
        articles.append({
            'id': article.id,
            'type': 'article',
            'title': article.nom,
            'subtitle': f'Réf: {article.reference} - Stock: {article.qte_disponible} - {article.prix_unitaire} DH',
            'status': 'En stock' if article.qte_disponible > 0 else 'Rupture',
            'url': f'/article/detail/{article.id}/',
            'icon': 'fas fa-box',
            'priority': 1,
            'highlight': 'Article'
        })
    
    # Recherche par stock (faible, rupture, disponible)
    if 'stock faible' in query.lower() or 'rupture' in query.lower():
        articles_stock = Article.objects.filter(qte_disponible__lte=10).order_by('qte_disponible')[:5]
        for article in articles_stock:
            articles.append({
                'id': article.id,
                'type': 'article',
                'title': article.nom,
                'subtitle': f'Stock faible: {article.qte_disponible} unités - {article.prix_unitaire} DH',
                'status': 'Stock faible' if article.qte_disponible > 0 else 'Rupture',
                'url': f'/article/detail/{article.id}/',
                'icon': 'fas fa-box',
                'priority': 2,
                'highlight': 'Stock'
            })
    
    # Recherche par prix
    if any(keyword in query.lower() for keyword in ['prix', 'montant', 'dh', 'euro', '€']):
        try:
            import re
            prix_match = re.search(r'(\d+(?:[.,]\d+)?)', query)
            if prix_match:
                prix = float(prix_match.group(1).replace(',', '.'))
                articles_prix = Article.objects.filter(prix_unitaire__gte=prix).order_by('prix_unitaire')[:5]
                for article in articles_prix:
                    articles.append({
                        'id': article.id,
                        'type': 'article',
                        'title': article.nom,
                        'subtitle': f'Prix: {article.prix_unitaire} DH - Stock: {article.qte_disponible}',
                        'status': 'En stock' if article.qte_disponible > 0 else 'Rupture',
                        'url': f'/article/detail/{article.id}/',
                        'icon': 'fas fa-box',
                        'priority': 3,
                        'highlight': 'Prix'
                    })
        except:
            pass
    
    return articles[:12]


def search_statistiques_global(query):
    """Recherche avancée dans les statistiques et fonctionnalités"""
    statistiques = []
    
    # Recherche par mots-clés statistiques étendus
    keywords = {
        'kpi': {'title': 'Dashboard KPIs', 'url': '/kpis/', 'icon': 'fas fa-chart-line', 'category': 'Analytics'},
        'performance': {'title': 'Performance Opérateurs', 'url': '/kpis/#performance-operateurs', 'icon': 'fas fa-chart-bar', 'category': 'Analytics'},
        'statistiques': {'title': 'Statistiques par Région', 'url': '/parametre/repartition/details-region/', 'icon': 'fas fa-chart-pie', 'category': 'Analytics'},
        'export': {'title': 'Exports disponibles', 'url': '/parametre/repartition/details-region/', 'icon': 'fas fa-file-export', 'category': 'Données'},
                'repartition': {'title': 'Répartition Automatique', 'url': '/parametre/repartition/automatique/', 'icon': 'fas fa-random', 'category': 'Gestion'},
        'sav': {'title': 'Service Après-Vente', 'url': '/parametre/sav/commandes-retournees/', 'icon': 'fas fa-tools', 'category': 'Support'},
        'synchronisation': {'title': 'Gestion de Synchronisation', 'url': '/synchronisation/dashboard/', 'icon': 'fas fa-sync', 'category': 'Système'},
        'sync': {'title': 'Synchronisation', 'url': '/synchronisation/dashboard/', 'icon': 'fas fa-sync', 'category': 'Système'},
        'sync logs': {'title': 'Logs de Synchronisation', 'url': '/synchronisation/logs/', 'icon': 'fas fa-file-alt', 'category': 'Système'},
        'sync config': {'title': 'Configuration Sync', 'url': '/synchronisation/dashboard/', 'icon': 'fas fa-cog', 'category': 'Système'},
        'gestion sync': {'title': 'Gestion Synchronisation', 'url': '/synchronisation/dashboard/', 'icon': 'fas fa-sync', 'category': 'Système'},
        'configuration': {'title': 'Configuration', 'url': '/parametre/', 'icon': 'fas fa-cog', 'category': 'Système'},
        'dashboard': {'title': 'Dashboard principal', 'url': '/kpis/', 'icon': 'fas fa-tachometer-alt', 'category': 'Analytics'},
        'rapport': {'title': 'Rapports', 'url': '/parametre/repartition/details-region/', 'icon': 'fas fa-file-chart-line', 'category': 'Données'},
        'analyse': {'title': 'Analyses', 'url': '/kpis/', 'icon': 'fas fa-chart-line', 'category': 'Analytics'},
        'ventes': {'title': 'Statistiques de ventes', 'url': '/kpis/#ventes', 'icon': 'fas fa-chart-line', 'category': 'Analytics'},
        'commandes': {'title': 'Gestion des commandes', 'url': '/commande/', 'icon': 'fas fa-shopping-cart', 'category': 'Gestion'},
        'clients': {'title': 'Gestion des clients', 'url': '/client/', 'icon': 'fas fa-users', 'category': 'Gestion'},
        'articles': {'title': 'Gestion des articles', 'url': '/article/', 'icon': 'fas fa-box', 'category': 'Gestion'},
        'opérateurs': {'title': 'Gestion des opérateurs', 'url': '/parametre/operateurs/', 'icon': 'fas fa-user-cog', 'category': 'Gestion'},
        'régions': {'title': 'Gestion des régions', 'url': '/parametre/regions/', 'icon': 'fas fa-map', 'category': 'Gestion'},
        'villes': {'title': 'Gestion des villes', 'url': '/parametre/villes/', 'icon': 'fas fa-map-marker-alt', 'category': 'Gestion'},
        'utilisateurs': {'title': 'Gestion des utilisateurs', 'url': '/parametre/operateurs/', 'icon': 'fas fa-users-cog', 'category': 'Gestion'},
        'paramètres': {'title': 'Paramètres système', 'url': '/parametre/', 'icon': 'fas fa-cogs', 'category': 'Système'},
        'système': {'title': 'Configuration système', 'url': '/parametre/', 'icon': 'fas fa-server', 'category': 'Système'},
        'admin': {'title': 'Administration', 'url': '/parametre/', 'icon': 'fas fa-user-shield', 'category': 'Système'},
        'profil': {'title': 'Mon profil', 'url': '/parametre/profile/', 'icon': 'fas fa-user-circle', 'category': 'Utilisateur'},
        'mot de passe': {'title': 'Changer mot de passe', 'url': '/parametre/profile/changer-mot-de-passe/', 'icon': 'fas fa-key', 'category': 'Utilisateur'},
        'déconnexion': {'title': 'Se déconnecter', 'url': '/logout/', 'icon': 'fas fa-sign-out-alt', 'category': 'Utilisateur'},
        'aide': {'title': 'Aide et support', 'url': '#', 'icon': 'fas fa-question-circle', 'category': 'Support'},
        'support': {'title': 'Support technique', 'url': '#', 'icon': 'fas fa-headset', 'category': 'Support'},
        'documentation': {'title': 'Documentation', 'url': '#', 'icon': 'fas fa-book', 'category': 'Support'},
        'notifications': {'title': 'Notifications', 'url': '#', 'icon': 'fas fa-bell', 'category': 'Système'},
        'alertes': {'title': 'Alertes système', 'url': '#', 'icon': 'fas fa-exclamation-triangle', 'category': 'Système'},
        'erreurs': {'title': 'Logs d\'erreurs', 'url': '/synchronisation/logs/', 'icon': 'fas fa-exclamation-circle', 'category': 'Système'},
        'sauvegarde': {'title': 'Sauvegarde', 'url': '#', 'icon': 'fas fa-database', 'category': 'Système'},
        'restauration': {'title': 'Restauration', 'url': '#', 'icon': 'fas fa-undo', 'category': 'Système'},
        'mise à jour': {'title': 'Mises à jour', 'url': '#', 'icon': 'fas fa-download', 'category': 'Système'},
        'maintenance': {'title': 'Mode maintenance', 'url': '#', 'icon': 'fas fa-tools', 'category': 'Système'},
        'sécurité': {'title': 'Sécurité', 'url': '#', 'icon': 'fas fa-shield-alt', 'category': 'Système'},
        'audit': {'title': 'Audit', 'url': '#', 'icon': 'fas fa-clipboard-check', 'category': 'Système'},
        'historique': {'title': 'Historique', 'url': '#', 'icon': 'fas fa-history', 'category': 'Données'},
        'archives': {'title': 'Archives', 'url': '#', 'icon': 'fas fa-archive', 'category': 'Données'},
        'backup': {'title': 'Sauvegarde', 'url': '#', 'icon': 'fas fa-database', 'category': 'Système'},
        'restore': {'title': 'Restauration', 'url': '#', 'icon': 'fas fa-undo', 'category': 'Système'},
        'update': {'title': 'Mises à jour', 'url': '#', 'icon': 'fas fa-download', 'category': 'Système'},
        'maintenance': {'title': 'Mode maintenance', 'url': '#', 'icon': 'fas fa-tools', 'category': 'Système'},
        'security': {'title': 'Sécurité', 'url': '#', 'icon': 'fas fa-shield-alt', 'category': 'Système'},
        'audit': {'title': 'Audit', 'url': '#', 'icon': 'fas fa-clipboard-check', 'category': 'Système'},
        'history': {'title': 'Historique', 'url': '#', 'icon': 'fas fa-history', 'category': 'Données'},
        'archives': {'title': 'Archives', 'url': '#', 'icon': 'fas fa-archive', 'category': 'Données'},
    }
    
    for keyword, info in keywords.items():
        if keyword in query.lower():
            statistiques.append({
                'id': keyword,
                'type': 'statistique',
                'title': info['title'],
                'subtitle': f'{info["category"]} - Accès direct',
                'status': 'Disponible',
                'url': info['url'],
                'icon': info['icon'],
                'priority': 1,
                'highlight': info['category']
            })
    
    return statistiques


def get_commande_status_global(commande):
    """Obtenir le statut actuel d'une commande"""
    etat_actuel = commande.etats.filter(date_fin__isnull=True).first()
    if etat_actuel:
        return etat_actuel.enum_etat.libelle
    return "Nouvelle"


@staff_member_required
@login_required
def search_suggestions_api(request):
    """API améliorée pour les suggestions de recherche"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 1:
        return JsonResponse({'suggestions': []})
    
    suggestions = []
    
    # Suggestions basées sur l'historique et les tendances
    common_searches = [
        "commandes confirmées",
        "opérateurs préparation",
        "statistiques casablanca",
        "export excel",
        "stock faible",
        "sav commandes retournées",
        "performance opérateurs",
        "kpi ventes",
        "répartition automatique",
        "synchronisation",
        "gestion sync",
        "sync logs",
        "logs système",
        "configuration",
        "mon profil",
        "changer mot de passe",
        "aide support",
        "notifications",
        "alertes système",
        "sauvegarde",
        "mise à jour",
        "maintenance",
        "sécurité",
        "audit",
        "historique",
        "archives"
    ]
    
    for search in common_searches:
        if query.lower() in search.lower():
            suggestions.append({
                'text': search,
                'category': 'Recherche fréquente',
                'icon': 'fas fa-fire',
                'url': f'/parametre/recherche-globale/?q={search}', # URL générique pour recherche fréquente
                'isSuggestion': True
            })
    
    # Suggestions de commandes récentes
    recent_commandes = Commande.objects.order_by('-id')[:5]
    for cmd in recent_commandes:
        suggestions.append({
            'text': f"commande #{cmd.id}",
            'category': 'Commande récente',
            'icon': 'fas fa-shopping-cart',
            'url': f'/commande/detail/{cmd.id}/',
            'isSuggestion': True
        })
    
    # Suggestions de régions actives
    active_regions = Region.objects.annotate(
        nb_commandes=Count('villes__commandes', filter=Q(
            villes__commandes__etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée", "En préparation"],
            villes__commandes__etats__date_fin__isnull=True
        ))
    ).filter(nb_commandes__gt=0)[:5]
    
    for region in active_regions:
        suggestions.append({
            'text': f"statistiques {region.nom_region.lower()}",
            'category': 'Région active',
            'icon': 'fas fa-map',
            'url': f'/parametre/repartition/details-region/?region={region.nom_region}',
            'isSuggestion': True
        })
    
    # Suggestions d'opérateurs actifs
    active_operateurs = Operateur.objects.filter(actif=True)[:5]
    for op in active_operateurs:
        suggestions.append({
            'text': f"opérateur {op.user.first_name.lower()} {op.user.last_name.lower()}",
            'category': 'Opérateur actif',
            'icon': 'fas fa-user',
            'url': f'/parametre/operateurs/detail/{op.id}/',
            'isSuggestion': True
        })
    
    # Suggestions d'articles en stock faible
    low_stock_articles = Article.objects.filter(qte_disponible__lte=10)[:5]
    for article in low_stock_articles:
        suggestions.append({
            'text': f"article {article.nom.lower()}",
            'category': 'Stock faible',
            'icon': 'fas fa-box',
            'url': f'/article/detail/{article.id}/',
            'isSuggestion': True
        })
    
    # Suggestions spécifiques pour la synchronisation
    sync_suggestions = [
        {"text": "synchronisation", "url": "/synchronisation/dashboard/"},
        {"text": "gestion sync", "url": "/synchronisation/dashboard/"},
        {"text": "sync logs", "url": "/synchronisation/logs/"},
        {"text": "logs synchronisation", "url": "/synchronisation/logs/"},
        {"text": "configuration sync", "url": "/synchronisation/dashboard/"},
        {"text": "état synchronisation", "url": "/synchronisation/dashboard/"},
        {"text": "dashboard synchronisation", "url": "/synchronisation/dashboard/"}
    ]
    
    for sync_sugg in sync_suggestions:
        if query.lower() in sync_sugg["text"].lower():
            suggestions.append({
                'text': sync_sugg["text"],
                'category': 'Synchronisation',
                'icon': 'fas fa-sync',
                'url': sync_sugg["url"],
                'isSuggestion': True
            })
    
    # Suggestions de fonctionnalités (basées sur les mots-clés du search_statistiques_global)
    feature_keywords = {
        "dashboard kpis": "/kpis/",
        "performance opérateurs": "/kpis/#performance-operateurs",
        "statistiques par région": "/parametre/repartition/details-region/",
        "export données": "/parametre/repartition/details-region/",
        "répartition automatique": "/parametre/repartition/automatique/",
        "service après-vente": "/parametre/sav/commandes-retournees/",
        "synchronisation": "/synchronisation/dashboard/",
        "gestion sync": "/synchronisation/dashboard/",
        "sync logs": "/synchronisation/logs/",
        "logs système": "/synchronisation/logs/",
        "configuration": "/parametre/",
        "mon profil": "/parametre/profile/",
        "changer mot de passe": "/parametre/profile/changer-mot-de-passe/",
        "aide support": "#",
        "notifications": "#",
        "alertes système": "#",
        "sauvegarde": "#",
        "mise à jour": "#",
        "maintenance": "#",
        "sécurité": "#",
        "audit": "#",
        "historique": "#",
        "archives": "#",
    }
    
    for keyword, url in feature_keywords.items():
        if query.lower() in keyword.lower():
            suggestions.append({
                'text': keyword,
                'category': 'Fonctionnalité',
                'icon': 'fas fa-cog', # Icône générique pour les fonctionnalités
                'url': url,
                'isSuggestion': True
            })
    
    return JsonResponse({'suggestions': suggestions[:15]})

def export_stats_region_csv(stats_par_region):
    """Export CSV des statistiques par région"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="statistiques_par_region.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Région', 'Nombre de Commandes', 'Montant Total (DH)', 'Moyenne par Commande (DH)'])
    
    for stat in stats_par_region:
        moyenne = stat['total_montant'] / stat['nb_commandes'] if stat['nb_commandes'] > 0 else 0
        writer.writerow([
            stat['ville__region__nom_region'],
            stat['nb_commandes'],
            f"{stat['total_montant']:,.2f}",
            f"{moyenne:,.2f}"
        ])
    
    return response

def export_stats_region_excel(stats_par_region):
    """Export Excel des statistiques par région"""
    if not OPENPYXL_AVAILABLE:
        return HttpResponse("Export Excel non disponible - openpyxl non installé", status=400)
    
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Statistiques par Région"
    
    # Styles
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # En-têtes
    headers = ['Région', 'Nombre de Commandes', 'Montant Total (DH)', 'Moyenne par Commande (DH)']
    for col, header in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
    
    # Données
    for row, stat in enumerate(stats_par_region, 2):
        moyenne = stat['total_montant'] / stat['nb_commandes'] if stat['nb_commandes'] > 0 else 0
        
        worksheet.cell(row=row, column=1, value=stat['ville__region__nom_region']).border = border
        worksheet.cell(row=row, column=2, value=stat['nb_commandes']).border = border
        worksheet.cell(row=row, column=3, value=stat['total_montant']).border = border
        worksheet.cell(row=row, column=4, value=moyenne).border = border
    
    # Ajuster la largeur des colonnes
    worksheet.column_dimensions['A'].width = 25
    worksheet.column_dimensions['B'].width = 20
    worksheet.column_dimensions['C'].width = 20
    worksheet.column_dimensions['D'].width = 20
    
    # Sauvegarder
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="statistiques_par_region.xlsx"'
    return response

def export_stats_ville_csv(stats_par_ville):
    """Export CSV des statistiques par ville"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="statistiques_par_ville.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Ville', 'Région', 'Nombre de Commandes', 'Montant Total (DH)', 'Moyenne par Commande (DH)'])
    
    for stat in stats_par_ville:
        moyenne = stat['total_montant'] / stat['nb_commandes'] if stat['nb_commandes'] > 0 else 0
        writer.writerow([
            stat['ville__nom'],
            stat['ville__region__nom_region'],
            stat['nb_commandes'],
            f"{stat['total_montant']:,.2f}",
            f"{moyenne:,.2f}"
        ])
    
    return response

def export_stats_ville_excel(stats_par_ville):
    """Export Excel des statistiques par ville"""
    if not OPENPYXL_AVAILABLE:
        return HttpResponse("Export Excel non disponible - openpyxl non installé", status=400)
    
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "Statistiques par Ville"
    
    # Styles
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # En-têtes
    headers = ['Ville', 'Région', 'Nombre de Commandes', 'Montant Total (DH)', 'Moyenne par Commande (DH)']
    for col, header in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
    
    # Données
    for row, stat in enumerate(stats_par_ville, 2):
        moyenne = stat['total_montant'] / stat['nb_commandes'] if stat['nb_commandes'] > 0 else 0
        
        worksheet.cell(row=row, column=1, value=stat['ville__nom']).border = border
        worksheet.cell(row=row, column=2, value=stat['ville__region__nom_region']).border = border
        worksheet.cell(row=row, column=3, value=stat['nb_commandes']).border = border
        worksheet.cell(row=row, column=4, value=stat['total_montant']).border = border
        worksheet.cell(row=row, column=5, value=moyenne).border = border
    
    # Ajuster la largeur des colonnes
    worksheet.column_dimensions['A'].width = 20
    worksheet.column_dimensions['B'].width = 20
    worksheet.column_dimensions['C'].width = 18
    worksheet.column_dimensions['D'].width = 18
    worksheet.column_dimensions['E'].width = 18
    
    # Sauvegarder
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="statistiques_par_ville.xlsx"'
    return response

def export_stats_combine_csv(stats_par_region, stats_par_ville):
    """Export CSV combiné des statistiques par région et ville"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="statistiques_combinees.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Type', 'Nom', 'Région', 'Nombre de Commandes', 'Montant Total (DH)', 'Moyenne par Commande (DH)'])
    
    # Ajouter les données par région
    for stat in stats_par_region:
        moyenne = stat['total_montant'] / stat['nb_commandes'] if stat['nb_commandes'] > 0 else 0
        writer.writerow([
            'Région',
            stat['ville__region__nom_region'],
            stat['ville__region__nom_region'],
            stat['nb_commandes'],
            f"{stat['total_montant']:,.2f}",
            f"{moyenne:,.2f}"
        ])
    
    # Ajouter les données par ville
    for stat in stats_par_ville:
        moyenne = stat['total_montant'] / stat['nb_commandes'] if stat['nb_commandes'] > 0 else 0
        writer.writerow([
            'Ville',
            stat['ville__nom'],
            stat['ville__region__nom_region'],
            stat['nb_commandes'],
            f"{stat['total_montant']:,.2f}",
            f"{moyenne:,.2f}"
        ])
    
    return response

def export_stats_combine_excel(stats_par_region, stats_par_ville):
    """Export Excel combiné des statistiques par région et ville"""
    if not OPENPYXL_AVAILABLE:
        return HttpResponse("Export Excel non disponible - openpyxl non installé", status=400)
    
    workbook = Workbook()
    
    # Styles
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # Onglet Régions
    worksheet_regions = workbook.active
    worksheet_regions.title = "Par Région"
    
    headers = ['Région', 'Nombre de Commandes', 'Montant Total (DH)', 'Moyenne par Commande (DH)']
    for col, header in enumerate(headers, 1):
        cell = worksheet_regions.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
    
    for row, stat in enumerate(stats_par_region, 2):
        moyenne = stat['total_montant'] / stat['nb_commandes'] if stat['nb_commandes'] > 0 else 0
        
        worksheet_regions.cell(row=row, column=1, value=stat['ville__region__nom_region']).border = border
        worksheet_regions.cell(row=row, column=2, value=stat['nb_commandes']).border = border
        worksheet_regions.cell(row=row, column=3, value=stat['total_montant']).border = border
        worksheet_regions.cell(row=row, column=4, value=moyenne).border = border
    
    worksheet_regions.column_dimensions['A'].width = 25
    worksheet_regions.column_dimensions['B'].width = 20
    worksheet_regions.column_dimensions['C'].width = 20
    worksheet_regions.column_dimensions['D'].width = 20
    
    # Onglet Villes
    worksheet_villes = workbook.create_sheet("Par Ville")
    
    headers = ['Ville', 'Région', 'Nombre de Commandes', 'Montant Total (DH)', 'Moyenne par Commande (DH)']
    for col, header in enumerate(headers, 1):
        cell = worksheet_villes.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
    
    for row, stat in enumerate(stats_par_ville, 2):
        moyenne = stat['total_montant'] / stat['nb_commandes'] if stat['nb_commandes'] > 0 else 0
        
        worksheet_villes.cell(row=row, column=1, value=stat['ville__nom']).border = border
        worksheet_villes.cell(row=row, column=2, value=stat['ville__region__nom_region']).border = border
        worksheet_villes.cell(row=row, column=3, value=stat['nb_commandes']).border = border
        worksheet_villes.cell(row=row, column=4, value=stat['total_montant']).border = border
        worksheet_villes.cell(row=row, column=5, value=moyenne).border = border
    
    worksheet_villes.column_dimensions['A'].width = 20
    worksheet_villes.column_dimensions['B'].width = 20
    worksheet_villes.column_dimensions['C'].width = 18
    worksheet_villes.column_dimensions['D'].width = 18
    worksheet_villes.column_dimensions['E'].width = 18
    
    # Sauvegarder
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="statistiques_combinees.xlsx"'
    return response

def export_region_detail_csv(region_name):
    """Export CSV détaillé des commandes d'une région avec leurs paniers"""
    import csv
    from commande.models import Commande, Panier
    from article.models import Article
    
    # Récupérer toutes les commandes de la région avec leurs paniers
    commandes = Commande.objects.filter(
        ville__region__nom_region=region_name,
        etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée"],
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article').distinct()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="commandes_{region_name.lower()}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID Commande', 'Client', 'Ville', 'Région', 'Date Commande', 'Total Commande (DH)',
        'ID Panier', 'Article', 'Référence Article', 'Quantité', 'Prix Unitaire (DH)', 'Total Article (DH)'
    ])
    
    for commande in commandes:
        # Si la commande a des paniers
        if commande.paniers.exists():
            for i, panier in enumerate(commande.paniers.all()):
                if i == 0:
                    # Premier article - inclure les informations de commande
                    writer.writerow([
                        commande.id,
                        commande.client.nom if commande.client else 'N/A',
                        commande.ville.nom if commande.ville else 'N/A',
                        region_name,
                        commande.date_cmd.strftime('%d/%m/%Y') if commande.date_cmd else 'N/A',
                        f"{commande.total_cmd:,.2f}",
                        panier.id,
                        panier.article.nom if panier.article else 'N/A',
                        panier.article.reference if panier.article else 'N/A',
                        panier.quantite,
                        f"{panier.article.prix_unitaire:,.2f}" if panier.article else '0,00',
                        f"{panier.quantite * panier.article.prix_unitaire:,.2f}" if panier.article else '0,00'
                    ])
                else:
                    # Articles suivants - informations de commande vides
                    writer.writerow([
                        '', '', '', '', '', '',  # Informations de commande vides
                        panier.id,
                        panier.article.nom if panier.article else 'N/A',
                        panier.article.reference if panier.article else 'N/A',
                        panier.quantite,
                        f"{panier.article.prix_unitaire:,.2f}" if panier.article else '0,00',
                        f"{panier.quantite * panier.article.prix_unitaire:,.2f}" if panier.article else '0,00'
                    ])
        else:
            # Commande sans panier
            writer.writerow([
                commande.id,
                commande.client.nom if commande.client else 'N/A',
                commande.ville.nom if commande.ville else 'N/A',
                region_name,
                commande.date_cmd.strftime('%d/%m/%Y') if commande.date_cmd else 'N/A',
                f"{commande.total_cmd:,.2f}",
                'N/A', 'N/A', 'N/A', 'N/A', 'N/A', 'N/A'
            ])
    
    return response

def export_region_detail_excel(region_name):
    """Export Excel détaillé des commandes d'une région avec leurs paniers"""
    if not OPENPYXL_AVAILABLE:
        return HttpResponse("Export Excel non disponible - openpyxl non installé", status=400)
    
    from commande.models import Commande, Panier
    from article.models import Article
    
    # Récupérer toutes les commandes de la région avec leurs paniers
    commandes = Commande.objects.filter(
        ville__region__nom_region=region_name,
        etats__enum_etat__libelle__in=["Confirmée", "À imprimer", "Préparée"],
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article').distinct()
    
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = f"Commandes {region_name}"
    
    # Styles
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="3B82F6", end_color="3B82F6", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # En-têtes
    headers = [
        'ID Commande', 'Client', 'Ville', 'Région', 'Date Commande', 'Total Commande (DH)',
        'ID Panier', 'Article', 'Référence Article', 'Quantité', 'Prix Unitaire (DH)', 'Total Article (DH)'
    ]
    for col, header in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.border = border
    
    # Données
    row = 2
    for commande in commandes:
        # Écrire les informations de la commande une seule fois
        commande_row = row
        worksheet.cell(row=row, column=1, value=commande.id).border = border
        worksheet.cell(row=row, column=2, value=commande.client.nom if commande.client else 'N/A').border = border
        worksheet.cell(row=row, column=3, value=commande.ville.nom if commande.ville else 'N/A').border = border
        worksheet.cell(row=row, column=4, value=region_name).border = border
        worksheet.cell(row=row, column=5, value=commande.date_cmd.strftime('%d/%m/%Y') if commande.date_cmd else 'N/A').border = border
        worksheet.cell(row=row, column=6, value=commande.total_cmd).border = border
        
        # Si la commande a des paniers
        if commande.paniers.exists():
            for i, panier in enumerate(commande.paniers.all()):
                if i == 0:
                    # Premier article - utiliser la ligne de la commande
                    current_row = row
                else:
                    # Articles suivants - nouvelle ligne avec informations de commande vides
                    row += 1
                    current_row = row
                    # Laisser les colonnes 1-6 vides pour éviter la répétition
                
                worksheet.cell(row=current_row, column=7, value=panier.id).border = border
                worksheet.cell(row=current_row, column=8, value=panier.article.nom if panier.article else 'N/A').border = border
                worksheet.cell(row=current_row, column=9, value=panier.article.reference if panier.article else 'N/A').border = border
                worksheet.cell(row=current_row, column=10, value=panier.quantite).border = border
                worksheet.cell(row=current_row, column=11, value=panier.article.prix_unitaire if panier.article else 0).border = border
                worksheet.cell(row=current_row, column=12, value=panier.quantite * panier.article.prix_unitaire if panier.article else 0).border = border
            row += 1
        else:
            # Commande sans panier
            worksheet.cell(row=row, column=7, value='N/A').border = border
            worksheet.cell(row=row, column=8, value='N/A').border = border
            worksheet.cell(row=row, column=9, value='N/A').border = border
            worksheet.cell(row=row, column=10, value='N/A').border = border
            worksheet.cell(row=row, column=11, value='N/A').border = border
            worksheet.cell(row=row, column=12, value='N/A').border = border
            row += 1
    
    # Ajuster la largeur des colonnes
    column_widths = [12, 20, 15, 15, 15, 18, 10, 25, 15, 10, 15, 18]
    for i, width in enumerate(column_widths, 1):
        worksheet.column_dimensions[get_column_letter(i)].width = width
    
    # Sauvegarder
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="commandes_{region_name.lower()}.xlsx"'
    return response

# ======================== VUES API RECHERCHE SAV ========================

@staff_member_required
@login_required
def sav_search_api(request):
    """API pour la recherche dans les tableaux SAV"""
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', 'all')
    
    if not query:
        return JsonResponse({'results': [], 'total': 0})
    
    from commande.models import Commande, EtatCommande
    
    # Base queryset selon la catégorie
    if category == 'retournees':
        commandes = Commande.objects.filter(
            etats__enum_etat__libelle='Retournée',
            etats__date_fin__isnull=True
        )
    elif category == 'reportees':
        commandes = Commande.objects.filter(
            etats__enum_etat__libelle='Reportée',
            etats__date_fin__isnull=True
        )
    elif category == 'livrees-partiellement':
        commandes = Commande.objects.filter(
            etats__enum_etat__libelle='Livrée Partiellement',
            etats__date_fin__isnull=True
        )
    elif category == 'annulees':
        commandes = Commande.objects.filter(
            etats__enum_etat__libelle='Annulée (SAV)',
            etats__date_fin__isnull=True
        )
    elif category == 'livrees-avec-changement':
        commandes = Commande.objects.filter(
            etats__enum_etat__libelle='Livrée avec Changement',
            etats__date_fin__isnull=True
        )
    elif category == 'livrees':
        commandes = Commande.objects.filter(
            etats__enum_etat__libelle='Livrée',
            etats__date_fin__isnull=True
        )
    else:
        # Recherche dans toutes les catégories SAV
        commandes = Commande.objects.filter(
            etats__enum_etat__libelle__in=[
                'Retournée', 'Reportée', 'Livrée Partiellement', 
                'Annulée (SAV)', 'Livrée avec Changement', 'Livrée'
            ],
            etats__date_fin__isnull=True
        )
    
    # Recherche flexible
    if query:
        commandes = commandes.filter(
            Q(id_yz__icontains=query) |
            Q(num_cmd__icontains=query) |
            Q(client__nom__icontains=query) |
            Q(client__prenom__icontains=query) |
            Q(client__numero_tel__icontains=query) |
            Q(client__adresse__icontains=query) |
            Q(ville__nom__icontains=query) |
            Q(ville__region__nom_region__icontains=query) |
            Q(paniers__article__nom__icontains=query) |
            Q(etats__enum_etat__libelle__icontains=query)
        ).distinct()
    
    # Sélection des champs nécessaires
    commandes = commandes.select_related(
        'client', 'ville', 'ville__region'
    ).prefetch_related(
        'etats__enum_etat', 'etats__operateur', 'paniers__article'
    ).order_by('-etats__date_debut')
    
    # Limiter les résultats
    commandes = commandes[:50]
    
    results = []
    for commande in commandes:
        # Calculer le statut
        status = get_commande_status_global(commande)
        
        # Articles du panier
        articles = []
        for panier in commande.paniers.all()[:3]:  # Limiter à 3 articles
            articles.append({
                'nom': panier.article.nom,
                'quantite': panier.quantite,
                'prix': float(panier.prix_unitaire)
            })
        
        results.append({
            'id': commande.id,
            'id_yz': commande.id_yz,
            'num_cmd': commande.num_cmd,
            'client': {
                'nom': commande.client.nom,
                'prenom': commande.client.prenom,
                'telephone': commande.client.numero_tel,
                'adresse': commande.client.adresse
            },
            'ville': {
                'nom': commande.ville.nom,
                'region': commande.ville.region.nom_region
            },
            'total': float(commande.total_cmd),
            'date': commande.date_cmd.strftime('%d/%m/%Y'),
            'status': status,
            'articles': articles,
            'url': f'/commande/{commande.id}/'
        })
    
    return JsonResponse({
        'results': results,
        'total': len(results),
        'query': query
    })

# ======================== FONCTIONS D'EXPORT ========================
