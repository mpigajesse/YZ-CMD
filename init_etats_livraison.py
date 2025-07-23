import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import EnumEtatCmd

# Créer ou récupérer les états
for libelle, ordre, couleur in [
    ('Bon état', 90, '#10B981'),
    ('Défectueux', 91, '#EF4444'),
]:
    etat, created = EnumEtatCmd.objects.get_or_create(
        libelle=libelle,
        defaults={'ordre': ordre, 'couleur': couleur}
    )
    if created:
        print(f"✅ État '{libelle}' créé.")
    else:
        print(f"ℹ️  État '{libelle}' existe déjà.")
