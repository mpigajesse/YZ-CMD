#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from kpis.models import KPIConfiguration

configs = KPIConfiguration.objects.all()
print(f"Total configurations: {configs.count()}")

# Afficher quelques exemples
for config in configs[:5]:
    print(f"- {config.nom_parametre}: {config.valeur} ({config.categorie})")
