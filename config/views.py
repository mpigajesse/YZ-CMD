from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse, NoReverseMatch
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from parametre.models import Operateur
import json
import subprocess
import os
from django.contrib.auth import logout
from django.contrib import messages
from django.middleware.csrf import get_token

@login_required
def home_redirect(request):
    """
    Redirige l'utilisateur vers sa page home spécifique selon son type
    """
    user = request.user
    
    # Vérifier si l'utilisateur a un profil opérateur
    try:
        operateur = Operateur.objects.get(user=user, actif=True)
        
        # Redirection selon le type d'opérateur
        if operateur.type_operateur == 'PREPARATION':
            return redirect(reverse('Prepacommande:home'))
        elif operateur.type_operateur == 'CONFIRMATION':
            return redirect(reverse('operatConfirme:home'))
        elif operateur.type_operateur == 'LOGISTIQUE':
            return redirect(reverse('operatLogistic:home'))
        elif operateur.type_operateur == 'SUPERVISEUR_PREPARATION':
            return redirect(reverse('Superpreparation:home'))
        elif operateur.type_operateur == 'ADMIN':
            return redirect(reverse('app_admin:home'))
        else:
            # Type d'opérateur non reconnu
            return redirect(reverse('app_admin:home'))
    
    except Operateur.DoesNotExist:
        # Si pas de profil opérateur, vérifier les groupes Django (ancien système)
        if user.groups.filter(name='operateur_confirme').exists():
            return redirect(reverse('operatConfirme:home'))
        elif user.groups.filter(name='operateur_logistique').exists():
            return redirect(reverse('operatLogistic:home'))
        elif user.groups.filter(name='operateur_preparation').exists():
            return redirect(reverse('Prepacommande:home'))
        elif user.groups.filter(name='superviseur').exists():
            return redirect(reverse('Superpreparation:home'))
        else:
            # Par défaut, rediriger vers l'interface admin
            return redirect(reverse('app_admin:home'))

@login_required
def test_admin_url(request):
    try:
        url = reverse('admin:liste_operateurs')
        message = f"URL for admin:liste_operateurs resolved successfully: {url}"
    except NoReverseMatch as e:
        message = f"Failed to resolve admin:liste_operateurs: {e}"
    return render(request, 'test_url.html', {'message': message}) 

@login_required 
def clear_middleware_messages(request):
    """Vue utilitaire pour forcer le nettoyage des messages MWI-001"""
    from django.contrib import messages
    
    # Nettoyer les flags de session
    keys_to_remove = [key for key in request.session.keys() if key.startswith('middleware_redirect')]
    for key in keys_to_remove:
        del request.session[key]
    
    # Nettoyer les messages MWI-001
    storage = messages.get_messages(request)
    messages_to_keep = []
    messages_cleaned = 0
    
    for message in storage:
        if not ("MWI-001" in str(message) and "Accès non autorisé" in str(message)):
            messages_to_keep.append(message)
        else:
            messages_cleaned += 1
    
    # Remettre seulement les messages à garder
    storage.used = True
    for message in messages_to_keep:
        messages.add_message(request, message.level, message.message, message.tags)
    
    messages.success(request, f"✅ Nettoyage terminé. {messages_cleaned} message(s) MWI-001 supprimé(s).")
    
    # Rediriger vers la page d'accueil appropriée selon le type d'utilisateur
    return home_redirect(request)

def is_admin(user):
    """Vérifie si l'utilisateur est un administrateur"""
    return user.is_authenticated and user.is_staff

@require_POST
@user_passes_test(is_admin)
def diagnostic_clients_ajax(request):
    """Exécute le diagnostic des clients via AJAX"""
    try:
        # Importer les modèles nécessaires
        from client.models import Client
        from commande.models import Commande
        from synchronisation.models import SyncLog
        from django.db.models import Count, Q
        
        # Statistiques de base
        total_clients = Client.objects.count()
        clients_avec_commandes = Client.objects.filter(commandes__isnull=False).distinct().count()
        clients_sans_commandes = total_clients - clients_avec_commandes
        
        # Doublons
        doublons_tel = Client.objects.values('numero_tel').annotate(
            count=Count('id')
        ).filter(count__gt=1).count()
        
        doublons_nom = Client.objects.values('nom', 'prenom').annotate(
            count=Count('id')
        ).filter(count__gt=1).count()
        
        # Clients sans téléphone
        clients_sans_tel = Client.objects.filter(
            Q(numero_tel__isnull=True) | Q(numero_tel__exact='')
        ).count()
        
        # Clients sans nom
        clients_sans_nom = Client.objects.filter(
            Q(nom__isnull=True) | Q(nom__exact='') | 
            Q(prenom__isnull=True) | Q(prenom__exact='')
        ).count()
        
        # Générer des recommandations
        recommendations = []
        if doublons_tel > 0:
            recommendations.append(f"Fusionner {doublons_tel} groupes de clients avec des numéros identiques")
        if clients_sans_tel > 0:
            recommendations.append(f"Compléter les numéros de téléphone pour {clients_sans_tel} clients")
        if clients_sans_commandes > total_clients * 0.8:
            recommendations.append("Vérifier la synchronisation - trop de clients sans commandes")
        
        return JsonResponse({
            'success': True,
            'total_clients': total_clients,
            'doublons_tel': doublons_tel,
            'doublons_nom': doublons_nom,
            'clients_avec_commandes': clients_avec_commandes,
            'clients_sans_commandes': clients_sans_commandes,
            'clients_sans_tel': clients_sans_tel,
            'clients_sans_nom': clients_sans_nom,
            'recommendations': ' | '.join(recommendations) if recommendations else None,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@require_POST
@user_passes_test(is_admin)
def corriger_clients_ajax(request):
    """Corrige automatiquement les doublons de clients via AJAX"""
    try:
        from client.models import Client
        from django.db.models import Count
        from django.db import transaction
        
        # Trouver les numéros de téléphone en double
        doublons_tel = Client.objects.values('numero_tel').annotate(
            count=Count('id')
        ).filter(count__gt=1).order_by('-count')
        
        clients_fusionnes = 0
        
        for doublon in doublons_tel:
            numero_tel = doublon['numero_tel']
            clients_dupliques = Client.objects.filter(numero_tel=numero_tel).order_by('date_creation')
            
            if clients_dupliques.count() > 1:
                with transaction.atomic():
                    # Garder le premier client (le plus ancien)
                    client_principal = clients_dupliques.first()
                    clients_a_fusionner = clients_dupliques.exclude(id=client_principal.id)
                    
                    # Transférer toutes les commandes vers le client principal
                    for client_dup in clients_a_fusionner:
                        # Transférer les commandes
                        client_dup.commandes.update(client=client_principal)
                        
                        # Mettre à jour les informations du client principal si nécessaire
                        if not client_principal.email and client_dup.email:
                            client_principal.email = client_dup.email
                        if not client_principal.adresse and client_dup.adresse:
                            client_principal.adresse = client_dup.adresse
                        if not client_principal.nom and client_dup.nom:
                            client_principal.nom = client_dup.nom
                        if not client_principal.prenom and client_dup.prenom:
                            client_principal.prenom = client_dup.prenom
                        
                        # Supprimer le client en double
                        client_dup.delete()
                        clients_fusionnes += 1
                    
                    # Sauvegarder les modifications du client principal
                    client_principal.save()
        
        return JsonResponse({
            'success': True,
            'clients_fusionnes': clients_fusionnes,
            'message': f'{clients_fusionnes} clients ont été fusionnés avec succès.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }) 

def custom_logout(request):
    # Utiliser la déconnexion standard de Django qui gère le CSRF correctement
    logout(request)
    messages.info(request, "Vous avez été déconnecté avec succès.")
    return redirect('login')

@ensure_csrf_cookie
def get_csrf_token_view(request):
    """Vue pour obtenir un token CSRF frais"""
    token = get_token(request)
    return JsonResponse({'csrfToken': token})

@csrf_exempt
def check_csrf_status(request):
    """Vue pour vérifier l'état du CSRF"""
    csrf_cookie = request.COOKIES.get('yz_csrf_token', None)
    session_csrf = request.session.get('_csrftoken', None)
    
    return JsonResponse({
        'csrf_cookie_exists': csrf_cookie is not None,
        'csrf_cookie_name': 'yz_csrf_token',
        'session_csrf_exists': session_csrf is not None,
        'cookies': list(request.COOKIES.keys()),
    }) 