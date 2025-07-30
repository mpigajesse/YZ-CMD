from django.conf import settings
from django.contrib.auth import logout
from django.utils.timezone import now
from django.shortcuts import redirect
from django.contrib import messages
import datetime
from django.urls import reverse
from parametre.models import Operateur # Import d'Operateur pour Operateur.DoesNotExist
import logging

logger = logging.getLogger(__name__)

class CSRFDebugMiddleware:
    """Middleware pour déboguer les problèmes CSRF"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Déboguer les problèmes CSRF uniquement en mode DEBUG
        if settings.DEBUG and request.method == 'POST':
            csrf_cookie = request.COOKIES.get('yz_csrf_token', None)
            csrf_token = request.META.get('HTTP_X_CSRFTOKEN', None)
            csrf_post = request.POST.get('csrfmiddlewaretoken', None)
            
            logger.info(f"[CSRF Debug] URL: {request.path}")
            logger.info(f"[CSRF Debug] Cookie: {csrf_cookie}")
            logger.info(f"[CSRF Debug] Header: {csrf_token}")
            logger.info(f"[CSRF Debug] POST: {csrf_post}")
            logger.info(f"[CSRF Debug] Cookies: {list(request.COOKIES.keys())}")
            
            # Vérifier si le token CSRF est présent dans le formulaire
            if request.path == '/login/' and request.method == 'POST' and not csrf_post:
                logger.warning("[CSRF Debug] Formulaire de connexion sans token CSRF")
                # Ajouter un message pour informer l'utilisateur
                messages.warning(request, "Problème de sécurité CSRF détecté. Veuillez rafraîchir la page et réessayer.")
        
        response = self.get_response(request)
        return response

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Vérifier la dernière activité de l'utilisateur
            last_activity = request.session.get('last_activity')
            
            if last_activity:
                last_activity = datetime.datetime.fromisoformat(last_activity)
                time_elapsed = (now() - last_activity).total_seconds()
                
                if time_elapsed > settings.SESSION_IDLE_TIMEOUT:
                    logout(request)
                    messages.warning(request, "Votre session a expiré en raison d'une longue période d'inactivité. Veuillez vous reconnecter.")
                    return redirect(settings.LOGIN_URL)
            
            # Mettre à jour le timestamp de dernière activité
            request.session['last_activity'] = now().isoformat()

        return self.get_response(request)

class UserTypeValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed_prefixes = {
            'CONFIRMATION': '/operateur-confirme/',
            'LOGISTIQUE': '/operateur-logistique/',
            'PREPARATION': '/operateur-preparation/',
            'ADMIN': '/parametre/', # Pour les opérateurs de type ADMIN qui ne sont pas forcément superusers
        }
        self.universal_allowed_paths_startswith = (
            settings.STATIC_URL,
            settings.MEDIA_URL,
            '/login/',
            '/logout/',
            '/password_reset/', # Si vous avez des URLs de réinitialisation de mot de passe
            '/__reload__/', # Pour le middleware de rechargement automatique en développement
            '/api/csrf/', # Pour les routes CSRF
        )
        self.universal_allowed_exact_paths = (
            # Ajoutez ici des chemins exacts si nécessaire, par exemple une page d'accueil publique
        )

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        if request.user.is_superuser:
            return self.get_response(request)

        if any(request.path.startswith(prefix) for prefix in self.universal_allowed_paths_startswith) or \
           request.path in self.universal_allowed_exact_paths:
            return self.get_response(request)

        if request.path.startswith('/admin/'):
            return self.get_response(request)

        try:
            profil = request.user.profil_operateur
            if not profil.actif:
                messages.error(request, "Votre compte opérateur est désactivé. Veuillez contacter l'administrateur. (Code: MWI-007)")
                logout(request)
                return redirect(settings.LOGIN_URL)
            
            user_type = profil.type_operateur
            expected_prefix = self.allowed_prefixes.get(user_type)
            
            # --- Correction : autoriser les URLs avec ou sans slash final ---
            if expected_prefix and expected_prefix.endswith('/'):
                expected_prefix_alt = expected_prefix.rstrip('/')
            else:
                expected_prefix_alt = expected_prefix + '/'

            # Si le chemin actuel ne commence PAS par le préfixe attendu (avec ou sans slash), rediriger
            if expected_prefix and not (request.path.startswith(expected_prefix) or request.path.startswith(expected_prefix_alt)):
                # Nettoyage des messages d'erreur persistants
                storage = messages.get_messages(request)
                messages_to_keep = []
                for message in storage:
                    if not ("MWI-001" in str(message) and "Accès non autorisé" in str(message)):
                        messages_to_keep.append(message)
                storage.used = True
                for message in messages_to_keep:
                    messages.add_message(request, message.level, message.message, message.tags)

                # Redirection automatique vers la bonne URL d'accueil
                    if user_type == 'CONFIRMATION':
                        return redirect(reverse('operatConfirme:home'))
                    elif user_type == 'LOGISTIQUE':
                        return redirect(reverse('operatLogistic:home'))
                    elif user_type == 'PREPARATION':
                        return redirect(reverse('Prepacommande:home'))
                    elif user_type == 'ADMIN':
                        return redirect(reverse('app_admin:home'))
                    else:
                        messages.error(request, "Type d'opérateur non géré pour la redirection. (Code: MWI-002)")
                        logout(request)
                        return redirect(settings.LOGIN_URL)
                else:
                # Nettoyage des flags de redirection et messages d'erreur MWI-001
                    session_key = f'middleware_redirect_{user_type}'
                    redirect_count_key = f'middleware_redirect_count_{user_type}'
                if session_key in request.session:
                    del request.session[session_key]
                if redirect_count_key in request.session:
                    del request.session[redirect_count_key]
                # Nettoyage des messages d'erreur MWI-001
                    storage = messages.get_messages(request)
                    messages_to_keep = []
                    for message in storage:
                        if not ("MWI-001" in str(message) and "Accès non autorisé" in str(message)):
                            messages_to_keep.append(message)
                storage.used = True
                for message in messages_to_keep:
                        messages.add_message(request, message.level, message.message, message.tags)

        except Operateur.DoesNotExist:
            messages.error(request, "Votre compte n'est pas associé à un profil opérateur valide. Veuillez contacter l'administrateur. (Code: MWI-004)")
            logout(request)
            return redirect(settings.LOGIN_URL)
        except Exception as e:
            print(f"[UserTypeValidationMiddleware Error]: {e}")
            messages.error(request, "Une erreur inattendue s'est produite lors de la validation de votre profil. Veuillez vous reconnecter. (Code: MWI-005)")
            logout(request)
            return redirect(settings.LOGIN_URL)

        response = self.get_response(request)
        return response 