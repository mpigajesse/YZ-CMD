import os
import django

# Initialisation de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import EnumEtatCmd

print("Liste des états EnumEtatCmd :")
for etat in EnumEtatCmd.objects.all().order_by('ordre', 'libelle'):
    print(f"- {etat.libelle} (ordre: {etat.ordre}, couleur: {etat.couleur})") 