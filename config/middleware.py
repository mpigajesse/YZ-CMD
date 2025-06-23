from django.conf import settings
from django.contrib.auth import logout
from django.utils.timezone import now
from django.shortcuts import redirect
from django.contrib import messages
import datetime
from django.urls import reverse
from parametre.models import Operateur # Import d'Operateur pour Operateur.DoesNotExist

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
        )
        self.universal_allowed_exact_paths = (
            # Ajoutez ici des chemins exacts si nécessaire, par exemple une page d'accueil publique
        )

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Les super-utilisateurs ont un accès complet à toutes les interfaces personnalisées
        if request.user.is_superuser:
            return self.get_response(request)

        # Autoriser l'accès aux fichiers statiques/médias et aux pages d'authentification/déconnexion pour tous
        if any(request.path.startswith(prefix) for prefix in self.universal_allowed_paths_startswith) or \
           request.path in self.universal_allowed_exact_paths:
            return self.get_response(request)

        # Exclure explicitement le site d'administration Django de ce middleware pour les non-superusers
        # (il est géré par Django admin lui-même)
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        try:
            profil = request.user.profil_operateur
            user_type = profil.type_operateur
            
            expected_prefix = self.allowed_prefixes.get(user_type)
            
            if expected_prefix:
                # Si le chemin actuel ne commence PAS par le préfixe attendu pour ce type d'opérateur,
                # rediriger vers la page d'accueil spécifique à son rôle.
                if not request.path.startswith(expected_prefix):
                    # Éviter les messages répétés en utilisant la session
                    session_key = f'middleware_redirect_{user_type}'
                    if not request.session.get(session_key, False):
                        messages.error(request, f"Accès non autorisé. Redirection vers votre interface {user_type.capitalize()}. (Code: MWI-001)")
                        request.session[session_key] = True
                    
                    if user_type == 'CONFIRMATION':
                        return redirect(reverse('operatConfirme:home'))
                    elif user_type == 'LOGISTIQUE':
                        return redirect(reverse('operatLogistic:home'))
                    elif user_type == 'PREPARATION':
                        return redirect(reverse('Prepacommande:home'))
                    elif user_type == 'ADMIN':
                        return redirect(reverse('app_admin:home'))
                    else:
                        # Cas inattendu: type d'opérateur connu mais pas de redirection définie
                        messages.error(request, "Type d'opérateur non géré pour la redirection. (Code: MWI-002)")
                        logout(request)
                        return redirect(settings.LOGIN_URL)
                else:
                    # Si l'accès est autorisé, nettoyer le flag de redirection
                    session_key = f'middleware_redirect_{user_type}'
                    if session_key in request.session:
                        del request.session[session_key]
            else:
                # Si le type d'opérateur n'est pas mappé dans allowed_prefixes, ou profil_operateur.type_operateur est None/vide
                messages.error(request, "Votre type d'opérateur n'est pas correctement configuré. Veuillez contacter l'administrateur. (Code: MWI-003)")
                logout(request)
                return redirect(settings.LOGIN_URL)

        except Operateur.DoesNotExist:
            # Si l'utilisateur authentifié n'est pas un super-utilisateur et n'a PAS de profil Operateur
            messages.error(request, "Votre compte n'est pas associé à un profil opérateur valide. Veuillez contacter l'administrateur. (Code: MWI-004)")
            logout(request)
            return redirect(settings.LOGIN_URL)
        except Exception as e:
            # Gérer toute autre erreur inattendue lors de l'accès au profil
            print(f"[UserTypeValidationMiddleware Error]: {e}") # Pour le débogage en développement
            messages.error(request, "Une erreur inattendue s'est produite lors de la validation de votre profil. Veuillez vous reconnecter. (Code: MWI-005)")
            logout(request)
            return redirect(settings.LOGIN_URL)

        response = self.get_response(request)
        return response 