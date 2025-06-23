from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User, Group
from parametre.models import Operateur # Assurez-vous que ce chemin est correct
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm # Importez PasswordChangeForm
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from commande.models import Commande
from commande.views import gerer_changement_etat_automatique
import json

# Create your views here.

@login_required
def dashboard(request):
    """Page d'accueil de l'interface opérateur logistique avec statistiques réelles"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    from django.db.models import Count, Q, Sum, Avg, F
    from datetime import datetime, timedelta
    
    # Dates pour les statistiques
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # === STATISTIQUES GLOBALES (TOUS LES OPÉRATEURS) ===
    
    # 1. Commandes en préparation (En préparation actif)
    en_preparation = Commande.objects.filter(
        etats__enum_etat__libelle='En préparation',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    # 2. Commandes prêtes à expédier (Préparée actif)
    prets_expedition = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    # 3. Commandes expédiées (En cours de livraison actif)
    expedies = Commande.objects.filter(
        etats__enum_etat__libelle='En cours de livraison',
        etats__date_fin__isnull=True
    ).distinct().count()
    
    # 4. Stock manquant (récupérer depuis la base de données)
    from article.models import Article
    
    # Compter les articles en rupture de stock (qte_disponible = 0) et actifs
    articles_rupture = Article.objects.filter(
        qte_disponible=0,
        actif=True
    ).count()
    
    # Compter les articles avec stock faible (moins de 5 unités)
    articles_stock_faible = Article.objects.filter(
        qte_disponible__lt=5,
        qte_disponible__gt=0,
        actif=True
    ).count()
    
    # Total des problèmes de stock
    stock_manquant = articles_rupture + articles_stock_faible
    
    # === ALERTES DE STOCK DÉTAILLÉES ===
    alertes_stock = []
    
    # Alertes de rupture de stock
    if articles_rupture > 0:
        alertes_stock.append({
            'type': 'danger',
            'message': f'{articles_rupture} article(s) en rupture de stock',
            'count': articles_rupture,
            'icon': 'fas fa-exclamation-triangle'
        })
    
    # Alertes de stock faible
    if articles_stock_faible > 0:
        alertes_stock.append({
            'type': 'warning', 
            'message': f'{articles_stock_faible} article(s) avec stock faible (< 5 unités)',
            'count': articles_stock_faible,
            'icon': 'fas fa-exclamation-circle'
        })
    
    # Articles à réapprovisionner bientôt (stock < 10)
    articles_a_reapprovisionner = Article.objects.filter(
        actif=True,
        qte_disponible__lt=10,
        qte_disponible__gt=0
    ).order_by('qte_disponible')[:3]
    
    if articles_a_reapprovisionner.exists():
        noms_articles = [art.nom for art in articles_a_reapprovisionner]
        alertes_stock.append({
            'type': 'info',
            'message': f'À réapprovisionner bientôt : {", ".join(noms_articles)}',
            'count': len(noms_articles),
            'icon': 'fas fa-info-circle'
        })
    
    # === DÉTAILS SUPPLÉMENTAIRES DU STOCK ===
    
    # Articles les plus en demande (avec le plus de commandes)
    from django.db.models import Count
    articles_populaires = Article.objects.filter(
        actif=True,
        paniers__isnull=False
    ).annotate(
        nb_commandes=Count('paniers__commande', distinct=True)
    ).order_by('-nb_commandes')[:5]
    
    # Stock total et valeur
    stock_total = Article.objects.filter(actif=True).aggregate(
        total_articles=Count('id'),
        total_stock=Sum('qte_disponible'),
        valeur_totale=Sum(F('qte_disponible') * F('prix_unitaire'))
    )
    
    # Articles par catégorie avec problèmes de stock
    categories_stock = Article.objects.filter(
        actif=True
    ).values('categorie').annotate(
        total_articles=Count('id'),
        articles_rupture=Count('id', filter=Q(qte_disponible=0)),
        articles_faible=Count('id', filter=Q(qte_disponible__lt=5, qte_disponible__gt=0)),
        stock_moyen=Avg('qte_disponible')
    ).order_by('-articles_rupture', '-articles_faible')
    
    # Si aucune alerte, message positif
    if not alertes_stock:
        alertes_stock.append({
            'type': 'success',
            'message': 'Tous les articles sont bien approvisionnés',
            'count': 0,
            'icon': 'fas fa-check-circle'
        })
    
    # === STATISTIQUES SPÉCIFIQUES À CET OPÉRATEUR ===
    
    # Commandes affectées à cet opérateur
    mes_commandes = Commande.objects.filter(
        etats__operateur=operateur,
        etats__enum_etat__libelle='En cours de livraison',
        etats__date_fin__isnull=True
    ).distinct()
    
    # Mes commandes aujourd'hui
    mes_commandes_aujourd_hui = mes_commandes.filter(
        etats__date_debut__date=today
    ).count()
    
    # Mes commandes cette semaine
    mes_commandes_semaine = mes_commandes.filter(
        etats__date_debut__date__gte=start_of_week
    ).count()
    
    # Mes commandes ce mois
    mes_commandes_mois = mes_commandes.filter(
        etats__date_debut__date__gte=start_of_month
    ).count()
    
    # Montant total de mes commandes
    mes_commandes_montant = mes_commandes.aggregate(total=Sum('total_cmd'))['total'] or 0
    
    # === COMMANDES URGENTES (exemple: commandes de plus de 3 jours) ===
    date_limite_urgence = today - timedelta(days=3)
    commandes_urgentes = mes_commandes.filter(
        etats__date_debut__date__lte=date_limite_urgence
    )
    
    # === STATISTIQUES PAR VILLE POUR CET OPÉRATEUR ===
    stats_par_ville = mes_commandes.values(
        'ville__nom', 'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('-nb_commandes')[:5]  # Top 5 des villes
    
    # === ÉVOLUTION DES LIVRAISONS (7 derniers jours) ===
    livraisons_semaine = []
    for i in range(7):
        date_jour = today - timedelta(days=6-i)
        nb_livraisons = Commande.objects.filter(
            etats__operateur=operateur,
            etats__enum_etat__libelle='Livrée',
            etats__date_debut__date=date_jour
        ).distinct().count()
        livraisons_semaine.append({
            'date': date_jour,
            'nb_livraisons': nb_livraisons
        })
    
    # === CALCULS DE POURCENTAGES ===
    # Pourcentage d'évolution cette semaine vs semaine dernière
    semaine_derniere_debut = start_of_week - timedelta(days=7)
    semaine_derniere_fin = start_of_week - timedelta(days=1)
    
    commandes_semaine_derniere = Commande.objects.filter(
        etats__operateur=operateur,
        etats__enum_etat__libelle='En cours de livraison',
        etats__date_debut__date__range=[semaine_derniere_debut, semaine_derniere_fin]
    ).distinct().count()
    
    if commandes_semaine_derniere > 0:
        evolution_semaine = ((mes_commandes_semaine - commandes_semaine_derniere) / commandes_semaine_derniere) * 100
    else:
        evolution_semaine = 100 if mes_commandes_semaine > 0 else 0
    
    context = {
        'operateur': operateur,
        # Statistiques globales
        'en_preparation': en_preparation,
        'prets_expedition': prets_expedition,
        'expedies': expedies,
        'stock_manquant': stock_manquant,
        # Mes statistiques
        'mes_commandes_total': mes_commandes.count(),
        'mes_commandes_aujourd_hui': mes_commandes_aujourd_hui,
        'mes_commandes_semaine': mes_commandes_semaine,
        'mes_commandes_mois': mes_commandes_mois,
        'mes_commandes_montant': mes_commandes_montant,
        # Commandes urgentes
        'commandes_urgentes': commandes_urgentes,
        'nb_commandes_urgentes': commandes_urgentes.count(),
        # Statistiques par ville
        'stats_par_ville': stats_par_ville,
        # Alertes de stock détaillées
        'alertes_stock': alertes_stock,
        'articles_rupture': articles_rupture,
        'articles_stock_faible': articles_stock_faible,
        # Détails du stock
        'articles_populaires': articles_populaires,
        'stock_total': stock_total,
        'categories_stock': categories_stock,
        'articles_a_reapprovisionner': articles_a_reapprovisionner,
        # Évolution
        'evolution_semaine': round(evolution_semaine, 1),
        'livraisons_semaine': livraisons_semaine,
        # Méta
        'page_title': 'Tableau de Bord',
        'page_subtitle': f'Interface Opérateur Logistique - {operateur.nom_complet}',
    }
    
    return render(request, 'composant_generale/operatLogistic/home.html', context)

@login_required
def liste_commandes(request):
    """Liste des commandes affectées à cet opérateur logistique"""
    try:
        # Récupérer l'opérateur logistique connecté
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    # Récupérer les commandes affectées à cet opérateur logistique
    # Les commandes sont dans l'état "En cours de livraison" et affectées à cet opérateur
    commandes_affectees = Commande.objects.filter(
        etats__enum_etat__libelle='En cours de livraison',
        etats__operateur=operateur,
        etats__date_fin__isnull=True  # État actif
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct().order_by('-etats__date_debut')
    
    # Si aucune commande trouvée avec la méthode stricte, essayer une approche plus large
    if not commandes_affectees.exists():
        # Chercher toutes les commandes qui ont été affectées à cet opérateur pour la livraison
        # et qui n'ont pas encore d'état "Livrée" ou "Retournée"
        commandes_affectees = Commande.objects.filter(
            etats__operateur=operateur,
            etats__enum_etat__libelle__in=['En cours de livraison', 'Préparée']
        ).exclude(
            # Exclure les commandes qui ont déjà un état ultérieur actif
            Q(etats__enum_etat__libelle__in=['Livrée', 'Retournée', 'Annulée'], etats__date_fin__isnull=True)
        ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct().order_by('-etats__date_debut')
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_affectees = commandes_affectees.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(commandes_affectees, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    start_of_month = today.replace(day=1)
    
    # Compter les commandes par période (utiliser la même logique flexible)
    base_filter = Q(etats__operateur=operateur) & (
        Q(etats__enum_etat__libelle='En cours de livraison', etats__date_fin__isnull=True) |
        Q(etats__enum_etat__libelle='Préparée')
    )
    
    affectees_aujourd_hui = Commande.objects.filter(
        base_filter & Q(etats__date_debut__date=today)
    ).distinct().count()
    
    affectees_semaine = Commande.objects.filter(
        base_filter & Q(etats__date_debut__date__gte=start_of_week)
    ).distinct().count()
    
    affectees_mois = Commande.objects.filter(
        base_filter & Q(etats__date_debut__date__gte=start_of_month)
    ).distinct().count()
    
    total_commandes = commandes_affectees.count()
    
    # Montant total
    total_montant = commandes_affectees.aggregate(total=Sum('total_cmd'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'operateur': operateur,
        'total_commandes': total_commandes,
        'total_montant': total_montant,
        'affectees_aujourd_hui': affectees_aujourd_hui,
        'affectees_semaine': affectees_semaine,
        'affectees_mois': affectees_mois,
        'page_title': 'Mes Commandes',
        'page_subtitle': f'Commandes affectées à {operateur.nom_complet}',
    }
    
    return render(request, 'operatLogistic/liste_commande.html', context)

@login_required
def detail_commande(request, commande_id):
    """Affiche les détails d'une commande spécifique pour l'opérateur logistique."""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')

    try:
        commande = get_object_or_404(Commande, id=commande_id)

        # Vérifier que la commande est bien affectée à cet opérateur
        is_affectee = commande.etats.filter(
            Q(enum_etat__libelle='En cours de livraison') | Q(enum_etat__libelle='Préparée'),
            operateur=operateur
        ).exists()

        if not is_affectee:
            messages.error(request, "Vous n'avez pas l'autorisation de voir les détails de cette commande.")
            return redirect('operatLogistic:liste_commandes')
            
    except Commande.DoesNotExist:
        raise Http404("La commande n'existe pas.")

    context = {
        'commande': commande,
        'page_title': f'Détails Commande {commande.id_yz}',
        'page_subtitle': 'Informations complètes sur la commande à livrer',
    }
    return render(request, 'operatLogistic/detail_commande.html', context)

@login_required
def repartition(request):
    """Page de répartition automatique des commandes par ville et région"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    # Récupérer les commandes actuellement en cours de livraison (déjà réparties)
    from commande.models import EnumEtatCmd
    from django.db.models import Count
    
    commandes_reparties = Commande.objects.filter(
        etats__enum_etat__libelle='En cours de livraison',
        etats__date_fin__isnull=True  # État actif
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats__operateur').distinct()
    
    # Statistiques par ville et région des commandes réparties
    stats_par_ville = commandes_reparties.values(
        'ville__nom', 'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('ville__region__nom_region', 'ville__nom')
    
    stats_par_region = commandes_reparties.values(
        'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('ville__region__nom_region')
    
    # Calculer le montant total général
    total_montant_general = commandes_reparties.aggregate(total=Sum('total_cmd'))['total'] or 0
    
    context = {
        'operateur': operateur,
        'commandes_reparties': commandes_reparties,
        'stats_par_ville': stats_par_ville,
        'stats_par_region': stats_par_region,
        'total_commandes_reparties': commandes_reparties.count(),
        'total_montant_general': total_montant_general,
        'page_title': 'Répartition des Commandes',
        'page_subtitle': 'Répartition automatique par ville et région',
    }
    
    return render(request, 'operatLogistic/repartition.html', context)

@login_required
def details_region(request, nom_region):
    """Page de détails d'une région avec toutes les commandes par ville et opérateur"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur logistique non trouvé.")
        return redirect('login')
    
    from commande.models import EnumEtatCmd
    from django.db.models import Count
    from urllib.parse import unquote
    
    # Décoder le nom de la région depuis l'URL
    nom_region = unquote(nom_region)
    
    # Récupérer les commandes de cette région en cours de livraison
    commandes_region = Commande.objects.filter(
        etats__enum_etat__libelle='En cours de livraison',
        etats__date_fin__isnull=True,  # État actif
        ville__region__nom_region=nom_region
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats__operateur').distinct()
    
    # Statistiques détaillées par ville
    stats_par_ville = commandes_region.values(
        'ville__nom'
    ).annotate(
        nb_commandes=Count('id'),
        total_montant=Sum('total_cmd')
    ).order_by('ville__nom')
    
    # Calculer les totaux
    total_commandes = commandes_region.count()
    total_montant = commandes_region.aggregate(total=Sum('total_cmd'))['total'] or 0
    
    context = {
        'operateur': operateur,
        'nom_region': nom_region,
        'commandes_region': commandes_region,
        'stats_par_ville': stats_par_ville,
        'total_commandes': total_commandes,
        'total_montant': total_montant,
        'page_title': f'Détails - {nom_region}',
        'page_subtitle': 'Répartition détaillée par ville',
    }
    
    return render(request, 'operatLogistic/details_region.html', context)

@login_required
def parametre(request):
    """Page des paramètres opérateur logistique"""
    return render(request, 'operatLogistic/parametre.html')

@login_required
def creer_operateur_logistique(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        mail = request.POST.get('mail')
        telephone = request.POST.get('telephone')
        adresse = request.POST.get('adresse')

        # Validation de base
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
                type_operateur='LOGISTIQUE', # Type spécifique pour logistique
                telephone=telephone,
                adresse=adresse
            )
            operateur.save()

            # Ajouter l'utilisateur au groupe 'operateur_logistique'
            group, created = Group.objects.get_or_create(name='operateur_logistique')
            user.groups.add(group)

            messages.success(request, f"L'opérateur logistique {prenom} {nom} a été créé avec succès.")
            return redirect('app_admin:liste_operateurs') # Rediriger vers la liste des opérateurs

        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la création de l'opérateur : {e}")
            if 'user' in locals() and user.pk:
                user.delete()
            return render(request, 'composant_generale/creer_operateur.html', {'form_data': request.POST})

    return render(request, 'composant_generale/creer_operateur.html')

@login_required
def profile_logistique(request):
    """Page de profil pour l'opérateur logistique"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur non trouvé.")
        return redirect('login') # Rediriger vers la page de connexion ou une page d'erreur
    return render(request, 'operatLogistic/profile.html', {'operateur': operateur})

@login_required
def modifier_profile_logistique(request):
    """Page de modification de profil pour l'opérateur logistique"""
    try:
        operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
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
            return render(request, 'operatLogistic/modifier_profile.html', {'operateur': operateur, 'user': user})

        # Vérifier si l'email est déjà utilisé par un autre utilisateur (sauf l'utilisateur actuel)
        if User.objects.filter(email=email).exclude(pk=user.pk).exists():
            messages.error(request, "Cet email est déjà utilisé par un autre compte.")
            return render(request, 'operatLogistic/modifier_profile.html', {'operateur': operateur, 'user': user})
        
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
            # Ne pas modifier type_operateur ou actif
            operateur.save()

            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('operatLogistic:profile')

        except Exception as e:
            messages.error(request, f"Une erreur est survenue lors de la mise à jour : {e}")

    return render(request, 'operatLogistic/modifier_profile.html', {'operateur': operateur, 'user': user})

@login_required
def changer_mot_de_passe_logistique(request):
    """Page de changement de mot de passe pour l'opérateur logistique"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important! Pour garder l'utilisateur connecté
            messages.success(request, 'Votre mot de passe a été mis à jour avec succès !')
            return redirect('operatLogistic:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'operatLogistic/changer_mot_de_passe.html', {'form': form})

@login_required
def marquer_livree(request, commande_id):
    """Marquer une commande comme livrée"""
    if request.method == 'POST':
        try:
            # Vérifier que l'utilisateur est un opérateur logistique
            operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
            
            # Récupérer la commande
            commande = Commande.objects.get(id=commande_id)
            
            # Vérifier que la commande est affectée à cet opérateur
            etat_actuel = commande.etat_actuel
            if not (etat_actuel and etat_actuel.operateur == operateur and etat_actuel.enum_etat.libelle == 'En cours de livraison'):
                return JsonResponse({'success': False, 'message': 'Cette commande ne vous est pas affectée ou n\'est pas en cours de livraison.'})
            
            # Marquer comme livrée
            gerer_changement_etat_automatique(
                commande, 
                'Livrée', 
                operateur=operateur,
                commentaire="Commande livrée par l'opérateur logistique"
            )
            
            return JsonResponse({'success': True, 'message': f'Commande {commande.id_yz} marquée comme livrée avec succès.'})
            
        except Operateur.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Opérateur non trouvé.'})
        except Commande.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Commande non trouvée.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})

@login_required
def signaler_probleme(request, commande_id):
    """Signaler un problème avec une commande"""
    if request.method == 'POST':
        try:
            # Vérifier que l'utilisateur est un opérateur logistique
            operateur = Operateur.objects.get(user=request.user, type_operateur='LOGISTIQUE')
            
            # Récupérer les données
            data = json.loads(request.body)
            description = data.get('description', '')
            
            if not description:
                return JsonResponse({'success': False, 'message': 'Description du problème requise.'})
            
            # Récupérer la commande
            commande = Commande.objects.get(id=commande_id)
            
            # Vérifier que la commande est affectée à cet opérateur
            etat_actuel = commande.etat_actuel
            if not (etat_actuel and etat_actuel.operateur == operateur):
                return JsonResponse({'success': False, 'message': 'Cette commande ne vous est pas affectée.'})
            
            # Créer une opération pour signaler le problème
            Operation.objects.create(
                commande=commande,
                type_operation='COMMENTAIRE',
                operateur=operateur,
                commentaire=f"PROBLÈME SIGNALÉ: {description}"
            )
            
            return JsonResponse({'success': True, 'message': f'Problème signalé pour la commande {commande.id_yz}.'})
            
        except Operateur.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Opérateur non trouvé.'})
        except Commande.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Commande non trouvée.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée.'})
