#!/usr/bin/env python
import os
import django
import sys

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'YZ_CMD.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    django.setup()
    
    from commande.models import Commande, EnumEtatCmd, EtatCommande
    
    print('=== DIAGNOSTIC DES ÉTATS ===')
    print(f'Nombre total de commandes: {Commande.objects.count()}')
    print(f'Nombre total d\'EnumEtatCmd: {EnumEtatCmd.objects.count()}')
    print(f'Nombre total d\'EtatCommande: {EtatCommande.objects.count()}')
    print()

    print('=== EnumEtatCmd existants ===')
    for enum_etat in EnumEtatCmd.objects.all():
        print(f'- {enum_etat.libelle} (ID: {enum_etat.id})')
    print()

    print('=== Commandes récentes (5 dernières) ===')
    for cmd in Commande.objects.order_by('-id')[:5]:
        etat_actuel = cmd.etat_actuel
        if etat_actuel:
            print(f'Commande {cmd.num_cmd}: État = {etat_actuel.enum_etat.libelle}')
        else:
            print(f'Commande {cmd.num_cmd}: AUCUN ÉTAT ACTUEL')
            # Vérifier s'il y a des états pour cette commande
            etats_count = cmd.etats.count()
            print(f'  -> Nombre d\'états total: {etats_count}')
            if etats_count > 0:
                dernier_etat = cmd.etats.first()
                print(f'  -> Dernier état: {dernier_etat.enum_etat.libelle} (date_fin: {dernier_etat.date_fin})')
                
    print()
    print('=== Test de la propriété etat_actuel ===')
    # Tester la logique de etat_actuel
    cmd_test = Commande.objects.first()
    if cmd_test:
        print(f'Commande test: {cmd_test.num_cmd}')
        etats_actifs = cmd_test.etats.filter(date_fin__isnull=True)
        print(f'États actifs (date_fin=NULL): {etats_actifs.count()}')
        for etat in etats_actifs:
            print(f'  -> {etat.enum_etat.libelle} (ID: {etat.id}, date_debut: {etat.date_debut})')

except Exception as e:
    print(f'Erreur: {e}')
    import traceback
    traceback.print_exc()