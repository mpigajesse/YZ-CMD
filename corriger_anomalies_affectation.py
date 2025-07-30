"""
Script de correction des anomalies d'affectation détectées.
Corrige les commandes sans état actuel et les affectations incorrectes.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import Commande, EtatCommande, Operation, EnumEtatCmd
from parametre.models import Operateur
from django.utils import timezone
from datetime import timedelta

def corriger_anomalies_affectation():
    """
    Corrige les anomalies d'affectation détectées.
    """
    print("🔧 Correction des anomalies d'affectation")
    print("=" * 50)
    
    # 1. Récupérer les opérateurs de préparation actifs
    operateurs_prepa = Operateur.objects.filter(
        type_operateur='PREPARATION',
        actif=True
    ).order_by('id')
    
    if not operateurs_prepa.exists():
        print("❌ Aucun opérateur de préparation actif trouvé")
        return
    
    print(f"✅ {operateurs_prepa.count()} opérateurs de préparation actifs disponibles")
    
    # 2. Récupérer les états nécessaires
    etat_en_preparation = EnumEtatCmd.objects.filter(libelle='En préparation').first()
    etat_a_imprimer = EnumEtatCmd.objects.filter(libelle='À imprimer').first()
    
    if not etat_en_preparation or not etat_a_imprimer:
        print("❌ États 'En préparation' ou 'À imprimer' non trouvés")
        return
    
    # 3. Corriger les commandes renvoyées sans état actuel
    print("\n3. Correction des commandes renvoyées sans état actuel:")
    commandes_renvoyees_sans_etat = []
    
    # Commandes avec opération de renvoi mais sans état actuel
    commandes_renvoyees = Commande.objects.filter(
        operations__type_operation='RENVOI_PREPARATION'
    ).distinct()
    
    for cmd in commandes_renvoyees:
        etat_actuel = cmd.etats.filter(
            enum_etat__libelle__in=['À imprimer', 'En préparation'],
            date_fin__isnull=True
        ).first()
        
        if not etat_actuel:
            commandes_renvoyees_sans_etat.append(cmd)
    
    print(f"   - {len(commandes_renvoyees_sans_etat)} commandes renvoyées sans état actuel")
    
    for i, cmd in enumerate(commandes_renvoyees_sans_etat):
        # Trouver l'opération de renvoi la plus récente
        operation_renvoi = cmd.operations.filter(
            type_operation='RENVOI_PREPARATION'
        ).order_by('-date_operation').first()
        
        if operation_renvoi:
            # Affecter à l'opérateur qui a fait le renvoi ou au premier opérateur disponible
            operateur_affectation = operation_renvoi.operateur if operation_renvoi.operateur.type_operateur == 'PREPARATION' else operateurs_prepa.first()
            
            # Créer l'état "En préparation"
            EtatCommande.objects.create(
                commande=cmd,
                enum_etat=etat_en_preparation,
                operateur=operateur_affectation,
                date_debut=operation_renvoi.date_operation,
                commentaire=f"Correction automatique - Renvoi depuis la logistique"
            )
            
            print(f"   ✅ Commande {cmd.id_yz}: affectée à {operateur_affectation.prenom} {operateur_affectation.nom}")
    
    # 4. Corriger les commandes livrées partiellement sans état actuel
    print("\n4. Correction des commandes livrées partiellement sans état actuel:")
    commandes_livrees_partiellement_sans_etat = []
    
    commandes_livrees_partiellement = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée Partiellement'
    ).distinct()
    
    for cmd in commandes_livrees_partiellement:
        etat_actuel = cmd.etats.filter(
            enum_etat__libelle__in=['À imprimer', 'En préparation'],
            date_fin__isnull=True
        ).first()
        
        if not etat_actuel:
            commandes_livrees_partiellement_sans_etat.append(cmd)
    
    print(f"   - {len(commandes_livrees_partiellement_sans_etat)} commandes livrées partiellement sans état actuel")
    
    for i, cmd in enumerate(commandes_livrees_partiellement_sans_etat):
        # Trouver l'état "Livrée Partiellement"
        etat_livree_partiellement = cmd.etats.filter(
            enum_etat__libelle='Livrée Partiellement'
        ).order_by('-date_debut').first()
        
        if etat_livree_partiellement:
            # Affecter au premier opérateur disponible
            operateur_affectation = operateurs_prepa.first()
            
            # Créer l'état "En préparation"
            EtatCommande.objects.create(
                commande=cmd,
                enum_etat=etat_en_preparation,
                operateur=operateur_affectation,
                date_debut=etat_livree_partiellement.date_fin or timezone.now(),
                commentaire=f"Correction automatique - Livraison partielle"
            )
            
            print(f"   ✅ Commande {cmd.id_yz}: affectée à {operateur_affectation.prenom} {operateur_affectation.nom}")
    
    # 5. Corriger les commandes de renvoi sans état actuel
    print("\n5. Correction des commandes de renvoi sans état actuel:")
    commandes_renvoi_sans_etat = []
    
    commandes_renvoi = Commande.objects.filter(
        num_cmd__startswith='RENVOI-'
    ).distinct()
    
    for cmd in commandes_renvoi:
        etat_actuel = cmd.etats.filter(
            enum_etat__libelle__in=['À imprimer', 'En préparation'],
            date_fin__isnull=True
        ).first()
        
        if not etat_actuel:
            commandes_renvoi_sans_etat.append(cmd)
    
    print(f"   - {len(commandes_renvoi_sans_etat)} commandes de renvoi sans état actuel")
    
    for i, cmd in enumerate(commandes_renvoi_sans_etat):
        # Trouver l'opération de livraison partielle qui a créé cette commande
        operation_livraison_partielle = Operation.objects.filter(
            type_operation='LIVRAISON_PARTIELLE',
            conclusion__icontains=cmd.num_cmd.replace('RENVOI-', '')
        ).order_by('-date_operation').first()
        
        if operation_livraison_partielle:
            # Affecter à l'opérateur qui a fait la livraison partielle ou au premier opérateur disponible
            operateur_affectation = operation_livraison_partielle.operateur if operation_livraison_partielle.operateur.type_operateur == 'PREPARATION' else operateurs_prepa.first()
            
            # Créer l'état "En préparation"
            EtatCommande.objects.create(
                commande=cmd,
                enum_etat=etat_en_preparation,
                operateur=operateur_affectation,
                date_debut=operation_livraison_partielle.date_operation,
                commentaire=f"Correction automatique - Commande de renvoi (livraison partielle)"
            )
            
            print(f"   ✅ Commande {cmd.id_yz} ({cmd.num_cmd}): affectée à {operateur_affectation.prenom} {operateur_affectation.nom}")
        else:
            # Fallback : affecter au premier opérateur disponible
            operateur_affectation = operateurs_prepa.first()
            
            EtatCommande.objects.create(
                commande=cmd,
                enum_etat=etat_en_preparation,
                operateur=operateur_affectation,
                date_debut=timezone.now(),
                commentaire=f"Correction automatique - Commande de renvoi (fallback)"
            )
            
            print(f"   ✅ Commande {cmd.id_yz} ({cmd.num_cmd}): affectée à {operateur_affectation.prenom} {operateur_affectation.nom} (fallback)")
    
    # 6. Rééquilibrer les affectations si nécessaire
    print("\n6. Rééquilibrage des affectations:")
    
    # Compter les commandes par opérateur
    repartition = {}
    for op in operateurs_prepa:
        nb_commandes = Commande.objects.filter(
            etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
            etats__operateur=op,
            etats__date_fin__isnull=True
        ).distinct().count()
        repartition[op] = nb_commandes
        print(f"   - {op.prenom} {op.nom}: {nb_commandes} commandes")
    
    # Identifier les opérateurs surchargés et sous-chargés
    commandes_par_op = list(repartition.values())
    if commandes_par_op:
        moyenne = sum(commandes_par_op) / len(commandes_par_op)
        seuil_surcharge = moyenne + 2
        seuil_sous_charge = max(0, moyenne - 2)
        
        print(f"   - Moyenne: {moyenne:.1f} commandes par opérateur")
        print(f"   - Seuil de surcharge: {seuil_surcharge:.1f}")
        print(f"   - Seuil de sous-charge: {seuil_sous_charge:.1f}")
        
        # Rééquilibrer si nécessaire
        op_surcharges = [op for op, nb in repartition.items() if nb > seuil_surcharge]
        op_sous_charges = [op for op, nb in repartition.items() if nb < seuil_sous_charge]
        
        if op_surcharges and op_sous_charges:
            print("   - Rééquilibrage en cours...")
            
            for op_surcharge in op_surcharges:
                nb_a_transferer = int(repartition[op_surcharge] - moyenne)
                commandes_a_transferer = Commande.objects.filter(
                    etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
                    etats__operateur=op_surcharge,
                    etats__date_fin__isnull=True
                ).distinct()[:nb_a_transferer]
                
                for cmd in commandes_a_transferer:
                    # Terminer l'état actuel
                    etat_actuel = cmd.etats.filter(
                        enum_etat__libelle__in=['À imprimer', 'En préparation'],
                        operateur=op_surcharge,
                        date_fin__isnull=True
                    ).first()
                    
                    if etat_actuel:
                        etat_actuel.date_fin = timezone.now()
                        etat_actuel.save()
                        
                        # Affecter à un opérateur sous-chargé
                        op_destination = op_sous_charges[0]  # Premier opérateur sous-chargé
                        
                        EtatCommande.objects.create(
                            commande=cmd,
                            enum_etat=etat_actuel.enum_etat,
                            operateur=op_destination,
                            date_debut=timezone.now(),
                            commentaire=f"Rééquilibrage automatique depuis {op_surcharge.prenom} {op_surcharge.nom}"
                        )
                        
                        print(f"     ✅ Commande {cmd.id_yz}: transférée de {op_surcharge.prenom} vers {op_destination.prenom}")
    
    print("\n" + "=" * 50)
    print("✅ CORRECTION TERMINÉE")
    print("=" * 50)

if __name__ == "__main__":
    corriger_anomalies_affectation() 