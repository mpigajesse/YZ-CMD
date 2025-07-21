"""
Script pour vérifier pourquoi les commandes renvoyées par la logistique ne s'affichent pas.
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

def verifier_commandes_renvoyees():
    """
    Vérifie pourquoi les commandes renvoyées par la logistique ne s'affichent pas.
    """
    print("🔍 Vérification des commandes renvoyées par la logistique")
    print("=" * 60)
    
    # Récupérer un opérateur de préparation
    operateur_prepa = Operateur.objects.filter(
        type_operateur='PREPARATION',
        actif=True
    ).first()
    
    if not operateur_prepa:
        print("❌ Aucun opérateur de préparation actif trouvé")
        return
    
    print(f"✅ Opérateur de préparation: {operateur_prepa.prenom} {operateur_prepa.nom}")
    
    # 1. Vérifier toutes les opérations de renvoi
    print("\n1. Vérification de toutes les opérations de renvoi:")
    
    operations_renvoi = Operation.objects.filter(
        type_operation='RENVOI_PREPARATION'
    ).select_related('commande', 'operateur').order_by('-date_operation')
    
    print(f"   - {operations_renvoi.count()} opérations de renvoi trouvées")
    
    for op in operations_renvoi:
        print(f"   📦 Opération {op.id}:")
        print(f"      Commande: {op.commande.id_yz} ({op.commande.num_cmd})")
        print(f"      Opérateur: {op.operateur.prenom} {op.operateur.nom} ({op.operateur.type_operateur})")
        print(f"      Date: {op.date_operation.strftime('%d/%m/%Y %H:%M')}")
        
        # Vérifier si cette commande est affectée à l'opérateur de préparation
        etat_actuel = op.commande.etats.filter(
            enum_etat__libelle__in=['À imprimer', 'En préparation'],
            operateur=operateur_prepa,
            date_fin__isnull=True
        ).first()
        
        if etat_actuel:
            print(f"      ✅ Affectée à {operateur_prepa.prenom}")
        else:
            print(f"      ❌ Pas affectée à {operateur_prepa.prenom}")
    
    # 2. Vérifier les commandes avec état précédent "En cours de livraison"
    print("\n2. Vérification des commandes avec état précédent 'En cours de livraison':")
    
    commandes_affectees = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).exclude(
        etats__enum_etat__libelle__in=['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct()
    
    commandes_avec_etat_precedent_livraison = []
    
    for cmd in commandes_affectees:
        etats_commande = cmd.etats.all().order_by('date_debut')
        etat_actuel = None
        
        # Trouver l'état actuel
        for etat in etats_commande:
            if etat.enum_etat.libelle in ['À imprimer', 'En préparation'] and not etat.date_fin:
                etat_actuel = etat
                break
        
        if etat_actuel:
            # Trouver l'état précédent
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                    if etat.enum_etat.libelle == 'En cours de livraison':
                        commandes_avec_etat_precedent_livraison.append({
                            'commande': cmd,
                            'etat_actuel': etat_actuel,
                            'etat_precedent': etat
                        })
                        break
    
    print(f"   - {len(commandes_avec_etat_precedent_livraison)} commandes avec état précédent 'En cours de livraison'")
    
    for item in commandes_avec_etat_precedent_livraison:
        cmd = item['commande']
        etat_actuel = item['etat_actuel']
        etat_precedent = item['etat_precedent']
        
        print(f"   📦 Commande {cmd.id_yz} ({cmd.num_cmd}):")
        print(f"      État actuel: {etat_actuel.enum_etat.libelle} ({etat_actuel.date_debut.strftime('%d/%m/%Y %H:%M')})")
        print(f"      État précédent: {etat_precedent.enum_etat.libelle} ({etat_precedent.date_fin.strftime('%d/%m/%Y %H:%M')})")
        
        # Vérifier si cette commande a des états ultérieurs problématiques
        a_etats_ultérieurs_problematiques = False
        for etat in etats_commande:
            if (etat.date_debut > etat_actuel.date_debut and 
                etat.enum_etat.libelle in ['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']):
                a_etats_ultérieurs_problematiques = True
                print(f"      ⚠️ État ultérieur problématique: {etat.enum_etat.libelle} ({etat.date_debut.strftime('%d/%m/%Y %H:%M')})")
                break
        
        if not a_etats_ultérieurs_problematiques:
            print(f"      ✅ Devrait apparaître dans 'Renvoyées par logistique'")
        else:
            print(f"      ❌ Ne devrait PAS apparaître (états ultérieurs problématiques)")
    
    # 3. Vérifier les commandes qui devraient être dans "renvoyees_logistique"
    print("\n3. Commandes qui devraient être dans 'Renvoyées par logistique':")
    
    commandes_renvoyees_logistique = []
    
    for cmd in commandes_affectees:
        # Vérifier les opérations de renvoi
        operation_renvoi = Operation.objects.filter(
            commande=cmd,
            type_operation='RENVOI_PREPARATION'
        ).first()
        
        if operation_renvoi:
            commandes_renvoyees_logistique.append({
                'commande': cmd,
                'type': 'operation',
                'operation': operation_renvoi
            })
            continue
        
        # Vérifier l'état précédent
        etats_commande = cmd.etats.all().order_by('date_debut')
        etat_actuel = None
        
        for etat in etats_commande:
            if etat.enum_etat.libelle in ['À imprimer', 'En préparation'] and not etat.date_fin:
                etat_actuel = etat
                break
        
        if etat_actuel:
            # Vérifier s'il y a des états ultérieurs problématiques
            a_etats_ultérieurs_problematiques = False
            for etat in etats_commande:
                if (etat.date_debut > etat_actuel.date_debut and 
                    etat.enum_etat.libelle in ['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']):
                    a_etats_ultérieurs_problematiques = True
                    break
            
            if not a_etats_ultérieurs_problematiques:
                # Trouver l'état précédent
                for etat in reversed(etats_commande):
                    if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                        if etat.enum_etat.libelle == 'En cours de livraison':
                            commandes_renvoyees_logistique.append({
                                'commande': cmd,
                                'type': 'etat_precedent',
                                'etat_precedent': etat
                            })
                            break
    
    print(f"   - {len(commandes_renvoyees_logistique)} commandes identifiées")
    
    for item in commandes_renvoyees_logistique:
        cmd = item['commande']
        type_renvoi = item['type']
        
        print(f"   📦 Commande {cmd.id_yz} ({cmd.num_cmd}):")
        if type_renvoi == 'operation':
            operation = item['operation']
            print(f"      ✅ Opération de renvoi: {operation.date_operation.strftime('%d/%m/%Y %H:%M')}")
        elif type_renvoi == 'etat_precedent':
            etat_precedent = item['etat_precedent']
            print(f"      ✅ État précédent: {etat_precedent.enum_etat.libelle} ({etat_precedent.date_fin.strftime('%d/%m/%Y %H:%M')})")
    
    # 4. Conclusion
    print(f"\n4. Conclusion:")
    if commandes_renvoyees_logistique:
        print(f"   ✅ {len(commandes_renvoyees_logistique)} commandes devraient apparaître dans 'Renvoyées par logistique'")
        print(f"   Le problème vient probablement de la logique de filtrage dans la vue.")
    else:
        print(f"   ❌ Aucune commande identifiée comme renvoyée par la logistique")
        print(f"   Cela peut être normal si aucune commande n'a été renvoyée vers cet opérateur.")
    
    print("\n" + "=" * 60)
    print("✅ VÉRIFICATION TERMINÉE")
    print("=" * 60)

if __name__ == "__main__":
    verifier_commandes_renvoyees() 