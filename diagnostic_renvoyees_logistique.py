#!/usr/bin/env python
"""
Script de diagnostic pour analyser les commandes renvoyées par logistique
et comprendre pourquoi il manque une commande.
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

def diagnostic_renvoyees_logistique():
    """Diagnostic des commandes renvoyées par logistique"""
    print("🔍 Diagnostic des commandes renvoyées par logistique")
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
    
    # 3. Analyser chaque commande pour déterminer si elle a été renvoyée par logistique
    commandes_renvoyees_logistique = []
    commandes_livrees_partiellement = []
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
        
        # Vérifier l'historique des états pour renvoi depuis livraison
        has_return_from_delivery_history = False
        for etat in cmd.etats.all().order_by('date_debut'):
            if (etat.enum_etat.libelle == 'En cours de livraison' and 
                etat.date_fin and 
                etat.date_fin < etat_actuel.date_debut):
                has_return_from_delivery_history = True
                print(f"      🚚 Historique de renvoi depuis livraison trouvé ({etat.date_debut.strftime('%d/%m/%Y %H:%M')})")
                break
        
        if has_return_from_delivery_history:
            commandes_renvoyees_logistique.append(cmd)
            continue
        
        # Vérifier l'historique pour livraison partielle
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
    print(f"   - Commandes renvoyées par logistique: {len(commandes_renvoyees_logistique)}")
    print(f"   - Commandes livrées partiellement: {len(commandes_livrees_partiellement)}")
    print(f"   - Autres commandes: {len(commandes_autres)}")
    
    # 5. Détails des commandes renvoyées par logistique
    print(f"\n3. Détails des commandes renvoyées par logistique:")
    for cmd in commandes_renvoyees_logistique:
        print(f"   📦 Commande {cmd.id_yz} ({cmd.num_cmd}): {cmd.client.prenom} {cmd.client.nom}")
        
        # Vérifier les opérations de renvoi
        operation_renvoi = Operation.objects.filter(
            commande=cmd,
            type_operation='RENVOI_PREPARATION'
        ).first()
        
        if operation_renvoi:
            print(f"      🔄 Opération de renvoi: {operation_renvoi.date_operation.strftime('%d/%m/%Y %H:%M')}")
        else:
            # Chercher l'état "En cours de livraison" précédent
            etat_livraison = None
            for etat in cmd.etats.all().order_by('date_debut'):
                if etat.enum_etat.libelle == 'En cours de livraison' and etat.date_fin:
                    etat_livraison = etat
                    break
            
            if etat_livraison:
                print(f"      🚚 Renvoi depuis livraison: {etat_livraison.date_fin.strftime('%d/%m/%Y %H:%M')}")
    
    # 6. Vérifier les commandes manquantes
    print(f"\n4. Vérification des commandes manquantes:")
    
    # Compter les commandes dans l'interface logistique (approximation)
    commandes_logistique = Commande.objects.filter(
        etats__enum_etat__libelle='En préparation',
        etats__date_fin__isnull=True
    ).distinct()
    
    print(f"   - Total commandes en préparation: {commandes_logistique.count()}")
    print(f"   - Commandes renvoyées détectées: {len(commandes_renvoyees_logistique)}")
    print(f"   - Différence: {commandes_logistique.count() - len(commandes_renvoyees_logistique)}")
    
    # 7. Analyser les commandes qui pourraient être manquées
    print(f"\n5. Analyse des commandes potentiellement manquées:")
    
    for cmd in commandes_affectees:
        if cmd not in commandes_renvoyees_logistique and cmd not in commandes_livrees_partiellement:
            print(f"   📦 Commande {cmd.id_yz} ({cmd.num_cmd}): {cmd.client.prenom} {cmd.client.nom}")
            
            # Analyser l'historique des états
            etats_commande = cmd.etats.all().order_by('date_debut')
            print(f"      Historique des états:")
            for etat in etats_commande:
                status = "ACTIF" if not etat.date_fin else "TERMINÉ"
                print(f"        - {etat.enum_etat.libelle} ({etat.date_debut.strftime('%d/%m/%Y %H:%M')}) [{status}]")
    
    print(f"\n6. Conclusion:")
    print(f"   Le compteur devrait afficher {len(commandes_renvoyees_logistique)} commandes renvoyées par logistique")

if __name__ == '__main__':
    diagnostic_renvoyees_logistique() 