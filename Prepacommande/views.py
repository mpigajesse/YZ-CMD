from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from parametre.models import Operateur
from commande.models import Commande, EtatCommande, EnumEtatCmd, Operation, Panier

# Create your views here.

@login_required
def home_view(request):
    """Page d'accueil avec statistiques pour les opérateurs de préparation"""
    try:
        operateur_profile = request.user.profil_operateur
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('login')

    # Dates pour les statistiques
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)

    # États spécifiques à la préparation
    try:
        etat_en_preparation = EnumEtatCmd.objects.get(libelle__icontains='préparation')
    except EnumEtatCmd.DoesNotExist:
        etat_en_preparation = None
    
    try:
        etat_confirmee = EnumEtatCmd.objects.get(libelle__icontains='confirmée')
    except EnumEtatCmd.DoesNotExist:
        etat_confirmee = None

    # Statistiques principales
    stats = {}
    
    # Commandes à préparer (confirmées mais non encore en préparation)
    if etat_confirmee and etat_en_preparation:
        commandes_a_preparer = Commande.objects.filter(
            etats__enum_etat=etat_confirmee,
            etats__date_fin__isnull=True
        ).exclude(
            etats__enum_etat=etat_en_preparation,
            etats__date_fin__isnull=True
        ).count()
    else:
        commandes_a_preparer = 0
    
    # Commandes en cours de préparation
    if etat_en_preparation:
        commandes_en_preparation = Commande.objects.filter(
            etats__enum_etat=etat_en_preparation,
            etats__date_fin__isnull=True
        ).count()
    else:
        commandes_en_preparation = 0
    
    # Commandes préparées aujourd'hui
    commandes_preparees_today = 0
    if etat_en_preparation:
        commandes_preparees_today = EtatCommande.objects.filter(
            enum_etat=etat_en_preparation,
            date_fin__date=today
        ).count()
    
    # Commandes préparées cette semaine
    commandes_preparees_week = 0
    if etat_en_preparation:
        commandes_preparees_week = EtatCommande.objects.filter(
            enum_etat=etat_en_preparation,
            date_fin__date__gte=start_of_week,
            date_fin__date__lte=today
        ).count()
    
    # Valeur totale des commandes préparées aujourd'hui
    valeur_preparees_today = 0
    if etat_en_preparation:
        commandes_ids = EtatCommande.objects.filter(
            enum_etat=etat_en_preparation,
            date_fin__date=today
        ).values_list('commande_id', flat=True)
        
        valeur_preparees_today = Commande.objects.filter(
            id__in=commandes_ids
        ).aggregate(
            total=Sum('total_cmd')
        )['total'] or 0
    
    # Commandes urgentes (plus de 2 jours d'attente)
    date_limite_urgence = today - timedelta(days=2)
    commandes_urgentes = 0
    if etat_confirmee:
        commandes_urgentes = Commande.objects.filter(
            etats__enum_etat=etat_confirmee,
            etats__date_fin__isnull=True,
            etats__date_debut__date__lte=date_limite_urgence
        ).count()
    
    # Articles les plus préparés cette semaine
    articles_populaires = []
    if etat_en_preparation:
        commandes_preparees_ids = EtatCommande.objects.filter(
            enum_etat=etat_en_preparation,
            date_fin__date__gte=start_of_week,
            date_fin__date__lte=today
        ).values_list('commande_id', flat=True)
        
        articles_populaires = Panier.objects.filter(
            commande_id__in=commandes_preparees_ids
        ).values(
            'article__nom', 'article__reference'
        ).annotate(
            total_quantite=Sum('quantite'),
            total_commandes=Count('commande', distinct=True)
        ).order_by('-total_quantite')[:5]
    
    # Performance quotidienne de l'opérateur
    ma_performance_today = 0
    if etat_en_preparation:
        ma_performance_today = EtatCommande.objects.filter(
            enum_etat=etat_en_preparation,
            date_fin__date=today,
            operateur=operateur_profile
        ).count()
    
    # Activité récente
    activite_recente = []
    if etat_en_preparation:
        activite_recente = EtatCommande.objects.filter(
            enum_etat=etat_en_preparation,
            operateur=operateur_profile,
            date_fin__isnull=False
        ).select_related('commande', 'commande__client').order_by('-date_fin')[:5]

    stats = {
        'commandes_a_preparer': commandes_a_preparer,
        'commandes_en_preparation': commandes_en_preparation,
        'commandes_preparees_today': commandes_preparees_today,
        'commandes_preparees_week': commandes_preparees_week,
        'valeur_preparees_today': valeur_preparees_today,
        'commandes_urgentes': commandes_urgentes,
        'ma_performance_today': ma_performance_today,
        'articles_populaires': articles_populaires,
        'activite_recente': activite_recente,
    }

    context = {
        'page_title': 'Tableau de Bord',
        'page_subtitle': 'Interface Opérateur de Préparation',
        'profile': operateur_profile,
        'stats': stats,
        'today': today,
    }
    return render(request, 'composant_generale/operatPrepa/home.html', context)

@login_required
def liste_prepa(request):
    """Liste des commandes à préparer pour les opérateurs de préparation"""
    context = {
        'page_title': 'Commandes à Préparer',
        'page_subtitle': 'Gérez les commandes en attente de préparation',
    }
    return render(request, 'Prepacommande/liste_prepa.html', context)

@login_required
def profile_view(request):
    try:
        operateur_profile = request.user.profil_operateur
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('login') # Ou une page d'erreur appropriée

    context = {
        'page_title': 'Mon Profil',
        'page_subtitle': 'Gérez les informations de votre profil',
        'profile': operateur_profile,
    }
    return render(request, 'Prepacommande/profile.html', context)

@login_required
def modifier_profile_view(request):
    try:
        operateur_profile = request.user.profil_operateur
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('login')

    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        mail = request.POST.get('mail')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        # Validation minimale (vous pouvez ajouter plus de validations ici)
        if not nom or not prenom or not mail:
            messages.error(request, "Nom, prénom et email sont requis.")
            context = {
                'page_title': 'Modifier Profil',
                'page_subtitle': 'Mettez à jour vos informations personnelles',
                'profile': operateur_profile,
                'form_data': request.POST, # Pour pré-remplir le formulaire
            }
            return render(request, 'Prepacommande/modifier_profile.html', context)
        
        # Mettre à jour l'utilisateur Django
        request.user.first_name = prenom
        request.user.last_name = nom
        request.user.email = mail
        request.user.save()

        # Mettre à jour le profil de l'opérateur
        operateur_profile.nom = nom
        operateur_profile.prenom = prenom
        operateur_profile.mail = mail
        operateur_profile.telephone = telephone
        operateur_profile.adresse = adresse

        # Gérer l'image si elle est fournie
        if 'photo' in request.FILES:
            operateur_profile.photo = request.FILES['photo']
        
        operateur_profile.save()

        messages.success(request, "Votre profil a été mis à jour avec succès.")
        return redirect('Prepacommande:profile') # Rediriger vers la page de profil après succès
    else:
        context = {
            'page_title': 'Modifier Profil',
            'page_subtitle': 'Mettez à jour vos informations personnelles',
            'profile': operateur_profile,
        }
        return render(request, 'Prepacommande/modifier_profile.html', context)

@login_required
def changer_mot_de_passe_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if not request.user.check_password(old_password):
            messages.error(request, "L'ancien mot de passe est incorrect.")
        elif new_password1 != new_password2:
            messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
        else:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user) # Important pour maintenir la session
            messages.success(request, "Votre mot de passe a été changé avec succès.")
            return redirect('Prepacommande:profile')

        # Si des erreurs, re-rendu le formulaire avec les messages
        context = {
            'page_title': 'Changer Mot de Passe',
            'page_subtitle': 'Sécurisez votre compte',
        }
        return render(request, 'Prepacommande/changer_mot_de_passe.html', context)
    else:
        context = {
            'page_title': 'Changer Mot de Passe',
            'page_subtitle': 'Sécurisez votre compte',
        }
        return render(request, 'Prepacommande/changer_mot_de_passe.html', context)

@login_required
def detail_prepa(request, pk):
    # Cette vue est un placeholder pour la page de détail de la préparation de commande
    # La logique réelle sera implémentée ultérieurement.
    context = {
        'page_title': f'Préparation Commande #{pk}',
        'page_subtitle': 'Détails de la commande et étapes de préparation',
        'commande_id': pk,
    }
    return render(request, 'Prepacommande/detail_prepa.html', context)

@login_required
def etiquette_view(request):
    """Page de gestion des étiquettes pour les commandes préparées"""
    context = {
        'page_title': 'Gestion des Étiquettes',
        'page_subtitle': 'Imprimez les étiquettes des commandes préparées',
    }
    return render(request, 'Prepacommande/etiquette.html', context)
