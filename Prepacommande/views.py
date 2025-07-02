from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.db.models import Count, Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.db import transaction

import json
from parametre.models import Operateur
from commande.models import Commande, EtatCommande, EnumEtatCmd, Operation, Panier
from django.urls import reverse

import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64

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
    try:
        operateur_profile = request.user.profil_operateur
        
        # Vérifier que l'utilisateur est un opérateur de préparation
        if not operateur_profile.is_preparation:
            messages.error(request, "Accès non autorisé. Vous n'êtes pas un opérateur de préparation.")
            return redirect('login')
            
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('login')

    # Récupérer les commandes dont l'état ACTUEL est "À imprimer" ou "En préparation" et qui sont affectées à cet opérateur
    # On cherche les commandes qui ont un état "À imprimer" ou "En préparation" actif (sans date_fin) avec cet opérateur
    from django.db.models import Q, Max
    
    commandes_affectees = Commande.objects.filter(
        Q(etats__enum_etat__libelle='À imprimer') | Q(etats__enum_etat__libelle='En préparation'),
        etats__operateur=operateur_profile,
        etats__date_fin__isnull=True  # État actif (en cours)
    ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article', 'etats').distinct()
    
    # Si aucune commande trouvée avec la méthode stricte, essayer une approche plus large
    if not commandes_affectees.exists():
        # Chercher toutes les commandes qui ont été affectées à cet opérateur pour la préparation
        # et qui n'ont pas encore d'état "Préparée" ou "En cours de livraison"
        commandes_affectees = Commande.objects.filter(
            Q(etats__enum_etat__libelle='À imprimer') | Q(etats__enum_etat__libelle='En préparation'),
            etats__operateur=operateur_profile
        ).exclude(
            # Exclure les commandes qui ont déjà un état ultérieur actif
            Q(etats__enum_etat__libelle__in=['Préparée', 'En cours de livraison', 'Livrée', 'Annulée'], etats__date_fin__isnull=True)
        ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article', 'etats').distinct()
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_affectees = commandes_affectees.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query)
        ).distinct()
    
    # Tri par date d'affectation (plus récentes en premier)
    commandes_affectees = commandes_affectees.order_by('-etats__date_debut')
    
    # Statistiques
    total_affectees = commandes_affectees.count()
    valeur_totale = commandes_affectees.aggregate(total=Sum('total_cmd'))['total'] or 0
    
    # Commandes urgentes (affectées depuis plus de 1 jour)
    date_limite_urgence = timezone.now() - timedelta(days=1)
    commandes_urgentes = commandes_affectees.filter(
        etats__date_debut__lt=date_limite_urgence
    ).count()
    
    context = {
        'page_title': 'Mes Commandes à Préparer',
        'page_subtitle': f'Vous avez {total_affectees} commande(s) affectée(s)',
        'commandes_affectees': commandes_affectees,
        'search_query': search_query,
        'stats': {
            'total_affectees': total_affectees,
            'valeur_totale': valeur_totale,
            'commandes_urgentes': commandes_urgentes,
        },
        'operateur_profile': operateur_profile,
        'api_produits_url_base': reverse('Prepacommande:api_commande_produits', args=[99999999]),
        'api_changer_etat_url_base': reverse('Prepacommande:api_changer_etat_preparation', args=[99999999]),
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
    """Page de changement de mot de passe pour l'opérateur de préparation - Désactivée"""
    return redirect('Prepacommande:profile')

@login_required
def detail_prepa(request, pk):
    """Vue détaillée pour la préparation d'une commande spécifique"""
    try:
        operateur_profile = request.user.profil_operateur
        
        # Vérifier que l'utilisateur est un opérateur de préparation
        if not operateur_profile.is_preparation:
            messages.error(request, "Accès non autorisé. Vous n'êtes pas un opérateur de préparation.")
            return redirect('login')
            
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('login')

    # Récupérer la commande spécifique
    try:
        commande = Commande.objects.select_related(
            'client', 'ville', 'ville__region'
        ).prefetch_related(
            'paniers__article', 'etats__enum_etat', 'etats__operateur'
        ).get(id=pk)
    except Commande.DoesNotExist:
        messages.error(request, "La commande demandée n'existe pas.")
        return redirect('Prepacommande:liste_prepa')

    # Vérifier que la commande est bien affectée à cet opérateur pour la préparation
    etat_preparation = commande.etats.filter(
        Q(enum_etat__libelle='À imprimer') | Q(enum_etat__libelle='En préparation'),
        operateur=operateur_profile
    ).first()
    
    if not etat_preparation:
        messages.error(request, "Cette commande ne vous est pas affectée pour la préparation.")
        return redirect('Prepacommande:liste_prepa')

    # Récupérer les paniers (articles) de la commande
    paniers = commande.paniers.all().select_related('article')
    
    # Ajouter le prix unitaire et le total de chaque ligne
    for panier in paniers:
        panier.prix_unitaire = panier.sous_total / panier.quantite if panier.quantite > 0 else 0
        panier.total_ligne = panier.sous_total
    
    # Calculer le total des articles
    total_articles = sum(panier.total_ligne for panier in paniers)
    
    # Récupérer tous les états de la commande pour afficher l'historique
    etats_commande = commande.etats.all().select_related('enum_etat', 'operateur').order_by('date_debut')
    
    # Déterminer l'état actuel
    etat_actuel = etats_commande.filter(date_fin__isnull=True).first()
    
    # Récupérer les opérations associées à la commande
    operations = commande.operations.select_related('operateur').order_by('-date_operation')
    
    # Générer le code-barres pour la commande
    code128 = barcode.get_barcode_class('code128')
    barcode_instance = code128(str(commande.id_yz), writer=ImageWriter())
    buffer = BytesIO()
    barcode_instance.write(buffer, options={'write_text': False, 'module_height': 10.0})
    barcode_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    commande_barcode = f"data:image/png;base64,{barcode_base64}"

    # Gestion des actions POST (marquer comme préparée, etc.)
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'commencer_preparation':
            # Passer de "À imprimer" vers "En préparation"
            if etat_preparation and etat_preparation.enum_etat.libelle == 'À imprimer' and not etat_preparation.date_fin:
                with transaction.atomic():
                    # Terminer l'état "À imprimer"
                    etat_preparation.date_fin = timezone.now()
                    etat_preparation.commentaire = "Impression terminée, début de la préparation."
                    etat_preparation.save()

                    # Créer ou récupérer l'état "En préparation"
                    etat_en_preparation_enum, created = EnumEtatCmd.objects.get_or_create(
                        libelle='En préparation',
                        defaults={'ordre': 40, 'couleur': '#3B82F6'}
                    )
                    
                    # Créer le nouvel état "En préparation"
                    EtatCommande.objects.create(
                        commande=commande,
                        enum_etat=etat_en_preparation_enum,
                        operateur=operateur_profile,
                        date_debut=timezone.now(),
                        commentaire="Commande passée en préparation."
                    )
                    
                    messages.success(request, f"La commande {commande.id_yz} est maintenant en cours de préparation.")
                
                return redirect('Prepacommande:detail_prepa', pk=commande.id)
        
        elif action == 'marquer_preparee':
            with transaction.atomic():
                # Marquer l'état 'En préparation' comme terminé
                etat_en_preparation, created = EnumEtatCmd.objects.get_or_create(libelle='En préparation')
                
                etat_actuel = EtatCommande.objects.filter(
                    commande=commande,
                    enum_etat=etat_en_preparation,
                    date_fin__isnull=True
                ).first()
                
                if etat_actuel:
                    etat_actuel.date_fin = timezone.now()
                    etat_actuel.operateur = operateur_profile
                    etat_actuel.save()
                
                # Créer le nouvel état 'Préparée'
                etat_preparee, created = EnumEtatCmd.objects.get_or_create(libelle='Préparée')
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=etat_preparee,
                    operateur=operateur_profile
                )
                
                # Log de l'opération
                Operation.objects.create(
                    commande=commande,
                    type_operation='PREPARATION_TERMINEE',
                    operateur=operateur_profile,
                    conclusion=f"Commande marquée comme préparée par {operateur_profile.nom_complet}."
                )
            
            messages.success(request, f"La commande {commande.id_yz} a bien été marquée comme préparée.")
            return redirect('Prepacommande:detail_prepa', pk=commande.pk)
    
    context = {
        'page_title': f'Préparation Commande {commande.id_yz}',
        'page_subtitle': f'Détails de la commande et étapes de préparation',
        'commande': commande,
        'paniers': paniers,
        'total_articles': total_articles,
        'etats_commande': etats_commande,
        'etat_actuel': etat_actuel,
        'etat_preparation': etat_preparation,
        'operateur_profile': operateur_profile,
        'operations': operations,
        'commande_barcode': commande_barcode,
    }
    return render(request, 'Prepacommande/detail_prepa.html', context)

@login_required
def etiquette_view(request):
    """Page de gestion des étiquettes pour les commandes préparées"""
    try:
        operateur_profile = request.user.profil_operateur
        
        # Vérifier que l'utilisateur est un opérateur de préparation
        if not operateur_profile.is_preparation:
            messages.error(request, "Accès non autorisé. Vous n'êtes pas un opérateur de préparation.")
            return redirect('login')
            
    except Operateur.DoesNotExist:
        messages.error(request, "Votre profil opérateur n'existe pas.")
        return redirect('login')

    # Récupérer les commandes préparées par cet opérateur
    # Une commande est considérée comme préparée quand elle a un état "Préparée" actif
    from django.db.models import Max
    
    commandes_preparees = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__operateur=operateur_profile,
        etats__date_fin__isnull=True  # État actif = commande préparée
    ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article', 'etats__enum_etat').annotate(
        date_preparation=Max('etats__date_debut')
    ).distinct()
    
    # Recherche
    search_query = request.GET.get('search', '')
    if search_query:
        commandes_preparees = commandes_preparees.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query)
        ).distinct()
    
    # Tri par date de préparation (plus récentes en premier)
    commandes_preparees = commandes_preparees.order_by('-date_preparation')
    
    # Générer les codes-barres pour chaque commande
    code128 = barcode.get_barcode_class('code128')
    for commande in commandes_preparees:
        barcode_instance = code128(str(commande.id_yz), writer=ImageWriter())
        buffer = BytesIO()
        barcode_instance.write(buffer, options={'write_text': False})
        barcode_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        commande.barcode_base64 = f"data:image/png;base64,{barcode_base64}"
    
    # Statistiques
    total_preparees = commandes_preparees.count()
    
    context = {
        'page_title': 'Consultation des Commandes Préparées',
        'page_subtitle': f'Consultez vos {total_preparees} commande(s) préparée(s)',
        'commandes_preparees': commandes_preparees,
        'search_query': search_query,
        'total_preparees': total_preparees,
        'operateur_profile': operateur_profile,
    }
    return render(request, 'Prepacommande/etiquette.html', context)

@login_required
def api_commande_produits(request, commande_id):
    """API pour récupérer les produits d'une commande pour les étiquettes"""
    try:
        # Récupérer la commande. La sécurité est déjà gérée par la page
        # qui appelle cette API, qui ne liste que les commandes autorisées.
        commande = Commande.objects.get(id=commande_id)
        
        # Récupérer tous les produits de la commande
        paniers = commande.paniers.all().select_related('article')
        
        # Construire la liste des produits
        produits_list = []
        for panier in paniers:
            if panier.article:
                # Format: "NOM REFERENCE , POINTURE"
                produit_info = f"{panier.article.nom or ''} {panier.article.reference or ''}".strip()
                if panier.article.pointure:
                    produit_info += f" , {panier.article.pointure}"
                
                # Ajouter la quantité si elle est supérieure à 1
                if panier.quantite > 1:
                    produit_info += f" (x{panier.quantite})" # Mettre la quantité entre parenthèses
                produits_list.append(produit_info)
        
        # Joindre tous les produits en une seule chaîne, en utilisant " + " comme séparateur
        produits_text = " + ".join(produits_list) if produits_list else "PRODUITS NON SPÉCIFIÉS"
        
        return JsonResponse({
            'success': True,
            'produits': produits_text,
            'nombre_articles': len(produits_list)
        })
        
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande non trouvée'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@login_required
def api_changer_etat_preparation(request, commande_id):
    """API pour changer l'état d'une commande de 'À imprimer' vers 'En préparation'"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})
    
    try:
        # Vérifier que l'utilisateur est un opérateur de préparation
        operateur_profile = request.user.profil_operateur
        if not operateur_profile.is_preparation:
            return JsonResponse({'success': False, 'message': 'Accès non autorisé'})
        
        # Récupérer la commande
        commande = Commande.objects.get(id=commande_id)
        
        # Vérifier que la commande est bien affectée à cet opérateur avec l'état "À imprimer"
        etat_a_imprimer = commande.etats.filter(
            enum_etat__libelle='À imprimer',
            operateur=operateur_profile,
            date_fin__isnull=True
        ).first()
        
        if not etat_a_imprimer:
            return JsonResponse({'success': False, 'message': 'Cette commande n\'est pas dans l\'état "À imprimer" ou ne vous est pas affectée'})
        
        # Effectuer la transition d'état
        with transaction.atomic():
            # Terminer l'état "À imprimer"
            etat_a_imprimer.date_fin = timezone.now()
            etat_a_imprimer.commentaire = "Impression terminée, passage automatique en préparation."
            etat_a_imprimer.save()

            # Créer ou récupérer l'état "En préparation"
            etat_en_preparation_enum, created = EnumEtatCmd.objects.get_or_create(
                libelle='En préparation',
                defaults={'ordre': 40, 'couleur': '#3B82F6'}
            )
            
            # Créer le nouvel état "En préparation"
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_en_preparation_enum,
                operateur=operateur_profile,
                date_debut=timezone.now(),
                commentaire="Commande passée automatiquement en préparation après impression."
            )
        
        return JsonResponse({
            'success': True, 
            'message': f'Commande {commande.id_yz} passée en préparation',
            'nouvel_etat': 'En préparation'
        })
        
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Profil opérateur non trouvé'})
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande non trouvée'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur: {str(e)}'})

@login_required
def modifier_commande_prepa(request, commande_id):
    """Page de modification complète d'une commande pour les opérateurs de préparation"""
    from commande.models import Commande, Operation
    from parametre.models import Ville
    
    try:
        # Récupérer l'opérateur
        operateur = Operateur.objects.get(user=request.user, type_operateur='PREPARATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de préparation non trouvé.")
        return redirect('login')
    
    # Récupérer la commande
    commande = get_object_or_404(Commande, id=commande_id)
    
    # Vérifier que la commande est affectée à cet opérateur pour la préparation
    etat_preparation = commande.etats.filter(
        Q(enum_etat__libelle='À imprimer') | Q(enum_etat__libelle='En préparation'),
        operateur=operateur,
        date_fin__isnull=True
    ).first()
    
    if not etat_preparation:
        messages.error(request, "Cette commande ne vous est pas affectée pour la préparation.")
        return redirect('Prepacommande:liste_prepa')
    
    if request.method == 'POST':
        try:
            # ================ GESTION DES ACTIONS AJAX SPÉCIFIQUES ================
            action = request.POST.get('action')
            
            if action == 'add_article':
                # Ajouter un nouvel article immédiatement
                from article.models import Article
                from commande.models import Panier
                
                article_id = request.POST.get('article_id')
                quantite = int(request.POST.get('quantite', 1))
                
                try:
                    article = Article.objects.get(id=article_id)
                    sous_total = article.prix_unitaire * quantite
                    
                    panier = Panier.objects.create(
                        commande=commande,
                        article=article,
                        quantite=quantite,
                        sous_total=sous_total
                    )
                    
                    # Recalculer le total de la commande
                    total_commande = commande.paniers.aggregate(
                        total=Sum('sous_total')
                    )['total'] or 0
                    commande.total_cmd = total_commande
                    commande.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Article ajouté avec succès',
                        'article_id': panier.id,
                        'total_commande': float(commande.total_cmd),
                        'nb_articles': commande.paniers.count(),
                    })
                    
                except Article.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Article non trouvé'
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            
            elif action == 'replace_article':
                # Remplacer un article existant
                from article.models import Article
                from commande.models import Panier
                
                ancien_article_id = request.POST.get('ancien_article_id')
                nouvel_article_id = request.POST.get('nouvel_article_id')
                nouvelle_quantite = int(request.POST.get('nouvelle_quantite', 1))
                
                try:
                    # Supprimer l'ancien panier
                    ancien_panier = Panier.objects.get(id=ancien_article_id, commande=commande)
                    ancien_panier.delete()
                    
                    # Créer le nouveau panier
                    nouvel_article = Article.objects.get(id=nouvel_article_id)
                    sous_total = nouvel_article.prix_unitaire * nouvelle_quantite
                    
                    nouveau_panier = Panier.objects.create(
                        commande=commande,
                        article=nouvel_article,
                        quantite=nouvelle_quantite,
                        sous_total=sous_total
                    )
                    
                    # Recalculer le total de la commande
                    total_commande = commande.paniers.aggregate(
                        total=Sum('sous_total')
                    )['total'] or 0
                    commande.total_cmd = total_commande
                    commande.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Article remplacé avec succès',
                        'nouvel_article_id': nouveau_panier.id,
                        'total_commande': float(commande.total_cmd),
                        'nb_articles': commande.paniers.count(),
                    })
                    
                except Panier.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Article original non trouvé'
                    })
                except Article.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Nouvel article non trouvé'
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            
            elif action == 'delete_article':
                # Supprimer un article
                from commande.models import Panier
                
                article_id = request.POST.get('article_id')
                
                try:
                    panier = Panier.objects.get(id=article_id, commande=commande)
                    panier.delete()
                    
                    # Recalculer le total de la commande
                    total_commande = commande.paniers.aggregate(
                        total=Sum('sous_total')
                    )['total'] or 0
                    commande.total_cmd = total_commande
                    commande.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Article supprimé avec succès',
                        'total_commande': float(commande.total_cmd),
                        'nb_articles': commande.paniers.count(),
                    })
                    
                except Panier.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Article non trouvé'
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            
            elif action == 'update_operation':
                # Mettre à jour une opération existante
                try:
                    from commande.models import Operation
                    import logging
                    logger = logging.getLogger(__name__)
                    
                    operation_id = request.POST.get('operation_id')
                    nouveau_commentaire = request.POST.get('nouveau_commentaire', '').strip()
                    
                    if not operation_id or not nouveau_commentaire:
                        return JsonResponse({'success': False, 'error': 'ID opération et commentaire requis'})
                    
                    # Récupérer et mettre à jour l'opération
                    operation = Operation.objects.get(id=operation_id, commande=commande)
                    operation.conclusion = nouveau_commentaire
                    operation.operateur = operateur  # Mettre à jour l'opérateur qui modifie
                    operation.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Opération mise à jour avec succès',
                        'operation_id': operation_id,
                        'nouveau_commentaire': nouveau_commentaire
                    })
                    
                except Operation.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Opération non trouvée'
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            
            elif action == 'add_operation':
                # Ajouter une nouvelle opération
                try:
                    from commande.models import Operation
                    
                    type_operation = request.POST.get('type_operation', '').strip()
                    commentaire = request.POST.get('commentaire', '').strip()
                    
                    if not type_operation or not commentaire:
                        return JsonResponse({
                            'success': False,
                            'error': 'Type d\'opération et commentaire requis'
                        })
                    
                    # Créer la nouvelle opération
                    operation = Operation.objects.create(
                        commande=commande,
                        type_operation=type_operation,
                        conclusion=commentaire,
                        operateur=operateur
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Opération ajoutée avec succès',
                        'operation_id': operation.id,
                        'type_operation': type_operation,
                        'commentaire': commentaire
                    })
                    
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            
            elif action == 'update_commande_info':
                # Mettre à jour les informations de base de la commande
                try:
                    # Récupérer les données du formulaire
                    nouvelle_adresse = request.POST.get('adresse', '').strip()
                    nouvelle_ville_id = request.POST.get('ville_id')
                    
                    # Mettre à jour l'adresse
                    if nouvelle_adresse:
                        commande.adresse = nouvelle_adresse
                    
                    # Mettre à jour la ville si fournie
                    if nouvelle_ville_id:
                        try:
                            nouvelle_ville = Ville.objects.get(id=nouvelle_ville_id)
                            commande.ville = nouvelle_ville
                        except Ville.DoesNotExist:
                            return JsonResponse({
                                'success': False,
                                'error': 'Ville non trouvée'
                            })
                    
                    commande.save()
                    
                    # Créer une opération pour consigner la modification
                    Operation.objects.create(
                        commande=commande,
                        type_operation='MODIFICATION_PREPA',
                        conclusion=f"La commande a été modifiée par l'opérateur.",
                        operateur=operateur
                    )

                    messages.success(request, f"Commande {commande.id_yz} mise à jour avec succès.")
                    return redirect('Prepacommande:detail_prepa', pk=commande.id)
                    
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            
            else:
                # Traitement du formulaire principal (non-AJAX)
                with transaction.atomic():
                    # Mettre à jour les informations du client
                    client = commande.client
                    client.nom = request.POST.get('client_nom', client.nom).strip()
                    client.prenom = request.POST.get('client_prenom', client.prenom).strip()
                    client.numero_tel = request.POST.get('client_telephone', client.numero_tel).strip()
                    client.save()

                    # Mettre à jour les informations de base de la commande
                    nouvelle_adresse = request.POST.get('adresse', '').strip()
                    nouvelle_ville_id = request.POST.get('ville_id')
                    
                    if nouvelle_adresse:
                        commande.adresse = nouvelle_adresse
                    
                    if nouvelle_ville_id:
                        try:
                            nouvelle_ville = Ville.objects.get(id=nouvelle_ville_id)
                            commande.ville = nouvelle_ville
                        except Ville.DoesNotExist:
                            messages.error(request, "Ville sélectionnée non trouvée.")
                            return redirect('Prepacommande:modifier_commande', commande_id=commande.id)
                    
                    commande.save()

                    # Créer une opération pour consigner la modification
                    Operation.objects.create(
                        commande=commande,
                        type_operation='MODIFICATION_PREPA',
                        conclusion=f"La commande a été modifiée par l'opérateur.",
                        operateur=operateur
                    )

                    messages.success(request, f"Les modifications de la commande {commande.id_yz} ont été enregistrées avec succès.")
                    return redirect('Prepacommande:detail_prepa', pk=commande.id)
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la modification: {str(e)}")
            return redirect('Prepacommande:modifier_commande', commande_id=commande.id)
    
    # Récupérer les données pour l'affichage
    paniers = commande.paniers.all().select_related('article')
    operations = commande.operations.all().select_related('operateur').order_by('-date_operation')
    villes = Ville.objects.all().order_by('nom')
    
    # Calculer le total des articles
    total_articles = sum(panier.sous_total for panier in paniers)
    
    context = {
        'page_title': f'Modifier Commande {commande.id_yz}',
        'page_subtitle': 'Modification des détails de la commande en préparation',
        'commande': commande,
        'paniers': paniers,
        'operations': operations,
        'villes': villes,
        'total_articles': total_articles,
        'operateur': operateur,
        'etat_preparation': etat_preparation,
    }
    
    return render(request, 'Prepacommande/modifier_commande.html', context)

@login_required
def api_articles_disponibles_prepa(request):
    """API pour récupérer les articles disponibles pour les opérateurs de préparation"""
    from article.models import Article
    
    try:
        # Vérifier que l'utilisateur est un opérateur de préparation
        operateur = Operateur.objects.get(user=request.user, type_operateur='PREPARATION')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Accès non autorisé'})
    
    search_query = request.GET.get('search', '')
    
    # Récupérer les articles actifs
    articles = Article.objects.filter(actif=True)
    
    if search_query:
        articles = articles.filter(
            Q(nom__icontains=search_query) |
            Q(reference__icontains=search_query) |
            Q(couleur__icontains=search_query) |
            Q(pointure__icontains=search_query)
        )
    
    # Limiter les résultats
    articles = articles[:20]
    
    articles_data = []
    for article in articles:
        articles_data.append({
            'id': article.id,
            'nom': article.nom,
            'reference': article.reference or '',
            'couleur': article.couleur,
            'pointure': article.pointure,
            'prix': float(article.prix_unitaire),
            'qte_disponible': article.qte_disponible,
            'display_text': f"{article.nom} - {article.couleur} - {article.pointure} ({article.prix_unitaire} DH)"
        })
    
    return JsonResponse({
        'success': True,
        'articles': articles_data
    })

@login_required
def api_panier_commande_prepa(request, commande_id):
    """API pour récupérer le panier d'une commande pour les opérateurs de préparation"""
    try:
        # Vérifier que l'utilisateur est un opérateur de préparation
        operateur = Operateur.objects.get(user=request.user, type_operateur='PREPARATION')
    except Operateur.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Accès non autorisé'})
    
    # Récupérer la commande
    try:
        commande = Commande.objects.get(id=commande_id)
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande non trouvée'})
    
    # Vérifier que la commande est affectée à cet opérateur
    etat_preparation = commande.etats.filter(
        Q(enum_etat__libelle='À imprimer') | Q(enum_etat__libelle='En préparation'),
        operateur=operateur,
        date_fin__isnull=True
    ).first()
    
    if not etat_preparation:
        return JsonResponse({'success': False, 'message': 'Commande non affectée'})
    
    # Récupérer les paniers
    paniers = commande.paniers.all().select_related('article')
    
    paniers_data = []
    for panier in paniers:
        paniers_data.append({
            'id': panier.id,
            'article_id': panier.article.id,
            'article_nom': panier.article.nom,
            'article_reference': panier.article.reference or '',
            'article_couleur': panier.article.couleur,
            'article_pointure': panier.article.pointure,
            'quantite': panier.quantite,
            'prix_unitaire': float(panier.article.prix_unitaire),
            'sous_total': float(panier.sous_total),
            'display_text': f"{panier.article.nom} - {panier.article.couleur} - {panier.article.pointure}"
        })
    
    return JsonResponse({
        'success': True,
        'paniers': paniers_data,
        'total_commande': float(commande.total_cmd),
        'nb_articles': len(paniers_data)
    })
