from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from functools import wraps
from parametre.models import Operateur

def superviseur_preparation_required(view_func):
    """
    Décorateur qui vérifie que l'utilisateur est un superviseur de préparation
    ou un opérateur de préparation (pour la compatibilité)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Pour les requêtes AJAX, renvoyer JSON au lieu de rediriger
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'message': 'Authentification requise'}, status=401)
            return redirect('login')
        
        try:
            operateur = Operateur.objects.get(user=request.user, actif=True)
            
            # Autoriser les superviseurs, les opérateurs de préparation et ADMIN
            if operateur.type_operateur in ['SUPERVISEUR_PREPARATION', 'PREPARATION', 'ADMIN']:
                return view_func(request, *args, **kwargs)
            else:
                # Pour les requêtes AJAX, renvoyer JSON au lieu de rediriger
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                    from django.http import JsonResponse
                    return JsonResponse({'success': False, 'message': 'Accès non autorisé. Seuls les superviseurs et opérateurs de préparation peuvent accéder à cette fonction.'}, status=403)
                messages.error(request, "Accès non autorisé. Seuls les superviseurs et opérateurs de préparation peuvent accéder à cette page.")
                return redirect('Superpreparation:home')
                
        except Operateur.DoesNotExist:
            # Fallback si pas de profil: autoriser selon groupes Django
            if request.user.groups.filter(name__in=['superviseur', 'operateur_preparation']).exists():
                return view_func(request, *args, **kwargs)
            
            # Pour les requêtes AJAX, renvoyer JSON au lieu de rediriger
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
                from django.http import JsonResponse
                return JsonResponse({'success': False, 'message': 'Votre profil opérateur n\'existe pas.'}, status=403)
            messages.error(request, "Votre profil opérateur n'existe pas.")
            return redirect('login')
    
    return _wrapped_view

def superviseur_only_required(view_func):
    """
    Décorateur qui vérifie que l'utilisateur est UNIQUEMENT un superviseur de préparation
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        try:
            operateur = Operateur.objects.get(user=request.user, actif=True)
            
            # Autoriser uniquement les superviseurs
            if operateur.type_operateur == 'SUPERVISEUR_PREPARATION':
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Accès non autorisé. Seuls les superviseurs de préparation peuvent accéder à cette page.")
                return redirect('Superpreparation:home')
                
        except Operateur.DoesNotExist:
            # Fallback: autoriser si dans le groupe superviseur
            if request.user.groups.filter(name='superviseur').exists():
                return view_func(request, *args, **kwargs)
            messages.error(request, "Votre profil opérateur n'existe pas.")
            return redirect('login')
    
    return _wrapped_view

def preparation_team_required(view_func):
    """
    Décorateur qui vérifie que l'utilisateur fait partie de l'équipe de préparation
    (superviseurs ET opérateurs de préparation)
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        try:
            operateur = Operateur.objects.get(user=request.user, actif=True)
            
            # Autoriser les superviseurs, les opérateurs de préparation et ADMIN
            if operateur.type_operateur in ['SUPERVISEUR_PREPARATION', 'PREPARATION', 'ADMIN']:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Accès non autorisé. Seuls les membres de l'équipe de préparation peuvent accéder à cette page.")
                return redirect('Superpreparation:home')
                
        except Operateur.DoesNotExist:
            # Fallback si pas de profil: autoriser selon groupes Django
            if request.user.groups.filter(name__in=['superviseur', 'operateur_preparation']).exists():
                return view_func(request, *args, **kwargs)
            messages.error(request, "Votre profil opérateur n'existe pas.")
            return redirect('login')
    
    return _wrapped_view
