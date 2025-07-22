import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from parametre.models import Operateur

print("Liste des opérateurs de préparation :")
trouve = False
for op in Operateur.objects.all():
    if op.type_operateur == 'PREPARATION':
        trouve = True
        print(f"- {op.user.username} | {op.prenom} {op.nom} | actif: {op.actif}")
        if not op.actif:
            print(f"  ⚠️  Cet opérateur est INACTIF !")
    else:
        # Optionnel : signaler les opérateurs mal typés
        pass
if not trouve:
    print("Aucun opérateur de préparation trouvé.") 