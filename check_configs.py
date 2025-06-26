#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from kpis.models import KPIConfiguration

print("Configurations KPI existantes:")
print("=" * 50)

configs = KPIConfiguration.objects.all()
print(f"Nombre total: {configs.count()}")
print()

for config in configs:
    print(f"Nom: {config.nom_parametre}")
    print(f"Valeur: {config.valeur} {config.unite}")
    print(f"Description: {config.description}")
    print(f"Min: {config.valeur_min}, Max: {config.valeur_max}")
    print("-" * 30)
