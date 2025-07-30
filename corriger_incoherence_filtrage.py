"""
Script de correction de l'incohérence entre les statistiques et le filtrage.
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

def corriger_incoherence_filtrage():
    """
    Corrige l'incohérence entre les statistiques et le filtrage.
    """
    print("🔧 Correction de l'incohérence de filtrage")
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
    
    # 1. Analyser le problème dans l'interface de préparation
    print("\n1. Analyse de l'interface de préparation:")
    
    # Récupérer toutes les commandes affectées
    commandes_affectees = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).exclude(
        etats__enum_etat__libelle__in=['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct()
    
    print(f"   - {commandes_affectees.count()} commandes affectées")
    
    # 2. Analyser chaque commande pour l'onglet "renvoyees_logistique"
    print("\n2. Analyse pour l'onglet 'Renvoyées par logistique':")
    
    commandes_renvoyees_logistique = []
    
    for cmd in commandes_affectees:
        print(f"\n   📦 Commande {cmd.id_yz} ({cmd.num_cmd}):")
        
        # Vérifier les opérations de renvoi
        from commande.models import Operation
        operation_renvoi = Operation.objects.filter(
            commande=cmd,
            type_operation='RENVOI_PREPARATION'
        ).first()
        
        if operation_renvoi:
            print(f"      ✅ Opération de renvoi trouvée: {operation_renvoi.date_operation.strftime('%d/%m/%Y %H:%M')}")
            commandes_renvoyees_logistique.append(cmd)
            continue
        
        # Vérifier l'état précédent
        etats_commande = cmd.etats.all().order_by('date_debut')
        etat_actuel = None
        
        # Trouver l'état actuel
        for etat in etats_commande:
            if etat.enum_etat.libelle in ['À imprimer', 'En préparation'] and not etat.date_fin:
                etat_actuel = etat
                break
        
        if etat_actuel:
            # Trouver l'état précédent
            etat_precedent = None
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                    if etat.enum_etat.libelle not in ['À imprimer', 'En préparation']:
                        etat_precedent = etat
                        break
            
            if etat_precedent:
                print(f"      ⬅️ État précédent: {etat_precedent.enum_etat.libelle} ({etat_precedent.date_fin.strftime('%d/%m/%Y %H:%M')})")
                
                if etat_precedent.enum_etat.libelle == 'En cours de livraison':
                    print(f"      ✅ Commande renvoyée depuis la logistique")
                    commandes_renvoyees_logistique.append(cmd)
                else:
                    print(f"      ❌ État précédent: {etat_precedent.enum_etat.libelle} (pas 'En cours de livraison')")
            else:
                print(f"      ❓ Aucun état précédent trouvé")
    
    print(f"\n3. Résumé pour 'Renvoyées par logistique':")
    print(f"   - Commandes identifiées: {len(commandes_renvoyees_logistique)}")
    
    # 4. Analyser l'interface logistique
    print("\n4. Analyse de l'interface logistique:")
    
    # Récupérer un opérateur logistique
    operateur_log = Operateur.objects.filter(
        type_operateur='LOGISTIQUE',
        actif=True
    ).first()
    
    if operateur_log:
        print(f"   - Opérateur logistique: {operateur_log.prenom} {operateur_log.nom}")
        
        # Récupérer les commandes renvoyées par cet opérateur
        commandes_renvoyees_log = Commande.objects.filter(
            operations__type_operation='RENVOI_PREPARATION',
            operations__operateur=operateur_log
        ).distinct()
        
        print(f"   - {commandes_renvoyees_log.count()} commandes renvoyées par la logistique")
        
        for cmd in commandes_renvoyees_log:
            operation = cmd.operations.filter(
                type_operation='RENVOI_PREPARATION',
                operateur=operateur_log
            ).first()
            
            if operation:
                print(f"      - Commande {cmd.id_yz} ({cmd.num_cmd}): {operation.date_operation.strftime('%d/%m/%Y %H:%M')}")
    
    # 5. Identifier les commandes manquantes
    print("\n5. Identification des commandes manquantes:")
    
    # Vérifier les commandes qui devraient être dans "renvoyees_logistique" mais ne sont pas comptées
    commandes_manquantes = []
    
    for cmd in commandes_affectees:
        # Vérifier si c'est une commande de renvoi (livraison partielle)
        if cmd.num_cmd and cmd.num_cmd.startswith('RENVOI-'):
            continue  # C'est pour l'onglet "livrees_partiellement"
        
        # Vérifier les opérations de renvoi
        operation_renvoi = Operation.objects.filter(
            commande=cmd,
            type_operation='RENVOI_PREPARATION'
        ).first()
        
        if operation_renvoi:
            if cmd not in commandes_renvoyees_logistique:
                commandes_manquantes.append(cmd)
            continue
        
        # Vérifier l'état précédent
        etats_commande = cmd.etats.all().order_by('date_debut')
        etat_actuel = None
        
        for etat in etats_commande:
            if etat.enum_etat.libelle in ['À imprimer', 'En préparation'] and not etat.date_fin:
                etat_actuel = etat
                break
        
        if etat_actuel:
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                    if etat.enum_etat.libelle == 'En cours de livraison':
                        if cmd not in commandes_renvoyees_logistique:
                            commandes_manquantes.append(cmd)
                        break
    
    if commandes_manquantes:
        print(f"   ⚠️ {len(commandes_manquantes)} commandes manquantes dans 'renvoyees_logistique':")
        for cmd in commandes_manquantes:
            print(f"      - Commande {cmd.id_yz} ({cmd.num_cmd})")
    else:
        print("   ✅ Aucune commande manquante")
    
    # 6. Proposer une correction
    print("\n6. Proposition de correction:")
    print("   Le problème vient probablement du fait que les commandes sont affichées")
    print("   dans le tableau mais ne sont pas correctement filtrées pour l'onglet.")
    print("   Il faut vérifier la logique de filtrage dans la vue liste_prepa.")
    
    print("\n" + "=" * 60)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 60)

if __name__ == "__main__":
    corriger_incoherence_filtrage() 