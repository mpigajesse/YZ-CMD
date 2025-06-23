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
            
            # Vérifier que l'opérateur est actif
            if not profil.actif:
                messages.error(request, "Votre compte opérateur est désactivé. Veuillez contacter l'administrateur. (Code: MWI-007)")
                logout(request)
                return redirect(settings.LOGIN_URL)
            
            user_type = profil.type_operateur
            expected_prefix = self.allowed_prefixes.get(user_type)
            
            # Debug: ajouter un print temporaire pour voir ce qui se passe
            if settings.DEBUG:
                print(f"[DEBUG] User: {request.user.username}, Type: {user_type}, Path: {request.path}, Expected: {expected_prefix}")
                if not request.path.startswith(expected_prefix):
                    print(f"[DEBUG] ❌ REDIRECTION DECLENCHEE: {request.path} ne commence pas par {expected_prefix}")
                else:
                    print(f"[DEBUG] ✅ ACCES AUTORISE: {request.path} commence par {expected_prefix}")
            
            if expected_prefix:
                # Si le chemin actuel ne commence PAS par le préfixe attendu pour ce type d'opérateur,
                # rediriger vers la page d'accueil spécifique à son rôle.
                if not request.path.startswith(expected_prefix):
                    # Debug supplémentaire pour comprendre le problème
                    if settings.DEBUG:
                        print(f"[DEBUG] DETAILS REDIRECTION:")
                        print(f"  - request.path = '{request.path}'")
                        print(f"  - expected_prefix = '{expected_prefix}'")
                        print(f"  - startswith result = {request.path.startswith(expected_prefix)}")
                        print(f"  - len(request.path) = {len(request.path)}")
                        print(f"  - len(expected_prefix) = {len(expected_prefix)}")
                        print(f"  - request.path chars = {[c for c in request.path]}")
                        print(f"  - expected_prefix chars = {[c for c in expected_prefix]}")
                    
                    # Éviter les boucles de redirection en vérifiant si nous sommes déjà en train de rediriger
                    session_key = f'middleware_redirect_{user_type}'
                    redirect_count_key = f'middleware_redirect_count_{user_type}'
                    
                    # Compter les tentatives de redirection pour éviter les boucles infinies
                    redirect_count = request.session.get(redirect_count_key, 0)
                    if redirect_count >= 3:
                        # Trop de redirections, nettoyer la session et déconnecter
                        messages.error(request, "Erreur de redirection multiple détectée. Veuillez vous reconnecter. (Code: MWI-006)")
                        for key in list(request.session.keys()):
                            if key.startswith('middleware_redirect'):
                                del request.session[key]
                        logout(request)
                        return redirect(settings.LOGIN_URL)
                    
                    # NE PAS afficher le message si l'utilisateur est déjà en cours de redirection vers la bonne interface
                    # (éviter les messages répétés lors des requêtes AJAX ou recharges)
                    redirect_count = request.session.get(redirect_count_key, 0)
                    if redirect_count <= 1 and not request.session.get(session_key, False):
                        messages.error(request, f"Accès non autorisé. Redirection vers votre interface {user_type.capitalize()}. (Code: MWI-001)")
                        request.session[session_key] = True
                    
                    request.session[redirect_count_key] = redirect_count + 1
                    
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
                    # Si l'accès est autorisé, nettoyer immédiatement les flags de redirection pour ce type d'utilisateur
                    session_key = f'middleware_redirect_{user_type}'
                    redirect_count_key = f'middleware_redirect_count_{user_type}'
                    
                    # Nettoyage forcé des messages d'erreur MWI-001 persistants
                    storage = messages.get_messages(request)
                    messages_to_keep = []
                    messages_cleaned = 0
                    
                    for message in storage:
                        if not ("MWI-001" in str(message) and "Accès non autorisé" in str(message)):
                            messages_to_keep.append(message)
                        else:
                            messages_cleaned += 1
                    
                    # Supprimer tous les messages et remettre seulement ceux à garder
                    storage.used = True  # Marquer comme utilisé pour vider
                    for message in messages_to_keep:
                        messages.add_message(request, message.level, message.message, message.tags)
                    
                    if messages_cleaned > 0 and settings.DEBUG:
                        print(f"[DEBUG] 🧹 {messages_cleaned} message(s) MWI-001 supprimé(s) du cache")
                    
                    if session_key in request.session:
                        del request.session[session_key]
                        if settings.DEBUG:
                            print(f"[DEBUG] ✅ Flag de redirection supprimé pour {user_type}")
                    
                    if redirect_count_key in request.session:
                        del request.session[redirect_count_key]
                        if settings.DEBUG:
                            print(f"[DEBUG] ✅ Compteur de redirection réinitialisé pour {user_type}")
                    
                    # Optionnel : nettoyer aussi les autres types pour éviter les conflits
                    for type_op in ['CONFIRMATION', 'LOGISTIQUE', 'PREPARATION', 'ADMIN']:
                        if type_op != user_type:  # Éviter de retraiter le type actuel
                            for key_prefix in [f'middleware_redirect_{type_op}', f'middleware_redirect_count_{type_op}']:
                                if key_prefix in request.session:
                                    del request.session[key_prefix]
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