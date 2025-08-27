import os
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User, Group
from parametre.models import Operateur

def generate_operators():
    print("Démarrage de la génération des opérateurs...")

    # Assurez-vous que les groupes existent
    group_confirme, created_confirme = Group.objects.get_or_create(name='operateur_confirme')
    if created_confirme:
        print(f"Groupe 'operateur_confirme' créé.")
    group_logistique, created_logistique = Group.objects.get_or_create(name='operateur_logistique')
    if created_logistique:
        print(f"Groupe 'operateur_logistique' créé.")

    group_preparation, created_preparation = Group.objects.get_or_create(name='operateur_preparation')
    if created_preparation:
        print(f"Groupe 'operateur_preparation' créé.")

    # Groupe Superviseur (préparation)
    group_superviseur, created_superviseur = Group.objects.get_or_create(name='superviseur')
    if created_superviseur:
        print(f"Groupe 'superviseur' créé.")

    # Génération des opérateurs de Confirmation
    for i in range(1, 6):
        username = f"YZ-OPCO{i:02d}"
        email = f"{username.lower()}@gmail.com"
        password = "123"
        prenom = f"PrenomCO{i}"
        nom = f"NomCO{i}"
        
        try:
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': email,
                'first_name': prenom,
                'last_name': nom,
                'is_active': True,
            })
            if created:
                user.set_password(password)
                user.save()
                print(f"Utilisateur Django '{username}' créé.")
            else:
                print(f"Utilisateur Django '{username}' existe déjà.")
            
            operateur, created_op = Operateur.objects.get_or_create(user=user, defaults={
                'nom': nom,
                'prenom': prenom,
                'mail': email,
                'type_operateur': 'CONFIRMATION',
                'telephone': f'+2126{i:08d}',
                'adresse': f'Adresse CO {i}',
                'actif': True,
            })
            if created_op:
                print(f"Opérateur '{username}' (Confirmation) créé et lié à l'utilisateur.")
                user.groups.add(group_confirme)
                print(f"Utilisateur '{username}' ajouté au groupe '{group_confirme.name}'.")
            else:
                print(f"Opérateur '{username}' (Confirmation) existe déjà.")
                if group_confirme not in user.groups.all():
                    user.groups.add(group_confirme)
                    print(f"Utilisateur '{username}' ajouté au groupe '{group_confirme.name}'.")

        except Exception as e:
            print(f"Erreur lors de la création de l'opérateur '{username}' (Confirmation): {e}")

    # Génération des opérateurs Logistiques
    for i in range(1, 6):
        username = f"YZ-OPL0{i}"
        email = f"{username.lower()}@gmail.com"
        password = "123"
        prenom = f"PrenomLO{i}"
        nom = f"NomLO{i}"
        
        try:
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': email,
                'first_name': prenom,
                'last_name': nom,
                'is_active': True,
            })
            if created:
                user.set_password(password)
                user.save()
                print(f"Utilisateur Django '{username}' créé.")
            else:
                print(f"Utilisateur Django '{username}' existe déjà.")

            operateur, created_op = Operateur.objects.get_or_create(user=user, defaults={
                'nom': nom,
                'prenom': prenom,
                'mail': email,
                'type_operateur': 'LOGISTIQUE',
                'telephone': f'+2127{i:08d}',
                'adresse': f'Adresse LO {i}',
                'actif': True,
            })
            if created_op:
                print(f"Opérateur '{username}' (Logistique) créé et lié à l'utilisateur.")
                user.groups.add(group_logistique)
                print(f"Utilisateur '{username}' ajouté au groupe '{group_logistique.name}'.")
            else:
                print(f"Opérateur '{username}' (Logistique) existe déjà.")
                if group_logistique not in user.groups.all():
                    user.groups.add(group_logistique)
                    print(f"Utilisateur '{username}' ajouté au groupe '{group_logistique.name}'.")

        except Exception as e:
            print(f"Erreur lors de la création de l'opérateur '{username}' (Logistique): {e}")

    # Génération des opérateurs de Préparation
    for i in range(1, 6):
        username = f"YZ-OPR0{i}"
        email = f"{username.lower()}@gmail.com"
        password = "123"
        prenom = f"PrenomPO{i}"
        nom = f"NomPO{i}"
        
        try:
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': email,
                'first_name': prenom,
                'last_name': nom,
                'is_active': True,
            })
            if created:
                user.set_password(password)
                user.save()
                print(f"Utilisateur Django '{username}' créé.")
            else:
                print(f"Utilisateur Django '{username}' existe déjà.")

            operateur, created_op = Operateur.objects.get_or_create(user=user, defaults={
                'nom': nom,
                'prenom': prenom,
                'mail': email,
                'type_operateur': 'PREPARATION',
                'telephone': f'+2128{i:08d}',
                'adresse': f'Adresse PO {i}',
                'actif': True,
            })
            if created_op:
                print(f"Opérateur '{username}' (Préparation) créé et lié à l'utilisateur.")
                user.groups.add(group_preparation)
                print(f"Utilisateur '{username}' ajouté au groupe '{group_preparation.name}'.")
            else:
                print(f"Opérateur '{username}' (Préparation) existe déjà.")
                if group_preparation not in user.groups.all():
                    user.groups.add(group_preparation)
                    print(f"Utilisateur '{username}' ajouté au groupe '{group_preparation.name}'.")

        except Exception as e:
            print(f"Erreur lors de la création de l'opérateur '{username}' (Préparation): {e}")

    # Génération des Superviseurs de Préparation
    for i in range(1, 4):
        username = f"YZ-OPSP0{i}"
        email = f"{username.lower()}@gmail.com"
        password = "123"
        prenom = f"PrenomSUP{i}"
        nom = f"NomSUP{i}"
        
        try:
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': email,
                'first_name': prenom,
                'last_name': nom,
                'is_active': True,
            })
            if created:
                user.set_password(password)
                user.save()
                print(f"Utilisateur Django '{username}' créé.")
            else:
                print(f"Utilisateur Django '{username}' existe déjà.")

            operateur, created_op = Operateur.objects.get_or_create(user=user, defaults={
                'nom': nom,
                'prenom': prenom,
                'mail': email,
                'type_operateur': 'SUPERVISEUR_PREPARATION',
                'telephone': f'+2129{i:08d}',
                'adresse': f'Adresse SUP {i}',
                'actif': True,
            })
            if created_op:
                print(f"Opérateur '{username}' (Superviseur Préparation) créé et lié à l'utilisateur.")
                user.groups.add(group_superviseur)
                print(f"Utilisateur '{username}' ajouté au groupe '{group_superviseur.name}'.")
            else:
                print(f"Opérateur '{username}' (Superviseur Préparation) existe déjà.")
                if group_superviseur not in user.groups.all():
                    user.groups.add(group_superviseur)
                    print(f"Utilisateur '{username}' ajouté au groupe '{group_superviseur.name}'.")

        except Exception as e:
            print(f"Erreur lors de la création du superviseur '{username}': {e}")
    
    print("Génération des opérateurs terminée.")

if __name__ == '__main__':
    generate_operators() 