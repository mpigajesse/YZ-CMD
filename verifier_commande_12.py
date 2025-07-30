"""
Script pour analyser spécifiquement la Commande 12 et comprendre pourquoi elle n'apparaît pas.
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

def analyser_commande_12():
    """
    Analyse spécifiquement la Commande 12 pour comprendre le problème.
    """
    print("🔍 Analyse spécifique de la Commande 12")
    print("=" * 60)
    
    # Récupérer la Commande 12
    commande_12 = Commande.objects.filter(id_yz=12).first()
    
    if not commande_12:
        print("❌ Commande 12 non trouvée")
        return
    
    print(f"✅ Commande 12 trouvée: {commande_12.num_cmd}")
    
    # Récupérer un opérateur de préparation
    operateur_prepa = Operateur.objects.filter(
        type_operateur='PREPARATION',
        actif=True
    ).first()
    
    if not operateur_prepa:
        print("❌ Aucun opérateur de préparation actif trouvé")
        return
    
    print(f"✅ Opérateur de préparation: {operateur_prepa.prenom} {operateur_prepa.nom}")
    
    # 1. Analyser tous les états de la commande
    print("\n1. Analyse de tous les états de la commande:")
    
    etats_commande = commande_12.etats.all().order_by('date_debut')
    
    for i, etat in enumerate(etats_commande):
        status = "🟢 ACTIF" if not etat.date_fin else "⚫ TERMINÉ"
        print(f"   {i+1}. {etat.enum_etat.libelle} ({etat.date_debut.strftime('%d/%m/%Y %H:%M')}) {status}")
        if etat.date_fin:
            print(f"      Terminé le: {etat.date_fin.strftime('%d/%m/%Y %H:%M')}")
        print(f"      Opérateur: {etat.operateur.prenom} {etat.operateur.nom} ({etat.operateur.type_operateur})")
    
    # 2. Vérifier l'opération de renvoi
    print("\n2. Vérification de l'opération de renvoi:")
    
    operation_renvoi = Operation.objects.filter(
        commande=commande_12,
        type_operation='RENVOI_PREPARATION'
    ).first()
    
    if operation_renvoi:
        print(f"   ✅ Opération de renvoi trouvée:")
        print(f"      ID: {operation_renvoi.id}")
        print(f"      Date: {operation_renvoi.date_operation.strftime('%d/%m/%Y %H:%M')}")
        print(f"      Opérateur: {operation_renvoi.operateur.prenom} {operation_renvoi.operateur.nom}")
    else:
        print("   ❌ Aucune opération de renvoi trouvée")
    
    # 3. Vérifier l'affectation actuelle
    print("\n3. Vérification de l'affectation actuelle:")
    
    etat_actuel = commande_12.etats.filter(
        enum_etat__libelle__in=['À imprimer', 'En préparation'],
        operateur=operateur_prepa,
        date_fin__isnull=True
    ).first()
    
    if etat_actuel:
        print(f"   ✅ État actuel: {etat_actuel.enum_etat.libelle}")
        print(f"      Date début: {etat_actuel.date_debut.strftime('%d/%m/%Y %H:%M')}")
        print(f"      Opérateur: {etat_actuel.operateur.prenom} {etat_actuel.operateur.nom}")
    else:
        print("   ❌ Pas d'état actuel affecté à cet opérateur")
    
    # 4. Vérifier les états ultérieurs problématiques
    print("\n4. Vérification des états ultérieurs problématiques:")
    
    if etat_actuel:
        etats_ultérieurs_problematiques = []
        
        for etat in etats_commande:
            if (etat.date_debut > etat_actuel.date_debut and 
                etat.enum_etat.libelle in ['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']):
                etats_ultérieurs_problematiques.append(etat)
        
        if etats_ultérieurs_problematiques:
            print(f"   ⚠️ {len(etats_ultérieurs_problematiques)} états ultérieurs problématiques trouvés:")
            for etat in etats_ultérieurs_problematiques:
                print(f"      - {etat.enum_etat.libelle} ({etat.date_debut.strftime('%d/%m/%Y %H:%M')})")
            print("   ❌ La commande sera ignorée par le filtre 'renvoyees_logistique'")
        else:
            print("   ✅ Aucun état ultérieur problématique trouvé")
    
    # 5. Simuler la logique de filtrage
    print("\n5. Simulation de la logique de filtrage 'renvoyees_logistique':")
    
    if etat_actuel:
        # Vérifier s'il y a des états ultérieurs problématiques
        a_etats_ultérieurs_problematiques = False
        for etat in etats_commande:
            if (etat.date_debut > etat_actuel.date_debut and 
                etat.enum_etat.libelle in ['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']):
                a_etats_ultérieurs_problematiques = True
                break
        
        if a_etats_ultérieurs_problematiques:
            print("   ❌ La commande sera ignorée (états ultérieurs problématiques)")
        else:
            # Vérifier les opérations de renvoi
            if operation_renvoi:
                print("   ✅ La commande sera incluse (opération de renvoi trouvée)")
            else:
                # Vérifier l'état précédent
                etat_precedent_livraison = None
                for etat in reversed(etats_commande):
                    if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                        if etat.enum_etat.libelle == 'En cours de livraison':
                            etat_precedent_livraison = etat
                            break
                
                if etat_precedent_livraison:
                    print(f"   ✅ La commande sera incluse (état précédent: {etat_precedent_livraison.enum_etat.libelle})")
                else:
                    print("   ❌ La commande ne sera pas incluse (aucun critère rempli)")
    else:
        print("   ❌ La commande ne sera pas incluse (pas d'état actuel)")
    
    # 6. Conclusion et solution
    print("\n6. Conclusion et solution:")
    
    if etat_actuel and operation_renvoi:
        # La commande a une opération de renvoi mais est ignorée à cause des états ultérieurs
        print("   🔧 SOLUTION: Modifier la logique de filtrage pour ignorer les états ultérieurs")
        print("   quand il y a une opération de renvoi explicite.")
        print("   La logique actuelle est trop restrictive.")
    else:
        print("   ❌ La commande ne remplit pas les critères de base.")
    
    print("\n" + "=" * 60)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 60)

if __name__ == "__main__":
    analyser_commande_12() 