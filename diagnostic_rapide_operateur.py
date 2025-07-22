import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from parametre.models import Operateur

USERNAME = "YZ-OPR01"  # Modifie ici si besoin

try:
    user = User.objects.get(username=USERNAME)
    print(f"Utilisateur : {user.username}")
    print(f"  is_active (User) : {user.is_active}")
    op = Operateur.objects.get(user=user)
    print(f"  type_operateur : {op.type_operateur}")
    print(f"  is_preparation : {op.is_preparation}")
    print(f"  actif (Operateur) : {op.actif}")
except User.DoesNotExist:
    print(f"Utilisateur '{USERNAME}' introuvable.")
except Operateur.DoesNotExist:
    print(f"Profil opérateur pour '{USERNAME}' introuvable.") 