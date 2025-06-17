from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User, Group
from parametre.models import Operateur # Assurez-vous que ce chemin est correct
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm # Importez PasswordChangeForm

# Create your views here.

@login_required
def dashboard(request):
    """Page d'accueil de l'interface opérateur de confirmation"""
    return render(request, 'composant_generale/operatConfirme/home.html')

@login_required
def liste_commandes(request):
    """Liste des commandes à confirmer"""
    return render(request, 'operatConfirme/liste_commande.html')

@login_required
def parametre(request):
    """Page des paramètres opérateur confirmation"""
    return render(request, 'operatConfirme/parametre.html')

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
    """Page de changement de mot de passe pour l'opérateur de confirmation"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important! Pour garder l'utilisateur connecté
            messages.success(request, 'Votre mot de passe a été mis à jour avec succès !')
            return redirect('operatConfirme:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'operatConfirme/changer_mot_de_passe.html', {'form': form})
