#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import Operation, Commande, Operateur
from django.db.models import Q

def debug_affectations():
    print("=== DIAGNOSTIC DES AFFECTATIONS ===")
    
    # 1. Vérifier les opérations d'affectation par supervision
    operations_supervision = Operation.objects.filter(
        type_operation='AFFECTATION_SUPERVISION'
    )
    print(f"\n1. Opérations AFFECTATION_SUPERVISION: {operations_supervision.count()}")
    for op in operations_supervision:
        print(f"   - Commande {op.commande.id_yz} affectée par {op.operateur.nom_complet}")
    
    # 2. Vérifier les opérations d'affectation par admin
    operations_admin = Operation.objects.filter(
        type_operation='AFFECTATION_ADMIN'
    )
    print(f"\n2. Opérations AFFECTATION_ADMIN: {operations_admin.count()}")
    for op in operations_admin:
        print(f"   - Commande {op.commande.id_yz} affectée par {op.operateur.nom_complet}")
    
    # 3. Vérifier les opérateurs de préparation
    operateurs_prepa = Operateur.objects.filter(type_operateur='PREPARATION', actif=True)
    print(f"\n3. Opérateurs de préparation actifs: {operateurs_prepa.count()}")
    for op in operateurs_prepa:
        print(f"   - {op.nom_complet} (ID: {op.id})")
    
    # 4. Vérifier les commandes en préparation
    commandes_en_prepa = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation', 'Collectée', 'Emballée'],
        etats__date_fin__isnull=True
    ).distinct()
    print(f"\n4. Commandes en préparation: {commandes_en_prepa.count()}")
    
    # 5. Pour chaque opérateur de préparation, vérifier ses commandes
    for operateur in operateurs_prepa:
        commandes_operateur = Commande.objects.filter(
            etats__enum_etat__libelle__in=['À imprimer', 'En préparation', 'Collectée', 'Emballée'],
            etats__operateur=operateur,
            etats__date_fin__isnull=True
        ).distinct()
        print(f"\n5. Commandes de {operateur.nom_complet}: {commandes_operateur.count()}")
        for cmd in commandes_operateur:
            # Vérifier s'il y a une opération d'affectation pour cette commande
            op_supervision = Operation.objects.filter(
                commande=cmd,
                type_operation='AFFECTATION_SUPERVISION'
            ).first()
            op_admin = Operation.objects.filter(
                commande=cmd,
                type_operation='AFFECTATION_ADMIN'
            ).first()
            
            affectation_type = "Aucune"
            if op_supervision:
                affectation_type = f"SUPERVISION par {op_supervision.operateur.nom_complet}"
            elif op_admin:
                affectation_type = f"ADMIN par {op_admin.operateur.nom_complet}"
            
            print(f"   - {cmd.id_yz}: {affectation_type}")

if __name__ == "__main__":
    debug_affectations()
