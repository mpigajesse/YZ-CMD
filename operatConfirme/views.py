from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from commande.models import Commande
from django.contrib import messages
from django.contrib.auth.models import User, Group
from parametre.models import Operateur, Ville # Assurez-vous que ce chemin est correct
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm # Importez PasswordChangeForm
from django.http import JsonResponse
import json
from django.utils import timezone
from commande.models import Commande, EtatCommande, EnumEtatCmd, Panier
from datetime import datetime, timedelta
from django.db.models import Sum
from django.db import models, transaction
from client.models import Client
from article.models import Article, VarianteArticle
import logging
from django.urls import reverse
from django.template.loader import render_to_string
# Suppression de l'app notifications: retirer les imports

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
        Q(etats__operateur=operateur, etats__date_fin__isnull=True, etats__enum_etat__libelle__in=['Affectée', 'En cours de confirmation']) |
        Q(etats__date_fin__isnull=True, etats__enum_etat__libelle='Retour Confirmation')
    ).distinct().select_related(
        'client', 'ville', 'ville__region'
    ).prefetch_related(
        'etats__enum_etat', 'paniers__article'
    ).order_by('-date_cmd', '-date_creation')
    
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
    
    # Commandes retournées par la préparation
    stats['commandes_retournees'] = Commande.objects.filter(
        etats__enum_etat__libelle='Retour Confirmation',
        etats__date_fin__isnull=True
    ).distinct().count()
    
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

    # Commandes annulées par cet opérateur
    stats['commandes_annulees'] = Commande.objects.filter(
        etats__operateur=operateur,
        etats__enum_etat__libelle='Annulée'
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
    
    # Commandes à afficher :
    # Celles qui sont explicitement affectées à l'opérateur avec un état actif.
    commandes_list = Commande.objects.filter(
        etats__operateur=operateur,
        etats__date_fin__isnull=True,
        etats__enum_etat__libelle__in=['Affectée', 'En cours de confirmation', 'Retour Confirmation']
    ).distinct().select_related(
        'client', 'ville', 'ville__region'
    ).prefetch_related(
        'etats__enum_etat', 'paniers__article'
    ).order_by('-etats__date_debut')
    
    # Recherche
    search_query = request.GET.get('search', '').strip()
    if search_query:
        commandes_list = commandes_list.filter(
            Q(id_yz__icontains=search_query) |
            Q(num_cmd__icontains=search_query) |
            Q(client__nom__icontains=search_query) |
            Q(client__prenom__icontains=search_query) |
            Q(client__numero_tel__icontains=search_query) |
            Q(ville__nom__icontains=search_query) |
            Q(adresse__icontains=search_query)
        )
    
    # Statistiques pour l'affichage des onglets/badges
    stats = {
        'en_attente': Commande.objects.filter(
            etats__operateur=operateur, 
            etats__date_fin__isnull=True, 
            etats__enum_etat__libelle='Affectée'
        ).distinct().count(),
        
        'en_cours': Commande.objects.filter(
        etats__operateur=operateur,
            etats__date_fin__isnull=True, 
            etats__enum_etat__libelle='En cours de confirmation'
        ).distinct().count(),
    
        'retournees': Commande.objects.filter(
        etats__operateur=operateur,
            etats__date_fin__isnull=True, 
            etats__enum_etat__libelle='Retour Confirmation'
        ).distinct().count()
    }
    stats['total'] = stats['en_attente'] + stats['en_cours'] + stats['retournees']

    # Filtrage par onglet
    tab = request.GET.get('tab', 'toutes')
    tab_map = {
        'en_attente': {'libelle': 'Affectée', 'display': 'En Attente'},
        'en_cours': {'libelle': 'En cours de confirmation', 'display': 'En Cours'},
        'retournees': {'libelle': 'Retour Confirmation', 'display': 'Retournées'},
    }
    
    current_tab_display_name = "Toutes"
    if tab in tab_map:
        commandes_list = commandes_list.filter(etats__operateur=operateur, etats__enum_etat__libelle=tab_map[tab]['libelle'], etats__date_fin__isnull=True)
        current_tab_display_name = tab_map[tab]['display']
    
    # Pagination
    paginator = Paginator(commandes_list, 15)  # 15 commandes par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Mes Commandes à Confirmer',
        'page_subtitle': f"Gestion des commandes qui vous sont affectées ou retournées.",
        'page_obj': page_obj,
        'search_query': search_query,
        'operateur': operateur,
        'stats': stats,
        'current_tab': tab,
        'current_tab_display_name': current_tab_display_name
    }
    
    return render(request, 'operatConfirme/liste_commande.html', context)

@login_required
def confirmer_commande_ajax(request, commande_id):
    """Confirme une commande spécifique via AJAX depuis la page de confirmation"""
    from commande.models import Commande, EtatCommande, EnumEtatCmd, Operation
    from article.models import Article
    from django.http import JsonResponse
    from django.utils import timezone
    from django.db import transaction
    
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
        
        # Vérifier que la commande n'est pas déjà confirmée
        if etat_actuel.enum_etat.libelle == 'Confirmée':
            return JsonResponse({'success': False, 'message': 'Cette commande est déjà confirmée.'})
            
        # Vérifier qu'au moins une opération a été effectuée
        operations_effectuees = Operation.objects.filter(
            commande=commande,
            operateur=operateur,
            type_operation__in=[
                'APPEL', 'Appel Whatsapp', 'Message Whatsapp', 'Vocal Whatsapp', 'ENVOI_SMS'
            ]
        ).exists()
        
        if not operations_effectuees:
            return JsonResponse({
                'success': False, 
                'message': 'Vous devez effectuer au moins une opération (appel, message, etc.) avant de confirmer la commande.'
            })
        
        # Utiliser une transaction pour la confirmation et la décrémentation du stock
        with transaction.atomic():
            print(f"🎯 DEBUG: Début de la confirmation de la commande {commande.id_yz}")
            
            # IMPORTANT: Récupérer et sauvegarder les informations de livraison depuis le formulaire
            # Ces informations doivent être envoyées avec la requête de confirmation
            try:
                if 'ville_livraison' in data and data['ville_livraison']:
                    from parametre.models import Ville
                    nouvelle_ville = Ville.objects.get(id=data['ville_livraison'])
                    commande.ville = nouvelle_ville
                    print(f"🏙️ DEBUG: Ville de livraison mise à jour: {nouvelle_ville.nom}")
                
                if 'adresse_livraison' in data:
                    commande.adresse = data['adresse_livraison']
                    print(f"📍 DEBUG: Adresse de livraison mise à jour: {data['adresse_livraison'][:50]}...")
                
                # Sauvegarder les modifications de la commande
                commande.save()
                print(f"💾 DEBUG: Informations de livraison sauvegardées")
                
            except Ville.DoesNotExist:
                print(f"❌ DEBUG: Ville de livraison non trouvée: {data.get('ville_livraison')}")
            except Exception as e:
                print(f"⚠️ DEBUG: Erreur lors de la sauvegarde des infos de livraison: {str(e)}")
            
            # Vérifier le stock et décrémenter les articles
            articles_decrémentes = []
            stock_insuffisant = []
            
            for panier in commande.paniers.all():
                article = panier.article
                quantite_commandee = panier.quantite
                
                print(f"📦 DEBUG: Article {article.nom} (ID:{article.id})")
                print(f"   - Stock actuel: {article.qte_disponible}")
                print(f"   - Quantité commandée: {quantite_commandee}")
                
                # Vérifier si le stock est suffisant
                if article.qte_disponible < quantite_commandee:
                    stock_insuffisant.append({
                        'article': article.nom,
                        'stock_actuel': article.qte_disponible,
                        'quantite_demandee': quantite_commandee
                    })
                    print(f"❌ DEBUG: Stock insuffisant pour {article.nom}")
                else:
                    # Décrémenter le stock via mouvements sur variantes (pas d'écriture sur Article.qte_disponible)
                    ancien_stock = article.qte_disponible
                    from Superpreparation.utils import creer_mouvement_stock as creer_mouvement_stock_prepa
                    creer_mouvement_stock_prepa(
                        article=article,
                        quantite=quantite_commandee,
                        type_mouvement='ajustement_neg' if quantite_commandee > 0 else 'ajustement_pos',
                        operateur=operateur,
                        commande=commande,
                        commentaire=f"Décrément lors de la confirmation commande {commande.id_yz}",
                        variante=None,
                    )
                    nouveau_stock = article.qte_disponible  # Propriété calculée à partir des variantes
                    
                    articles_decrémentes.append({
                        'article': article.nom,
                        'ancien_stock': ancien_stock,
                        'nouveau_stock': nouveau_stock,
                        'quantite_decrémententée': quantite_commandee
                    })
                    
                    print(f"✅ DEBUG: Stock mis à jour pour {article.nom}")
                    print(f"   - Ancien stock: {ancien_stock}")
                    print(f"   - Nouveau stock: {nouveau_stock}")
            
            # Si il y a des problèmes de stock, annuler la transaction
            if stock_insuffisant:
                error_msg = f"Stock insuffisant pour : "
                for item in stock_insuffisant:
                    error_msg += f"\n• {item['article']}: Stock={item['stock_actuel']}, Demandé={item['quantite_demandee']}"
                
                print(f"❌ DEBUG: Confirmation annulée - problèmes de stock")
                for item in stock_insuffisant:
                    print(f"   - {item['article']}: {item['stock_actuel']}/{item['quantite_demandee']}")
                
                return JsonResponse({
                    'success': False, 
                    'message': error_msg,
                    'stock_insuffisant': stock_insuffisant
                })
            
            # Créer le nouvel état "confirmée"
            enum_confirmee = EnumEtatCmd.objects.get(libelle='Confirmée')
            
            # Fermer l'état actuel
            etat_actuel.date_fin = timezone.now()
            etat_actuel.save()
            print(f"🔄 DEBUG: État actuel fermé: {etat_actuel.enum_etat.libelle}")
            
            # Créer le nouvel état Confirmée (historisation courte)
            nouvel_etat = EtatCommande.objects.create(
                commande=commande,
                enum_etat=enum_confirmee,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=commentaire
            )
            print(f"✅ DEBUG: Nouvel état créé: Confirmée")

            # Immédiatement basculer en file de préparation pour les superviseurs
            try:
                # Clore l'état Confirmée pour n'avoir qu'un état actif
                nouvel_etat.date_fin = timezone.now()
                nouvel_etat.save(update_fields=['date_fin'])

                # Créer l'état "À imprimer" (état d'entrée pour la préparation)
                enum_a_imprimer = EnumEtatCmd.objects.get(libelle='À imprimer')
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=enum_a_imprimer,
                    # On n'assigne pas d'opérateur spécifique: visible à tous les superviseurs
                    date_debut=timezone.now(),
                    commentaire=f"Commande reçue de la confirmation par {operateur.nom_complet}"
                )
                print("📨 DEBUG: État 'À imprimer' créé pour file préparation (superviseurs)")
            except EnumEtatCmd.DoesNotExist:
                print("⚠️ DEBUG: État 'À imprimer' introuvable. La commande reste en 'Confirmée'.")
            
            # Log des articles décrémernts
            print(f"📊 DEBUG: Résumé de la décrémentation:")
            print(f"   - {len(articles_decrémentes)} article(s) décrémenté(s)")
            for item in articles_decrémentes:
                print(f"   - {item['article']}: {item['ancien_stock']} → {item['nouveau_stock']} (-{item['quantite_decrémententée']})")
        
        return JsonResponse({
            'success': True, 
            'message': f'Commande {commande.id_yz} confirmée avec succès.',
            'articles_decrémentes': len(articles_decrémentes),
            'details_stock': articles_decrémentes,
            'redirect_url': '/operateur-confirme/confirmation/'
        })
        
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Commande non trouvée.'})
    except EnumEtatCmd.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'État "Confirmée" non trouvé dans la configuration.'})
    except Exception as e:
        print(f"❌ DEBUG: Erreur lors de la confirmation: {str(e)}")
        import traceback
        traceback.print_exc()
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
    from django.utils import timezone
    from datetime import timedelta
    
    try:
        # Vérifier que l'utilisateur est connecté
        if not request.user.is_authenticated:
            from django.contrib import messages
            messages.error(request, 'Vous devez être connecté pour accéder à cette page.')
            return redirect('login')
        
        # Récupérer l'objet Operateur correspondant à l'utilisateur connecté
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
        
        # Récupérer seulement les commandes confirmées par cet opérateur
        mes_commandes_confirmees = Commande.objects.filter(
            etats__enum_etat__libelle='Confirmée',
            etats__operateur=operateur  # Inclure même si l'état Confirmée est clôturé
        ).select_related('client', 'ville', 'ville__region').prefetch_related('etats', 'operations').distinct()
        

        
        # Tri par date de confirmation (plus récentes en premier)
        mes_commandes_confirmees = mes_commandes_confirmees.order_by('-etats__date_debut')
        
        # Calcul des statistiques
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        
        stats = {}
        stats['total_confirmees'] = mes_commandes_confirmees.count()
        
        # Valeur totale des commandes confirmées
        valeur_totale = mes_commandes_confirmees.aggregate(
            total=Sum('total_cmd')
        )['total'] or 0
        stats['valeur_totale'] = valeur_totale
        
        # Commandes confirmées cette semaine
        stats['confirmees_semaine'] = mes_commandes_confirmees.filter(
            etats__date_debut__date__gte=week_start,
            etats__enum_etat__libelle='Confirmée'
        ).count()
        
        # Commandes confirmées aujourd'hui
        stats['confirmees_aujourdhui'] = mes_commandes_confirmees.filter(
            etats__date_debut__date=today,
            etats__enum_etat__libelle='Confirmée'
        ).count()
        
    except Operateur.DoesNotExist:
        # Si l'utilisateur n'est pas un opérateur de confirmation, afficher notification JS
        mes_commandes_confirmees = Commande.objects.none()
        stats = {
            'total_confirmees': 0,
            'valeur_totale': 0,
            'confirmees_semaine': 0,
            'confirmees_aujourdhui': 0
        }
        # Ajouter un flag pour déclencher la notification côté client
        context = {
            'mes_commandes_confirmees': mes_commandes_confirmees,
            'stats': stats,
            'show_unauthorized_message': True,
            'user_username': request.user.username
        }
        return render(request, 'operatConfirme/commandes_confirmees.html', context)
    
    context = {
        'mes_commandes_confirmees': mes_commandes_confirmees,
        'stats': stats,
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
    """Page de changement de mot de passe pour l'opérateur de confirmation - Désactivée"""
    return redirect('operatConfirme:profile')

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
                    'message': f'{confirmed_count} commande(s) confirmée(s) avec succès',
                    'redirect_url': reverse('operatConfirme:confirmation')
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
            redirect_url = None
            
            # État "En cours de confirmation"
            try:
                etat_en_cours = EnumEtatCmd.objects.get(libelle='En cours de confirmation')
            except EnumEtatCmd.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'État "En cours de confirmation" non trouvé dans le système'
                })
            
            # Si une seule commande est lancée, préparer l'URL de redirection
            if len(commande_ids) == 1:
                redirect_url = reverse('operatConfirme:modifier_commande', args=[commande_ids[0]])

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
                response_data = {
                    'success': True,
                    'message': f'{launched_count} confirmation(s) lancée(s) avec succès'
                }
                if redirect_url:
                    response_data['redirect_url'] = redirect_url
                return JsonResponse(response_data)
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
def annuler_commande_confirmation(request, commande_id):
    """Vue pour annuler définitivement une commande (En cours de confirmation -> Annulée)"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            motif = data.get('motif', '').strip()
            
            if not motif:
                return JsonResponse({
                    'success': False,
                    'message': 'Le motif d\'annulation est obligatoire'
                })
            
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
            
            # Vérifier que la commande est dans l'état "En cours de confirmation" ou "Affectée"
            etat_actuel = commande.etats.filter(
                operateur=operateur,
                date_fin__isnull=True
            ).first()
            
            if not etat_actuel:
                return JsonResponse({
                    'success': False,
                    'message': 'Cette commande ne vous est pas affectée'
                })
            
            if etat_actuel.enum_etat.libelle.lower() == 'annulée':
                return JsonResponse({
                    'success': True,
                    'message': 'La commande est déjà annulée'
                })
            
            # Autoriser l'annulation depuis "En cours de confirmation" ou "Affectée"
            etats_autorises = ['en cours de confirmation', 'affectée']
            if etat_actuel.enum_etat.libelle.lower() not in etats_autorises:
                return JsonResponse({
                    'success': False,
                    'message': f'Cette commande est en état "{etat_actuel.enum_etat.libelle}" et ne peut pas être annulée depuis cet état'
                })
            
            # Récupérer ou créer l'état "Annulée"
            etat_annulee, created = EnumEtatCmd.objects.get_or_create(
                libelle='Annulée',
                defaults={'ordre': 70, 'couleur': '#EF4444'}
            )
            
            # Terminer l'état actuel
            etat_actuel.date_fin = timezone.now()
            etat_actuel.save()
            
            # Créer le nouvel état "Annulée"
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat_annulee,
                operateur=operateur,
                date_debut=timezone.now(),
                commentaire=f"Commande annulée par l'opérateur de confirmation - Motif: {motif}"
            )
            
            # Sauvegarder le motif d'annulation dans la commande
            commande.motif_annulation = motif
            commande.save()
            
            # Créer une opération d'annulation
            from commande.models import Operation
            Operation.objects.create(
                commande=commande,
                type_operation='ANNULATION',
                conclusion=motif,
                operateur=operateur
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Commande {commande.id_yz} annulée définitivement. Motif: {motif}'
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
def modifier_commande(request, commande_id):
    """Page de modification complète d'une commande pour les opérateurs de confirmation"""
    from commande.models import Commande, Operation
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
            # ================ GESTION DES ACTIONS AJAX SPÉCIFIQUES ================
            action = request.POST.get('action')
            
            if action == 'add_article':
                # Ajouter un nouvel article immédiatement
                from article.models import Article, VarianteArticle
                from commande.models import Panier
                
                article_id = request.POST.get('article_id')
                quantite = int(request.POST.get('quantite', 1))
                variante_id = request.POST.get('variante_id')  # Nouveau paramètre
                
                print(f"📦 Ajout article: ID={article_id}, Qté={quantite}, Variante={variante_id}")
                
                try:
                    # D'abord, essayer de trouver l'article directement
                    article = None
                    variante_id_int = None
                    
                    try:
                        article = Article.objects.get(id=article_id, actif=True)
                        # Convertir variante_id en entier ou None
                        variante_id_int = int(variante_id) if variante_id and variante_id != 'null' and variante_id != '' else None
                        print(f"✅ Article trouvé directement: {article.nom}")
                    except Article.DoesNotExist:
                        # Si pas trouvé comme Article, peut-être que c'est l'ID d'une variante
                        try:
                            variante = VarianteArticle.objects.get(id=article_id, actif=True)
                            article = variante.article
                            variante_id_int = variante.id
                            print(f"✅ Variante trouvée: {variante} -> Article: {article.nom}")
                        except VarianteArticle.DoesNotExist:
                            raise Article.DoesNotExist(f"Ni article ni variante trouvé avec l'ID {article_id}")
                    
                    if not article or not article.actif:
                        raise Article.DoesNotExist(f"Article inactif ou introuvable")
                    
                                        # Vérifier si l'article avec cette variante existe déjà dans la commande
                    if variante_id_int:
                        variante_obj = VarianteArticle.objects.get(id=variante_id_int)
                        panier_existant = Panier.objects.filter(
                            commande=commande, 
                            article=article, 
                            variante=variante_obj
                        ).first()
                    else:
                        variante_obj = None
                        panier_existant = Panier.objects.filter(
                            commande=commande, 
                            article=article, 
                            variante__isnull=True
                        ).first()
                    
                    if panier_existant:
                        # Si l'article existe déjà, mettre à jour la quantité
                        panier_existant.quantite += quantite
                        panier_existant.save()
                        panier = panier_existant
                        print(f"🔄 Article existant mis à jour: ID={article.id}, nouvelle quantité={panier.quantite}")
                    else:
                        # Si l'article n'existe pas, créer un nouveau panier
                        variante_obj = None
                        if variante_id_int:
                            variante_obj = VarianteArticle.objects.get(id=variante_id_int)
                        
                        panier = Panier.objects.create(
                            commande=commande,
                            article=article,
                            quantite=quantite,
                            sous_total=0,  # Sera recalculé après
                            variante=variante_obj
                        )
                        print(f"➕ Nouvel article ajouté: ID={article.id}, quantité={quantite}")
                    
                    # Recalculer le compteur après ajout
                    if article.isUpsell and hasattr(article, 'prix_upsell_1') and article.prix_upsell_1 is not None:
                        # Compter la quantité totale d'articles upsell (après ajout)
                        from django.db.models import Sum
                        total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(
                            total=Sum('quantite')
                        )['total'] or 0
                        
                        # Le compteur ne s'incrémente qu'à partir de 2 unités d'articles upsell
                        # 0-1 unités upsell → compteur = 0
                        # 2+ unités upsell → compteur = total_quantite_upsell - 1
                        if total_quantite_upsell >= 2:
                            commande.compteur = total_quantite_upsell - 1
                        else:
                            commande.compteur = 0
                        
                        commande.save()
                        
                        # Recalculer TOUS les articles de la commande avec le nouveau compteur
                        commande.recalculer_totaux_upsell()
                    else:
                        # Pour les articles normaux, juste calculer le sous-total
                        from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
                        prix_unitaire = get_prix_upsell_avec_compteur(article, commande.compteur)
                        sous_total = prix_unitaire * panier.quantite
                        panier.sous_total = float(sous_total)
                        panier.save()
                    
                    # Recalculer le total de la commande
                    total_commande = commande.paniers.aggregate(
                        total=models.Sum('sous_total')
                    )['total'] or 0
                    commande.total_cmd = float(total_commande)
                    commande.save()
                    
                    # Déterminer si c'était un ajout ou une mise à jour
                    message = 'Article ajouté avec succès' if not panier_existant else f'Quantité mise à jour ({panier.quantite})'
                    
                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'article_id': panier.id,
                        'total_commande': float(commande.total_cmd),
                        'nb_articles': commande.paniers.count(),
                        'compteur': commande.compteur,
                        'was_update': panier_existant is not None,
                        'new_quantity': panier.quantite
                    })
                    
                except Article.DoesNotExist as e:
                    return JsonResponse({
                        'success': False,
                        'error': f'Article ou variante avec l\'ID {article_id} non trouvé ou désactivé. {str(e)}'
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
                    # Supprimer l'ancien panier et décrémenter le compteur
                    ancien_panier = Panier.objects.get(id=ancien_article_id, commande=commande)
                    ancien_article = ancien_panier.article
                    
                    # Sauvegarder les infos avant suppression
                    ancien_etait_upsell = ancien_article.isUpsell
                    
                    # Supprimer l'ancien panier
                    ancien_panier.delete()
                    
                    # Créer le nouveau panier
                    nouvel_article = Article.objects.get(id=nouvel_article_id)
                    
                    # Recalculer le compteur après remplacement
                    from django.db.models import Sum
                    total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(
                        total=Sum('quantite')
                    )['total'] or 0
                    
                    # Ajouter la quantité si le nouvel article est upsell
                    if nouvel_article.isUpsell:
                        total_quantite_upsell += nouvelle_quantite
                    
                    # Appliquer la logique : compteur = max(0, total_quantite_upsell - 1)
                    if total_quantite_upsell >= 2:
                        commande.compteur = total_quantite_upsell - 1
                    else:
                        commande.compteur = 0
                    
                    commande.save()
                    
                    # Recalculer TOUS les articles de la commande avec le nouveau compteur
                    commande.recalculer_totaux_upsell()
                    
                    # Calculer le sous-total selon le compteur de la commande
                    from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
                    prix_unitaire = get_prix_upsell_avec_compteur(nouvel_article, commande.compteur)
                    sous_total = prix_unitaire * nouvelle_quantite
                    
                    nouveau_panier = Panier.objects.create(
                        commande=commande,
                        article=nouvel_article,
                        quantite=nouvelle_quantite,
                        sous_total=float(sous_total)
                    )
                    
                    # Recalculer le total de la commande
                    total_commande = commande.paniers.aggregate(
                        total=models.Sum('sous_total')
                    )['total'] or 0
                    commande.total_cmd = float(total_commande)
                    commande.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Article remplacé avec succès',
                        'nouvel_article_id': nouveau_panier.id,
                        'total_commande': float(commande.total_cmd),
                        'nb_articles': commande.paniers.count(),
                        'compteur': commande.compteur
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
            
            elif action == 'delete_panier':
                # Supprimer un article
                from commande.models import Panier
                
                panier_id = request.POST.get('panier_id')
                
                try:
                    panier = Panier.objects.get(id=panier_id, commande=commande)
                    
                    # Sauvegarder l'info avant suppression
                    etait_upsell = panier.article.isUpsell
                    
                    # Supprimer l'article
                    panier.delete()
                    
                    # Recalculer le compteur après suppression
                    if etait_upsell:
                        # Compter la quantité totale d'articles upsell restants (après suppression)
                        from django.db.models import Sum
                        total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(
                            total=Sum('quantite')
                        )['total'] or 0
                        
                        # Le compteur ne s'incrémente qu'à partir de 2 unités d'articles upsell
                        # 0-1 unités upsell → compteur = 0
                        # 2+ unités upsell → compteur = total_quantite_upsell - 1
                        if total_quantite_upsell >= 2:
                            commande.compteur = total_quantite_upsell - 1
                        else:
                            commande.compteur = 0
                        
                        commande.save()
                        
                        # Recalculer TOUS les articles de la commande avec le nouveau compteur
                        commande.recalculer_totaux_upsell()
                    
                    # Recalculer le total de la commande
                    total_commande = commande.paniers.aggregate(
                        total=models.Sum('sous_total')
                    )['total'] or 0
                    commande.total_cmd = float(total_commande)
                    commande.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Article supprimé avec succès',
                        'total_commande': float(commande.total_cmd),
                        'nb_articles': commande.paniers.count(),
                        'compteur': commande.compteur
                    })
                    
                except Panier.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'Article avec l\'ID panier {panier_id} non trouvé dans cette commande'
                    })
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            
            elif action == 'save_client_info':
                # Sauvegarder les informations du client
                nom = request.POST.get('nom')
                prenom = request.POST.get('prenom')
                telephone = request.POST.get('telephone')

                try:
                    client = commande.client
                    client.nom = nom
                    client.prenom = prenom
                    client.numero_tel = telephone
                    client.save()
                    return JsonResponse({'success': True, 'message': 'Informations client sauvegardées'})
                except Exception as e:
                    return JsonResponse({'success': False, 'error': str(e)})
            
            elif action == 'update_quantity':
                # Modifier la quantité d'un article
                from commande.models import Panier
                
                panier_id = request.POST.get('panier_id')
                nouvelle_quantite = int(request.POST.get('nouvelle_quantite', 1))
                
                try:
                    panier = Panier.objects.get(id=panier_id, commande=commande)
                    ancienne_quantite = panier.quantite
                    etait_upsell = panier.article.isUpsell
                    
                    # Modifier la quantité
                    panier.quantite = nouvelle_quantite
                    panier.save()
                    
                    # Recalculer le compteur si c'était un article upsell
                    if etait_upsell:
                        # Compter la quantité totale d'articles upsell (après modification)
                        from django.db.models import Sum
                        total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(
                            total=Sum('quantite')
                        )['total'] or 0
                        
                        # Le compteur ne s'incrémente qu'à partir de 2 unités d'articles upsell
                        if total_quantite_upsell >= 2:
                            commande.compteur = total_quantite_upsell - 1
                        else:
                            commande.compteur = 0
                        
                        commande.save()
                        
                        # Recalculer TOUS les articles de la commande avec le nouveau compteur
                        commande.recalculer_totaux_upsell()
                    else:
                        # Pour les articles normaux, juste recalculer le sous-total
                        from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
                        prix_unitaire = get_prix_upsell_avec_compteur(panier.article, commande.compteur)
                        panier.sous_total = float(prix_unitaire * nouvelle_quantite)
                        panier.save()
                    
                    # Recalculer le total de la commande
                    total_commande = commande.paniers.aggregate(
                        total=models.Sum('sous_total')
                    )['total'] or 0
                    commande.total_cmd = float(total_commande)
                    commande.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': f'Quantité modifiée de {ancienne_quantite} à {nouvelle_quantite}',
                        'sous_total': float(panier.sous_total),
                        'total_commande': float(commande.total_cmd),
                        'compteur': commande.compteur
                    })
                    
                except Panier.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'Article avec l\'ID panier {panier_id} non trouvé dans cette commande'
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
                    
                    print(f"🔄 DEBUG: Mise à jour opération {operation_id} pour commande {commande.id}")
                    print(f"📝 DEBUG: Nouveau commentaire: '{nouveau_commentaire}'")
                    print(f"🔍 DEBUG: Données POST reçues: {dict(request.POST)}")
                    
                    if not operation_id or not nouveau_commentaire:
                        print(f"❌ DEBUG: Données manquantes - operation_id: '{operation_id}', commentaire: '{nouveau_commentaire}'")
                        return JsonResponse({'success': False, 'error': 'ID opération et commentaire requis'})
                    
                    # Récupérer et mettre à jour l'opération
                    operation = Operation.objects.get(id=operation_id, commande=commande)
                    ancien_commentaire = operation.conclusion
                    
                    print(f"📋 DEBUG: Ancien commentaire: '{ancien_commentaire}'")
                    
                    operation.conclusion = nouveau_commentaire
                    operation.operateur = operateur  # Mettre à jour l'opérateur qui modifie
                    operation.save()
                    
                    print(f"✅ DEBUG: Opération {operation_id} sauvegardée en base de données")
                    
                    # Vérification post-sauvegarde
                    operation_verif = Operation.objects.get(id=operation_id)
                    print(f"🔍 DEBUG: Vérification en base: conclusion = '{operation_verif.conclusion}'")
                    
                    # Vérifier toutes les opérations de cette commande
                    toutes_operations = Operation.objects.filter(commande=commande)
                    print(f"📊 DEBUG: {toutes_operations.count()} opération(s) totales pour cette commande:")
                    for op in toutes_operations:
                        print(f"   - ID {op.id}: {op.type_operation} - '{op.conclusion}'")
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Opération mise à jour avec succès en base de données',
                        'operation_id': operation_id,
                        'nouveau_commentaire': nouveau_commentaire,
                        'ancien_commentaire': ancien_commentaire,
                        'debug_info': {
                            'verification_conclusion': operation_verif.conclusion,
                            'total_operations': toutes_operations.count()
                        }
                    })
                    
                except Operation.DoesNotExist:
                    print(f"❌ DEBUG: Opération {operation_id} introuvable pour commande {commande.id}")
                    return JsonResponse({'success': False, 'error': 'Opération introuvable'})
                except Exception as e:
                    print(f"❌ DEBUG: Erreur mise à jour opération: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return JsonResponse({'success': False, 'error': str(e)})
            
            elif action == 'create_operation':
                # Créer une nouvelle opération immédiatement
                try:
                    from commande.models import Operation
                    
                    type_operation = request.POST.get('type_operation')
                    commentaire = request.POST.get('commentaire', '').strip()
                    
                    print(f"🆕 DEBUG: Création nouvelle opération pour commande {commande.id}")
                    print(f"📝 DEBUG: Type: '{type_operation}', Commentaire: '{commentaire}'")
                    print(f"🔍 DEBUG: Données POST reçues: {dict(request.POST)}")
                    
                    if not type_operation or not commentaire:
                        print(f"❌ DEBUG: Données manquantes - type: '{type_operation}', commentaire: '{commentaire}'")
                        return JsonResponse({'success': False, 'error': 'Type d\'opération et commentaire requis'})
                    
                    # Créer la nouvelle opération
                    nouvelle_operation = Operation.objects.create(
                        type_operation=type_operation,
                        conclusion=commentaire,
                        commande=commande,
                        operateur=operateur
                    )
                    
                    print(f"✅ DEBUG: Nouvelle opération créée avec ID: {nouvelle_operation.id}")
                    
                    # Vérifier toutes les opérations de cette commande
                    toutes_operations = Operation.objects.filter(commande=commande)
                    print(f"📊 DEBUG: {toutes_operations.count()} opération(s) totales pour cette commande:")
                    for op in toutes_operations:
                        print(f"   - ID {op.id}: {op.type_operation} - '{op.conclusion}'")
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Nouvelle opération créée avec succès en base de données',
                        'operation_id': nouvelle_operation.id,
                        'type_operation': nouvelle_operation.type_operation,
                        'commentaire': nouvelle_operation.conclusion,
                        'debug_info': {
                            'total_operations': toutes_operations.count(),
                            'operation_date': nouvelle_operation.date_operation.strftime('%d/%m/%Y %H:%M')
                        }
                    })
                    
                except Exception as e:
                    print(f"❌ DEBUG: Erreur création opération: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    return JsonResponse({'success': False, 'error': str(e)})
            
            elif action == 'save_livraison':
                # Sauvegarder les informations de livraison (ville + adresse)
                try:
                    ville_id = request.POST.get('ville_livraison')
                    adresse = request.POST.get('adresse_livraison', '').strip()
                    
                    # Mettre à jour la ville de livraison si fournie
                    if ville_id:
                        try:
                            nouvelle_ville = Ville.objects.get(id=ville_id)
                            commande.ville = nouvelle_ville
                        except Ville.DoesNotExist:
                            return JsonResponse({'success': False, 'error': 'Ville de livraison invalide'})
                    
                    # Mettre à jour l'adresse (pas obligatoire)
                    commande.adresse = adresse
                    
                    # Recalculer le total avec les nouveaux frais de livraison
                    sous_total_articles = commande.sous_total_articles
                    frais_livraison = commande.ville.frais_livraison if commande.ville else 0
                    # Convertir explicitement en float pour éviter l'erreur Decimal + float
                    nouveau_total = float(sous_total_articles) 
                    commande.total_cmd = float(nouveau_total)
                    
                    # Sauvegarder les modifications
                    commande.save()
                    
                    # Préparer le message de succès
                    elements_sauvegardes = []
                    if ville_id:
                        elements_sauvegardes.append(f"ville: {commande.ville.nom}")
                    if adresse:
                        elements_sauvegardes.append(f"adresse: {adresse[:50]}{'...' if len(adresse) > 50 else ''}")
                    
                    if elements_sauvegardes:
                        message = f"Informations de livraison sauvegardées ({', '.join(elements_sauvegardes)})"
                    else:
                        message = 'Section livraison validée'
                    
                    return JsonResponse({
                        'success': True,
                        'message': message,
                        'ville_nom': commande.ville.nom if commande.ville else None,
                        'region_nom': commande.ville.region.nom_region if commande.ville and commande.ville.region else None,
                        'frais_livraison': commande.ville.frais_livraison if commande.ville else None,
                        'adresse': adresse,
                        'nouveau_total': nouveau_total,
                        'sous_total_articles': sous_total_articles
                    })
                    
                except Exception as e:
                    return JsonResponse({'success': False, 'error': str(e)})
            
            elif action == 'update_article':
                # Action pour mettre à jour un article (quantité ou article lui-même)
                from article.models import Article
                from commande.models import Panier
                
                panier_id = request.POST.get('panier_id')
                nouvel_article_id = request.POST.get('article_id')
                nouvelle_quantite = int(request.POST.get('quantite', 1))

                try:
                    # Récupérer le panier à modifier et le nouvel article
                    panier_a_modifier = Panier.objects.get(id=panier_id, commande=commande)
                    nouvel_article = Article.objects.get(id=nouvel_article_id)
                    
                    # Vérifier si un autre panier avec le nouvel article existe déjà
                    panier_existant = Panier.objects.filter(
                        commande=commande, 
                        article=nouvel_article
                    ).exclude(id=panier_id).first()

                    if panier_existant:
                        # Fusionner les quantités et supprimer l'ancien panier
                        panier_existant.quantite += nouvelle_quantite
                        panier_existant.save()
                        panier_a_modifier.delete()
                        print(f"🔄 Articles fusionnés: ID={nouvel_article.id}, nouvelle qté={panier_existant.quantite}")
                    else:
                        # Mettre à jour le panier existant
                        panier_a_modifier.article = nouvel_article
                        panier_a_modifier.quantite = nouvelle_quantite
                        panier_a_modifier.save()
                        print(f"✍️ Article mis à jour: Panier ID={panier_id}, Article ID={nouvel_article.id}, Qté={nouvelle_quantite}")

                    # Recalculer tous les totaux de la commande
                    commande.recalculer_totaux_upsell()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Article mis à jour avec succès',
                        'total_commande': float(commande.total_cmd),
                        'nb_articles': commande.paniers.count(),
                        'compteur': commande.compteur
                    })
                    
                except Panier.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Article original non trouvé dans le panier'}, status=404)
                except Article.DoesNotExist:
                    return JsonResponse({'success': False, 'error': 'Nouvel article non trouvé'}, status=404)
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    return JsonResponse({'success': False, 'error': str(e)}, status=500)

            elif action == 'replace_article':
                # Remplacer un article existant
                from article.models import Article
                from commande.models import Panier
                
                ancien_article_id = request.POST.get('ancien_article_id')
                nouvel_article_id = request.POST.get('nouvel_article_id')
                nouvelle_quantite = int(request.POST.get('nouvelle_quantite', 1))
                
                try:
                    # Supprimer l'ancien panier et décrémenter le compteur
                    ancien_panier = Panier.objects.get(id=ancien_article_id, commande=commande)
                    ancien_article = ancien_panier.article
                    
                    # Sauvegarder les infos avant suppression
                    ancien_etait_upsell = ancien_article.isUpsell
                    
                    # Supprimer l'ancien panier
                    ancien_panier.delete()
                    
                    # Créer le nouveau panier
                    nouvel_article = Article.objects.get(id=nouvel_article_id)
                    
                    # Recalculer le compteur après remplacement
                    from django.db.models import Sum
                    total_quantite_upsell = commande.paniers.filter(article__isUpsell=True).aggregate(
                        total=Sum('quantite')
                    )['total'] or 0
                    
                    # Ajouter la quantité si le nouvel article est upsell
                    if nouvel_article.isUpsell:
                        total_quantite_upsell += nouvelle_quantite
                    
                    # Appliquer la logique : compteur = max(0, total_quantite_upsell - 1)
                    if total_quantite_upsell >= 2:
                        commande.compteur = total_quantite_upsell - 1
                    else:
                        commande.compteur = 0
                    
                    commande.save()
                    
                    # Recalculer TOUS les articles de la commande avec le nouveau compteur
                    commande.recalculer_totaux_upsell()
                    
                    # Calculer le sous-total selon le compteur de la commande
                    from commande.templatetags.commande_filters import get_prix_upsell_avec_compteur
                    prix_unitaire = get_prix_upsell_avec_compteur(nouvel_article, commande.compteur)
                    sous_total = prix_unitaire * nouvelle_quantite
                    
                    nouveau_panier = Panier.objects.create(
                        commande=commande,
                        article=nouvel_article,
                        quantite=nouvelle_quantite,
                        sous_total=float(sous_total)
                    )
                    
                    # Recalculer le total de la commande
                    total_commande = commande.paniers.aggregate(
                        total=models.Sum('sous_total')
                    )['total'] or 0
                    commande.total_cmd = float(total_commande)
                    commande.save()
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Article remplacé avec succès',
                        'nouvel_article_id': nouveau_panier.id,
                        'total_commande': float(commande.total_cmd),
                        'nb_articles': commande.paniers.count(),
                        'compteur': commande.compteur
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
            
            # ================ TRAITEMENT NORMAL DU FORMULAIRE ================
            
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
            
            # Mise à jour du champ upsell
            is_upsell = request.POST.get('is_upsell', 'false')
            commande.is_upsell = (is_upsell == 'true')
            
            # ================ GESTION DES ARTICLES/PANIERS ================
            
            # 1. Gestion des articles supprimés
            articles_supprimes = request.POST.getlist('deleted_articles[]')
            if articles_supprimes:
                from commande.models import Panier
                for panier_id in articles_supprimes:
                    try:
                        panier = Panier.objects.get(id=panier_id, commande=commande)
                        panier.delete()
                    except Panier.DoesNotExist:
                        pass
            
            # 2. Gestion des articles modifiés
            articles_modifies = request.POST.getlist('modified_articles[]')
            nouvelles_quantites = request.POST.getlist('modified_quantities[]')
            
            if articles_modifies and nouvelles_quantites:
                from commande.models import Panier
                for i, panier_id in enumerate(articles_modifies):
                    if i < len(nouvelles_quantites):
                        try:
                            panier = Panier.objects.get(id=panier_id, commande=commande)
                            nouvelle_quantite = int(nouvelles_quantites[i])
                            if nouvelle_quantite > 0:
                                panier.quantite = nouvelle_quantite
                                # Recalculer le sous-total
                                panier.sous_total = float(panier.article.prix_unitaire * nouvelle_quantite)
                                panier.save()
                        except (Panier.DoesNotExist, ValueError):
                            continue
            
            # 3. Gestion des nouveaux articles
            nouveaux_articles = request.POST.getlist('new_articles[]')
            quantites_nouveaux = request.POST.getlist('new_quantities[]')
            
            if nouveaux_articles and quantites_nouveaux:
                from article.models import Article
                from commande.models import Panier
                
                for i, article_id in enumerate(nouveaux_articles):
                    if i < len(quantites_nouveaux):
                        try:
                            article = Article.objects.get(id=article_id)
                            quantite = int(quantites_nouveaux[i])
                            if quantite > 0:
                                sous_total = float(article.prix_unitaire * quantite)
                                Panier.objects.create(
                                    commande=commande,
                                    article=article,
                                    quantite=quantite,
                                    sous_total=sous_total
                                )
                        except (Article.DoesNotExist, ValueError):
                            continue
            
            # 4. Recalculer le total de la commande
            total_commande = commande.paniers.aggregate(
                total=models.Sum('sous_total')
            )['total'] or 0
            commande.total_cmd = float(total_commande)
            commande.save()
            
            # ================ GESTION DES OPÉRATIONS ================
            
            # Gestion des opérations individuelles avec commentaires spécifiques
            operations_selectionnees = request.POST.getlist('operations[]')
            operations_creees = []
            
            for type_operation in operations_selectionnees:
                if type_operation:  # Vérifier que le type n'est pas vide
                    # Récupérer le commentaire spécifique à cette opération
                    commentaire_specifique = request.POST.get(f'comment_{type_operation}', '').strip()
                    
                    # L'opérateur DOIT saisir un commentaire - pas de commentaire automatique
                    if commentaire_specifique:
                        # Créer l'opération avec le commentaire saisi par l'opérateur
                        operation = Operation.objects.create(
                            type_operation=type_operation,
                            conclusion=commentaire_specifique,
                            commande=commande,
                            operateur=operateur
                        )
                        operations_creees.append(operation)
                    else:
                        # Ignorer l'opération si aucun commentaire n'est fourni
                        messages.warning(request, f"Opération {type_operation} ignorée : aucun commentaire fourni par l'opérateur.")
            
            # Messages de succès
            messages_success = []
            if operations_creees:
                operations_names = [op.get_type_operation_display() for op in operations_creees]
                messages_success.append(f'Opérations ajoutées : {", ".join(operations_names)}')
            
            # Compter les modifications d'articles
            nb_articles_modifies = len(articles_supprimes) + len(articles_modifies) + len(nouveaux_articles)
            if nb_articles_modifies > 0:
                messages_success.append(f'{nb_articles_modifies} modification(s) d\'articles appliquée(s)')
            
            # Vérifier si c'est une requête AJAX pour la sauvegarde automatique
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                # Réponse JSON pour les requêtes AJAX
                response_data = {
                    'success': True,
                    'message': 'Modifications sauvegardées avec succès',
                    'total_commande': float(commande.total_cmd),
                    'nb_articles': commande.paniers.count(),
                }
                
                if operations_creees:
                    operations_names = [op.get_type_operation_display() for op in operations_creees]
                    response_data['operations_ajoutees'] = operations_names
                
                if nb_articles_modifies > 0:
                    response_data['articles_modifies'] = nb_articles_modifies
                
                return JsonResponse(response_data)
            else:
                # Réponse normale avec redirect pour les soumissions manuelles
                if messages_success:
                    messages.success(request, f'Commande modifiée avec succès. {" | ".join(messages_success)}')
                else:
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

@login_required
def api_operations_commande(request, commande_id):
    """API pour récupérer les opérations d'une commande mises à jour"""
    try:
        # Vérifier que l'utilisateur est un opérateur de confirmation
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
        
        # Récupérer la commande
        commande = Commande.objects.get(id=commande_id)
        
        # Récupérer toutes les opérations de cette commande
        operations = commande.operations.all().order_by('date_operation')
        
        operations_data = []
        for operation in operations:
            # Déterminer la classe CSS selon le type d'opération
            if operation.type_operation == "APPEL":
                classe_css = 'bg-blue-100 text-blue-800'
            elif operation.type_operation == "ENVOI_SMS":
                classe_css = 'bg-green-100 text-green-800'
            elif "Whatsapp" in operation.type_operation:
                classe_css = 'bg-emerald-100 text-emerald-800'
            else:
                classe_css = 'bg-gray-100 text-gray-800'
            
            # Déterminer le type principal
            if operation.type_operation == "APPEL":
                type_principal = 'APPEL'
            elif operation.type_operation == "ENVOI_SMS":
                type_principal = 'SMS'
            elif "Whatsapp" in operation.type_operation:
                type_principal = 'WHATSAPP'
            else:
                type_principal = 'OTHER'
            
            operations_data.append({
                'id': operation.id,
                'type_operation': operation.type_operation,
                'nom_display': operation.get_type_operation_display(),
                'classe_css': classe_css,
                'date_operation': operation.date_operation.strftime('%d/%m/%Y %H:%M'),
                'conclusion': operation.conclusion or '',
                'type_principal': type_principal
            })
        
        return JsonResponse({
            'success': True,
            'operations': operations_data,
            'count': len(operations_data)
        })
        
    except Operateur.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Utilisateur non autorisé'
        })
    except Commande.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Commande introuvable'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def api_articles_disponibles(request):
    try:
        # Récupérer tous les articles disponibles
        articles = Article.objects.filter(
            actif=True, 
        ).order_by('nom')
        
        # Préparer les données des articles
        articles_data = []
        for article in articles:
            # Mettre à jour le prix actuel si nécessaire
            if article.prix_actuel is None:
                article.prix_actuel = article.prix_unitaire
                article.save(update_fields=['prix_actuel'])
            
            # S'assurer que qte_disponible est bien un entier
            stock = article.qte_disponible
            if stock is None:
                stock = 0
            
            # Déterminer l'URL de l'image
            image_url = None
            if article.image:
                image_url = article.image.url
            elif article.image_url:
                image_url = article.image_url
            
            articles_data.append({
                'id': article.id,
                'nom': article.nom,
                'reference': article.reference or '',
                'pointure': article.pointure or '',
                'couleur': article.couleur or '',
                'categorie': (str(article.categorie) if article.categorie else ''),
                'prix_unitaire': float(article.prix_unitaire),
                'prix_actuel': float(article.prix_actuel or article.prix_unitaire),
                'prix_upsell_1': float(article.prix_upsell_1) if article.prix_upsell_1 else None,
                'prix_upsell_2': float(article.prix_upsell_2) if article.prix_upsell_2 else None,
                'prix_upsell_3': float(article.prix_upsell_3) if article.prix_upsell_3 else None,
                'prix_upsell_4': float(article.prix_upsell_4) if article.prix_upsell_4 else None,
                'qte_disponible': stock,
                'isUpsell': bool(article.isUpsell),
                'phase': article.phase,
                'has_promo_active': article.has_promo_active,
                'description': article.description or '',
                'image_url': image_url,
            })
        
        return JsonResponse(articles_data, safe=False)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        return JsonResponse({
            'success': False, 
            'error': 'Impossible de charger les articles. Veuillez réessayer.',
            'details': str(e)
        }, status=500)

@login_required
def api_commentaires_disponibles(request):
    """API pour récupérer la liste des commentaires prédéfinis depuis le modèle"""
    try:
        # Vérifier que l'utilisateur est un opérateur de confirmation
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    if request.method == 'GET':
        from commande.models import Operation
        
        # Récupérer les choix de commentaires depuis le modèle
        commentaires_choices = Operation.Type_Commentaire_CHOICES
        
        # Convertir en format utilisable par le frontend
        commentaires_data = {
            'APPEL': [],
            'ENVOI_SMS': [],
            'Appel Whatsapp': [],
            'Message Whatsapp': [],
            'Vocal Whatsapp': []
        }
        
        # Tous les commentaires sont utilisables pour tous les types d'opérations
        for choice_value, choice_label in commentaires_choices:
            commentaire_item = {
                'value': choice_value,
                'label': choice_label
            }
            
            # Ajouter le commentaire à tous les types d'opérations
            for type_operation in commentaires_data.keys():
                commentaires_data[type_operation].append(commentaire_item)
        
        return JsonResponse({
            'success': True,
            'commentaires': commentaires_data
        })
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

@login_required
def creer_commande(request):
    """Créer une nouvelle commande - Interface opérateur de confirmation"""
    try:
        # Récupérer le profil opérateur de l'utilisateur connecté
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        messages.error(request, "Profil d'opérateur de confirmation non trouvé.")
        return redirect('login')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Récupérer les données du formulaire
                type_client = request.POST.get('type_client')
                ville_id = request.POST.get('ville_livraison')
                adresse = request.POST.get('adresse', '').strip()
                is_upsell = request.POST.get('is_upsell') == 'on'
                total_cmd = request.POST.get('total_cmd', 0)

                # Log des données reçues
                logging.info(f"Données de création de commande reçues: type_client={type_client}, ville_id={ville_id}, adresse={adresse}, is_upsell={is_upsell}, total_cmd={total_cmd}")

                # Valider la présence de la ville et de l'adresse
                if not ville_id or not adresse:
                    messages.error(request, "Veuillez sélectionner une ville et fournir une adresse.")
                    return redirect('operatConfirme:creer_commande')

                # Gérer le client selon le type
                if type_client == 'existant':
                    client_id = request.POST.get('client')
                    if not client_id:
                        messages.error(request, "Veuillez sélectionner un client existant.")
                        return redirect('operatConfirme:creer_commande')
                    client = get_object_or_404(Client, pk=client_id)
                else:  # nouveau client
                    # Récupérer les données du nouveau client
                    nouveau_prenom = request.POST.get('nouveau_prenom', '').strip()
                    nouveau_nom = request.POST.get('nouveau_nom', '').strip()
                    nouveau_telephone = request.POST.get('nouveau_telephone', '').strip()
                    nouveau_email = request.POST.get('nouveau_email', '').strip()

                    # Validation des champs obligatoires pour nouveau client
                    if not all([nouveau_prenom, nouveau_nom, nouveau_telephone]):
                        messages.error(request, "Veuillez remplir tous les champs obligatoires du nouveau client (prénom, nom, téléphone).")
                        return redirect('operatConfirme:creer_commande')

                    # Vérifier si le téléphone existe déjà
                    if Client.objects.filter(numero_tel=nouveau_telephone).exists():
                        messages.warning(request, f"Un client avec le numéro {nouveau_telephone} existe déjà. Utilisez 'Client existant' ou modifiez le numéro.")
                        return redirect('operatConfirme:creer_commande')

                    # Créer le nouveau client
                    client = Client.objects.create(
                        prenom=nouveau_prenom,
                        nom=nouveau_nom,
                        numero_tel=nouveau_telephone,
                        email=nouveau_email if nouveau_email else None,
                        is_active=True
                    )

                ville = get_object_or_404(Ville, pk=ville_id)

                # Créer la commande avec le total fourni
                try:
                    commande = Commande.objects.create(
                        client=client,
                        ville=ville,
                        adresse=adresse,
                        total_cmd=float(total_cmd),  # Convertir en float
                        is_upsell=is_upsell,
                        origine='OC'  # Définir l'origine comme Opérateur Confirmation
                    )
                except Exception as e:
                    logging.error(f"Erreur lors de la création de la commande: {str(e)}")
                    messages.error(request, f"Impossible de créer la commande: {str(e)}")
                    return redirect('operatConfirme:creer_commande')

                # Traiter le panier et calculer le total
                article_ids = request.POST.getlist('article_id')
                quantites = request.POST.getlist('quantite')
                
                logging.info(f"Articles dans la commande: {article_ids}, Quantités: {quantites}")
                
                if not article_ids:
                    messages.warning(request, "La commande a été créée mais est vide. Aucun article n'a été ajouté.")
                
                total_calcule = 0
                for i, article_id in enumerate(article_ids):
                    try:
                        quantite = int(quantites[i])
                        if quantite > 0 and article_id:
                            article = get_object_or_404(Article, pk=article_id)
                            # Utiliser prix_actuel si disponible, sinon prix_unitaire
                            prix_a_utiliser = article.prix_actuel if article.prix_actuel is not None else article.prix_unitaire
                            
                            # Log pour comprendre le calcul du prix
                            logging.info(f"Article {article.id}: prix_unitaire={article.prix_unitaire}, prix_actuel={article.prix_actuel}, prix_utilisé={prix_a_utiliser}")
                            
                            sous_total = prix_a_utiliser * quantite
                            total_calcule += float(sous_total)
                            
                            Panier.objects.create(
                                commande=commande,
                                article=article,
                                quantite=quantite,
                                sous_total=float(sous_total)
                            )
                    except (ValueError, IndexError, Article.DoesNotExist) as e:
                        logging.error(f"Erreur lors de l'ajout d'un article: {str(e)}")
                        messages.error(request, f"Erreur lors de l'ajout d'un article : {e}")
                        raise e # Annule la transaction

                # Mettre à jour le total final de la commande avec le montant recalculé
                commande.total_cmd = float(total_calcule)
                commande.save()

                # Créer l'état initial "Affectée" directement à l'opérateur créateur
                try:
                    etat_affectee = EnumEtatCmd.objects.get(libelle='Affectée')
                    EtatCommande.objects.create(
                        commande=commande,
                        enum_etat=etat_affectee,
                        operateur=operateur,
                        commentaire=f"Commande créée et auto-affectée à {operateur.nom_complet}"
                    )
                except EnumEtatCmd.DoesNotExist:
                    try:
                        etat_initial = EnumEtatCmd.objects.get(libelle='Non affectée')
                        EtatCommande.objects.create(
                            commande=commande,
                            enum_etat=etat_initial,
                            commentaire=f"Commande créée par {operateur.nom_complet}"
                        )
                    except EnumEtatCmd.DoesNotExist:
                        pass # Si aucun état n'existe, créer sans état initial
                
                # Composer le message de succès final
                message_final = f"Commande YZ-{commande.id_yz} créée avec succès."
                if type_client != 'existant':
                    message_final = f"Nouveau client '{client.get_full_name}' créé. " + message_final

                messages.success(request, message_final)
                return redirect('operatConfirme:liste_commandes')

        except Exception as e:
            logging.error(f"Erreur critique lors de la création de la commande: {str(e)}")
            messages.error(request, f"Erreur critique lors de la création de la commande: {str(e)}")
            # Rediriger vers le formulaire pour correction
            return redirect('operatConfirme:creer_commande')

    # GET request - afficher le formulaire
    clients = Client.objects.all().order_by('prenom', 'nom')
    articles = Article.objects.all().order_by('nom')
    villes = Ville.objects.select_related('region').order_by('region__nom_region', 'nom')

    context = {
        'operateur': operateur,
        'clients': clients,
        'articles': articles,
        'villes': villes,
    }

    return render(request, 'operatConfirme/creer_commande.html', context)

@login_required
def api_panier_commande(request, commande_id):
    """API pour récupérer le contenu du panier d'une commande"""
    try:
        # Vérifier que l'utilisateur est un opérateur de confirmation
        operateur = Operateur.objects.get(user=request.user, type_operateur='CONFIRMATION')
    except Operateur.DoesNotExist:
        return JsonResponse({'error': 'Accès non autorisé'}, status=403)
    
    if request.method == 'GET':
        try:
            # Récupérer la commande avec ses paniers
            commande = get_object_or_404(
                Commande.objects.select_related('client', 'ville').prefetch_related(
                    'paniers__article'
                ),
                pk=commande_id
            )
            
            # Vérifier que l'opérateur peut voir cette commande
            # Soit elle lui est actuellement affectée (date_fin=null)
            # Soit il l'a déjà traitée (peu importe date_fin)
            etat_operateur = commande.etats.filter(
                operateur=operateur
            ).first()
            
            if not etat_operateur:
                return JsonResponse({'error': 'Cette commande ne vous est pas affectée'}, status=403)
            
            # Préparer les données pour le template
            paniers = commande.paniers.all()
            total_articles = sum(panier.quantite for panier in paniers)
            total_montant = sum(panier.sous_total for panier in paniers)
            frais_livraison = commande.ville.frais_livraison if commande.ville else 0
            # Convertir explicitement en float pour éviter l'erreur Decimal + float
            total_final = float(total_montant) + float(frais_livraison)
            
            # Construire la liste des articles pour le JSON
            articles_data = []
            for panier in paniers:
                articles_data.append({
                    'nom': str(panier.article.nom),
                    'reference': str(panier.article.reference) if panier.article.reference else 'N/A',
                    'description': str(panier.article.description) if panier.article.description else '',
                    'prix_unitaire': float(panier.article.prix_unitaire),
                    'quantite': panier.quantite,
                    'sous_total': float(panier.sous_total)
                })
            
            return JsonResponse({
                'success': True,
                'commande': {
                    'id_yz': commande.id_yz,
                    'client_nom': str(commande.client.get_full_name),
                    'total_articles': total_articles,
                    'total_montant': float(total_montant),
                    'frais_livraison': float(frais_livraison),
                    'total_final': float(total_final)
                },
                'articles': articles_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Erreur lors de la récupération du panier: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

def reinitialiser_compteur_commande(request, commande_id):
    """
    Fonction pour réinitialiser le compteur d'une commande si nécessaire
    """
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Vérifier et compter les articles upsell dans la commande
        articles_upsell = commande.paniers.filter(article__isUpsell=True)
        
        # Calculer la quantité totale d'articles upsell
        from django.db.models import Sum
        total_quantite_upsell = articles_upsell.aggregate(
            total=Sum('quantite')
        )['total'] or 0
        
        # Déterminer le compteur correct selon la nouvelle logique :
        # 0-1 unités upsell → compteur = 0
        # 2+ unités upsell → compteur = total_quantite_upsell - 1
        if total_quantite_upsell >= 2:
            compteur_correct = total_quantite_upsell - 1
        else:
            compteur_correct = 0
        
        if commande.compteur != compteur_correct:
            print(f"🔧 Correction du compteur: {commande.compteur} -> {compteur_correct}")
            commande.compteur = compteur_correct
            commande.save()
            
            # Recalculer les totaux
            commande.recalculer_totaux_upsell()
            
            messages.success(request, f"Compteur corrigé: {compteur_correct}")
        else:
            messages.info(request, "Compteur déjà correct")
            
        return redirect('operatConfirme:modifier_commande', commande_id=commande.id)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la correction: {str(e)}")
        return redirect('operatConfirme:confirmation')

def diagnostiquer_compteur_commande(request, commande_id):
    """
    Fonction pour diagnostiquer et corriger le compteur d'une commande
    """
    try:
        commande = get_object_or_404(Commande, id=commande_id)
        
        # Diagnostiquer la situation actuelle
        articles_upsell = commande.paniers.filter(article__isUpsell=True)
        compteur_actuel = commande.compteur
        
        # Calculer la quantité totale d'articles upsell
        from django.db.models import Sum
        total_quantite_upsell = articles_upsell.aggregate(
            total=Sum('quantite')
        )['total'] or 0
        
        print(f"🔍 DIAGNOSTIC Commande {commande.id_yz}:")
        print(f"📊 Compteur actuel: {compteur_actuel}")
        print(f"📦 Articles upsell trouvés: {articles_upsell.count()}")
        print(f"🔢 Quantité totale d'articles upsell: {total_quantite_upsell}")
        
        if articles_upsell.exists():
            print("📋 Articles upsell dans la commande:")
            for panier in articles_upsell:
                print(f"  - {panier.article.nom} (Qté: {panier.quantite}, ID: {panier.article.id}, isUpsell: {panier.article.isUpsell})")
        
        # Déterminer le compteur correct selon la nouvelle logique :
        # 0-1 unités upsell → compteur = 0
        # 2+ unités upsell → compteur = total_quantite_upsell - 1
        if total_quantite_upsell >= 2:
            compteur_correct = total_quantite_upsell - 1
        else:
            compteur_correct = 0
        
        print(f"✅ Compteur correct: {compteur_correct}")
        print("📖 Logique: 0-1 unités upsell → compteur=0 | 2+ unités upsell → compteur=total_quantité-1")
        
        # Corriger si nécessaire
        if compteur_actuel != compteur_correct:
            print(f"🔧 CORRECTION: {compteur_actuel} -> {compteur_correct}")
            commande.compteur = compteur_correct
            commande.save()
            
            # Recalculer tous les totaux
            commande.recalculer_totaux_upsell()
            
            messages.success(request, f"Compteur corrigé: {compteur_actuel} -> {compteur_correct}")
            
            # Retourner les nouvelles données
            return JsonResponse({
                'success': True,
                'message': f'Compteur corrigé de {compteur_actuel} vers {compteur_correct}',
                'ancien_compteur': compteur_actuel,
                'nouveau_compteur': compteur_correct,
                'total_commande': float(commande.total_cmd),
                'articles_upsell': articles_upsell.count(),
                'quantite_totale_upsell': total_quantite_upsell
            })
        else:
            return JsonResponse({
                'success': True,
                'message': 'Compteur déjà correct',
                'compteur': compteur_actuel,
                'articles_upsell': articles_upsell.count(),
                'quantite_totale_upsell': total_quantite_upsell
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def rafraichir_articles_section(request, commande_id):
    """
    Vue pour rafraîchir la section des articles d'une commande et renvoyer le HTML.
    """
    try:
        commande = get_object_or_404(Commande.objects.prefetch_related('paniers__article'), id=commande_id)
        
        # S'assurer que les totaux et le compteur sont à jour
        commande.recalculer_totaux_upsell()

        context = {
            'commande': commande,
            'villes': Ville.objects.select_related('region').order_by('region__nom_region', 'nom')
        }
        
        # Rendre le template partiel avec la liste des articles
        html = render_to_string('operatConfirme/partials/_articles_section.html', context, request=request)
        
        # Renvoyer le HTML et les totaux mis à jour
        return JsonResponse({
            'success': True,
            'html': html,
            'total_commande': float(commande.total_cmd),
            'articles_count': commande.paniers.count(),
            'compteur': commande.compteur,
        })
        
    except Commande.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Commande non trouvée'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def api_recherche_client_tel(request):
    """API pour rechercher un client par numéro de téléphone (recherche partielle)"""
    if request.method == 'GET':
        query = request.GET.get('q', '').strip()
        results = []
        if query and len(query) >= 3:
            from client.models import Client
            clients = Client.objects.filter(numero_tel__icontains=query).order_by('prenom', 'nom')[:10]
            for c in clients:
                results.append({
                    'id': c.pk,
                    'nom': c.nom,
                    'prenom': c.prenom,
                    'numero_tel': c.numero_tel,
                    'full_name': f"{c.prenom} {c.nom}",
                })
        return JsonResponse({'results': results})
    return JsonResponse({'results': []}, status=405)

@login_required
def api_recherche_article_ref(request):
    """API pour rechercher des articles par référence ou nom"""
    try:
        # Récupérer les paramètres de recherche
        query = request.GET.get('q', '').strip()
        article_id = request.GET.get('id', '').strip()
        reference = request.GET.get('reference', '').strip()
        
        # Cas 1: Recherche par ID (pour modifier_commande.html)
        if article_id:
            try:
                article = Article.objects.get(id=article_id, actif=True)
                # Mettre à jour le prix actuel si nécessaire
                if article.prix_actuel is None:
                    article.prix_actuel = article.prix_unitaire
                    article.save(update_fields=['prix_actuel'])
                
                article_data = {
                    'id': article.id,
                    'nom': article.nom,
                    'reference': article.reference or '',
                    'prix_unitaire': float(article.prix_unitaire),
                    'prix_actuel': float(article.prix_actuel or article.prix_unitaire),
                    'qte_disponible': article.qte_disponible or 0,
                }
                
                return JsonResponse({
                    'success': True,
                    'article': article_data
                })
            except Article.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'Article avec l\'ID {article_id} non trouvé ou désactivé'
                })
        
        # Cas 2: Recherche par référence exacte
        elif reference:
            article = Article.objects.filter(reference=reference, actif=True).first()
            if article:
                # Mettre à jour le prix actuel si nécessaire
                if article.prix_actuel is None:
                    article.prix_actuel = article.prix_unitaire
                    article.save(update_fields=['prix_actuel'])
                
                article_data = {
                    'id': article.id,
                    'nom': article.nom,
                    'reference': article.reference or '',
                    'prix_unitaire': float(article.prix_unitaire),
                    'prix_actuel': float(article.prix_actuel or article.prix_unitaire),
                    'qte_disponible': article.qte_disponible or 0,
                }
                
                return JsonResponse({
                    'success': True,
                    'article': article_data
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': f'Article avec la référence "{reference}" non trouvé ou désactivé'
                })
        
        # Cas 3: Recherche par texte (pour creer_commande.html)
        elif query and len(query) >= 2:
            # Rechercher les articles par référence ou nom
            articles = Article.objects.filter(
                Q(reference__icontains=query) | 
                Q(nom__icontains=query),
                actif=True
            ).order_by('nom')[:10]  # Limiter à 10 résultats
            
            results = []
            for article in articles:
                # Mettre à jour le prix actuel si nécessaire
                if article.prix_actuel is None:
                    article.prix_actuel = article.prix_unitaire
                    article.save(update_fields=['prix_actuel'])
                
                results.append({
                    'id': article.id,
                    'nom': article.nom,
                    'reference': article.reference or '',
                    'prix_unitaire': float(article.prix_unitaire),
                    'prix_actuel': float(article.prix_actuel or article.prix_unitaire),
                    'qte_disponible': article.qte_disponible or 0,
                })
            
            return JsonResponse({
                'results': results
            })
        
        # Cas par défaut: aucun paramètre valide
        else:
            return JsonResponse({
                'results': []
            })
        
    except Exception as e:
        import traceback
        print(f"Erreur dans api_recherche_article_ref: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'results': [],
            'error': str(e)
        })

# Vues liées aux notifications supprimées (test_modal, centre_notifications)

@login_required
def get_article_variants(request, article_id):
    """
    Récupère toutes les variantes disponibles d'un article donné
    """
    try:
        from article.models import Article, VarianteArticle
        
        print(f"🔍 Recherche des variantes pour l'article ID: {article_id} (type: {type(article_id)})")
        
        # Vérifier si l'article existe et s'il est actif
        try:
            article = Article.objects.get(id=article_id)
            print(f"📋 Article trouvé: {article.nom} (actif: {article.actif})")
            
            if not article.actif:
                print(f"⚠️ Article {article_id} existe mais est inactif")
                return JsonResponse({
                    'success': False,
                    'error': f'L\'article "{article.nom}" (ID: {article_id}) est désactivé'
                }, status=404)
                
        except Article.DoesNotExist:
            print(f"❌ Aucun article trouvé avec l'ID {article_id}")
            return JsonResponse({
                'success': False,
                'error': f'Aucun article trouvé avec l\'ID {article_id}'
            }, status=404)
            
        print(f"✅ Article actif trouvé: {article.nom}")
        
        # Récupérer toutes les variantes actives de cet article
        variantes = VarianteArticle.objects.filter(
            article=article,
            actif=True
        ).select_related('couleur', 'pointure').order_by('couleur__nom', 'pointure__ordre')
        
        print(f"📊 Nombre de variantes trouvées: {variantes.count()}")
        
        # Construire la liste des variantes avec leurs informations
        variants_data = []
        for variante in variantes:
            print(f"🔸 Variante: {variante.id} - Couleur: {variante.couleur} - Pointure: {variante.pointure} - Stock: {variante.qte_disponible}")
            
            variant_info = {
                'id': variante.id,
                'couleur': variante.couleur.nom if variante.couleur else None,
                'pointure': variante.pointure.pointure if variante.pointure else None,
                'taille': None,  # À adapter selon votre modèle si vous avez des tailles
                'stock': variante.qte_disponible,
                'prix_unitaire': float(variante.prix_unitaire),
                'prix_actuel': float(variante.prix_actuel),
                'reference_variante': variante.reference_variante,
                'est_disponible': variante.est_disponible
            }
            variants_data.append(variant_info)
        
        response_data = {
            'success': True,
            'variants': variants_data,
            'article': {
                'id': article.id,
                'nom': article.nom,
                'reference': article.reference
            }
        }
        
        print(f"📤 Réponse envoyée: {len(variants_data)} variantes")
        return JsonResponse(response_data)
        
    except Exception as e:
        import traceback
        print(f"❌ Erreur dans get_article_variants: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': 'Erreur lors de la récupération des variantes'
        }, status=500)


