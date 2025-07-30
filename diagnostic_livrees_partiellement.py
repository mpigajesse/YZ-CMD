#!/usr/bin/env python
"""
Script de diagnostic pour analyser les commandes livrées partiellement
et comprendre pourquoi le compteur ne fonctionne pas correctement.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import Commande, EtatCommande, Operation
from parametre.models import Operateur
from django.db.models import Q

def diagnostic_livrees_partiellement():
    """Diagnostic des commandes livrées partiellement"""
    print("🔍 Diagnostic des commandes livrées partiellement")
    print("=" * 60)
    
    # 1. Trouver l'opérateur de préparation
    operateur_prepa = Operateur.objects.filter(
        type_operateur='PREPARATION',
        actif=True
    ).first()
    
    if not operateur_prepa:
        print("❌ Aucun opérateur de préparation trouvé")
        return
    
    print(f"✅ Opérateur de préparation: {operateur_prepa.prenom} {operateur_prepa.nom}")
    
    # 2. Analyser toutes les commandes affectées à cet opérateur
    print("\n1. Analyse des commandes affectées à l'opérateur:")
    
    commandes_affectees = Commande.objects.filter(
        Q(etats__enum_etat__libelle='À imprimer') | Q(etats__enum_etat__libelle='En préparation'),
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article', 'etats').distinct()
    
    print(f"   - {commandes_affectees.count()} commandes affectées initialement")
    
    # 3. Analyser chaque commande pour déterminer si elle a été livrée partiellement
    commandes_livrees_partiellement = []
    commandes_renvoyees_logistique = []
    commandes_autres = []
    
    for cmd in commandes_affectees:
        print(f"\n   📦 Commande {cmd.id_yz} ({cmd.num_cmd}):")
        
        # Trouver l'état actuel
        etat_actuel = None
        for etat in cmd.etats.all().order_by('date_debut'):
            if etat.enum_etat.libelle in ['À imprimer', 'En préparation'] and not etat.date_fin:
                etat_actuel = etat
                break
        
        if not etat_actuel:
            print(f"      ❌ Pas d'état actuel trouvé")
            continue
        
        print(f"      État actuel: {etat_actuel.enum_etat.libelle} ({etat_actuel.date_debut.strftime('%d/%m/%Y %H:%M')})")
        
        # Vérifier s'il y a des états ultérieurs problématiques
        a_etats_ultérieurs_problematiques = False
        for etat in cmd.etats.all().order_by('date_debut'):
            if (etat.date_debut > etat_actuel.date_debut and 
                etat.enum_etat.libelle in ['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']):
                a_etats_ultérieurs_problematiques = True
                print(f"      ⚠️ État ultérieur problématique: {etat.enum_etat.libelle} ({etat.date_debut.strftime('%d/%m/%Y %H:%M')})")
                break
        
        if a_etats_ultérieurs_problematiques:
            print(f"      ❌ Exclue à cause d'états ultérieurs problématiques")
            continue
        
        # Vérifier les opérations de renvoi
        operation_renvoi = Operation.objects.filter(
            commande=cmd,
            type_operation='RENVOI_PREPARATION'
        ).first()
        
        if operation_renvoi:
            print(f"      🔄 Opération de renvoi trouvée ({operation_renvoi.date_operation.strftime('%d/%m/%Y %H:%M')})")
            commandes_renvoyees_logistique.append(cmd)
            continue
        
        # Vérifier l'historique des états
        has_partially_delivered_history = False
        for etat in cmd.etats.all().order_by('date_debut'):
            if (etat.enum_etat.libelle == 'Livrée Partiellement' and 
                etat.date_fin and 
                etat.date_fin < etat_actuel.date_debut):
                has_partially_delivered_history = True
                print(f"      📦 Historique de livraison partielle trouvé ({etat.date_debut.strftime('%d/%m/%Y %H:%M')})")
                break
        
        if has_partially_delivered_history:
            commandes_livrees_partiellement.append(cmd)
        else:
            commandes_autres.append(cmd)
            print(f"      ➡️ Commande normale")
    
    # 4. Résumé
    print(f"\n2. Résumé des catégories:")
    print(f"   - Commandes livrées partiellement: {len(commandes_livrees_partiellement)}")
    print(f"   - Commandes renvoyées par logistique: {len(commandes_renvoyees_logistique)}")
    print(f"   - Autres commandes: {len(commandes_autres)}")
    
    # 5. Détails des commandes livrées partiellement
    print(f"\n3. Détails des commandes livrées partiellement:")
    for cmd in commandes_livrees_partiellement:
        print(f"   📦 Commande {cmd.id_yz} ({cmd.num_cmd}): {cmd.client.prenom} {cmd.client.nom}")
        
        # Trouver l'état "Livrée Partiellement"
        etat_livree_partiellement = None
        for etat in cmd.etats.all().order_by('date_debut'):
            if etat.enum_etat.libelle == 'Livrée Partiellement':
                etat_livree_partiellement = etat
                break
        
        if etat_livree_partiellement:
            print(f"      Date livraison partielle: {etat_livree_partiellement.date_debut.strftime('%d/%m/%Y %H:%M')}")
            print(f"      Opérateur: {etat_livree_partiellement.operateur.prenom} {etat_livree_partiellement.operateur.nom}")
    
    # 6. Vérifier les commandes de renvoi
    print(f"\n4. Vérification des commandes de renvoi:")
    commandes_renvoi = Commande.objects.filter(
        num_cmd__startswith='RENVOI-',
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).distinct()
    
    print(f"   - {commandes_renvoi.count()} commandes de renvoi trouvées")
    
    for cmd in commandes_renvoi:
        print(f"   🔄 Commande de renvoi {cmd.id_yz} ({cmd.num_cmd})")
        
        # Chercher la commande originale
        num_cmd_original = cmd.num_cmd.replace('RENVOI-', '')
        commande_originale = Commande.objects.filter(num_cmd=num_cmd_original).first()
        
        if commande_originale:
            print(f"      Commande originale: {commande_originale.id_yz} ({commande_originale.num_cmd})")
            
            # Vérifier si la commande originale a été livrée partiellement
            etat_livree_partiellement = commande_originale.etats.filter(
                enum_etat__libelle='Livrée Partiellement'
            ).first()
            
            if etat_livree_partiellement:
                print(f"      ✅ Commande originale livrée partiellement ({etat_livree_partiellement.date_debut.strftime('%d/%m/%Y %H:%M')})")
            else:
                print(f"      ❌ Commande originale pas livrée partiellement")
    
    print(f"\n5. Conclusion:")
    print(f"   Le compteur devrait afficher {len(commandes_livrees_partiellement)} commandes livrées partiellement")
    print(f"   + {commandes_renvoi.count()} commandes de renvoi = {len(commandes_livrees_partiellement) + commandes_renvoi.count()} total")

if __name__ == '__main__':
    diagnostic_livrees_partiellement() 