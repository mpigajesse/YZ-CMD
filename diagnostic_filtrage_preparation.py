"""
Script de diagnostic pour analyser le problème de filtrage dans l'interface de préparation.
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
from django.db.models import F

def diagnostic_filtrage_preparation():
    """
    Diagnostic du problème de filtrage dans l'interface de préparation.
    """
    print("🔍 Diagnostic du filtrage dans l'interface de préparation")
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
    
    # 1. Analyser toutes les commandes affectées à cet opérateur
    print("\n1. Analyse de toutes les commandes affectées:")
    
    commandes_affectees = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct()
    
    print(f"   - {commandes_affectees.count()} commandes affectées à {operateur_prepa.prenom}")
    
    # 2. Analyser chaque commande en détail
    print("\n2. Analyse détaillée de chaque commande:")
    
    commandes_renvoyees_logistique = []
    commandes_livrees_partiellement = []
    commandes_autres = []
    
    for cmd in commandes_affectees:
        print(f"\n   📦 Commande {cmd.id_yz} ({cmd.num_cmd}):")
        
        # Récupérer tous les états de la commande
        etats_commande = cmd.etats.all().order_by('date_debut')
        
        print(f"      États de la commande:")
        for etat in etats_commande:
            status = "🟢 ACTIF" if not etat.date_fin else "⚫ TERMINÉ"
            print(f"        - {etat.enum_etat.libelle} ({etat.date_debut.strftime('%d/%m/%Y %H:%M')}) {status}")
            if etat.date_fin:
                print(f"          Terminé le: {etat.date_fin.strftime('%d/%m/%Y %H:%M')}")
        
        # Trouver l'état actuel
        etat_actuel = None
        for etat in etats_commande:
            if etat.enum_etat.libelle in ['À imprimer', 'En préparation'] and not etat.date_fin:
                etat_actuel = etat
                break
        
        if etat_actuel:
            print(f"      État actuel: {etat_actuel.enum_etat.libelle}")
            
            # Vérifier les opérations de renvoi
            operation_renvoi = Operation.objects.filter(
                commande=cmd,
                type_operation='RENVOI_PREPARATION'
            ).first()
            
            if operation_renvoi:
                print(f"      🔄 Opération de renvoi trouvée: {operation_renvoi.date_operation.strftime('%d/%m/%Y %H:%M')}")
                commandes_renvoyees_logistique.append(cmd)
                continue
            
            # Vérifier l'état précédent
            etat_precedent = None
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                    if etat.enum_etat.libelle not in ['À imprimer', 'En préparation']:
                        etat_precedent = etat
                        break
            
            if etat_precedent:
                print(f"      ⬅️ État précédent: {etat_precedent.enum_etat.libelle}")
                
                if etat_precedent.enum_etat.libelle == 'En cours de livraison':
                    print(f"      🚛 Commande renvoyée depuis la logistique")
                    commandes_renvoyees_logistique.append(cmd)
                elif etat_precedent.enum_etat.libelle == 'Livrée Partiellement':
                    print(f"      ⚠️ Commande livrée partiellement")
                    commandes_livrees_partiellement.append(cmd)
                else:
                    print(f"      📋 Commande normale")
                    commandes_autres.append(cmd)
            else:
                print(f"      ❓ Aucun état précédent trouvé")
                commandes_autres.append(cmd)
        
        # Vérifier si c'est une commande de renvoi (livraison partielle)
        if cmd.num_cmd and cmd.num_cmd.startswith('RENVOI-'):
            print(f"      🔄 Commande de renvoi détectée (livraison partielle)")
            commandes_livrees_partiellement.append(cmd)
    
    # 3. Résumé des catégories
    print("\n3. Résumé des catégories:")
    print(f"   - Commandes renvoyées par logistique: {len(commandes_renvoyees_logistique)}")
    print(f"   - Commandes livrées partiellement: {len(commandes_livrees_partiellement)}")
    print(f"   - Autres commandes: {len(commandes_autres)}")
    
    # 4. Vérifier les commandes problématiques
    print("\n4. Vérification des commandes problématiques:")
    
    for cmd in commandes_renvoyees_logistique:
        # Vérifier si la commande a des états ultérieurs problématiques
        etats_ultérieurs = cmd.etats.filter(
            date_debut__gt=etat_actuel.date_debut,
            enum_etat__libelle__in=['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']
        ).order_by('date_debut')
        
        if etats_ultérieurs.exists():
            print(f"   ⚠️ Commande {cmd.id_yz} ({cmd.num_cmd}):")
            print(f"      État actuel: {etat_actuel.enum_etat.libelle}")
            print(f"      États ultérieurs problématiques:")
            for etat in etats_ultérieurs:
                print(f"        - {etat.enum_etat.libelle} ({etat.date_debut.strftime('%d/%m/%Y %H:%M')})")
    
    # 5. Proposer une correction
    print("\n5. Proposition de correction:")
    print("   Le problème vient du fait que le filtre ne vérifie que l'état actuel")
    print("   mais ne vérifie pas si la commande a des états ultérieurs.")
    print("   Il faut exclure les commandes qui ont des états ultérieurs problématiques.")
    
    # 6. Test de la correction
    print("\n6. Test de la correction:")
    
    # Récupérer les commandes avec le filtre corrigé
    commandes_corrigees = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).exclude(
        # Exclure les commandes qui ont des états ultérieurs problématiques
        etats__enum_etat__libelle__in=['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison'],
        etats__date_debut__gt=F('etats__date_debut')
    ).distinct()
    
    print(f"   - Commandes après correction: {commandes_corrigees.count()}")
    
    print("\n" + "=" * 60)
    print("✅ DIAGNOSTIC TERMINÉ")
    print("=" * 60)

if __name__ == "__main__":
    diagnostic_filtrage_preparation() 