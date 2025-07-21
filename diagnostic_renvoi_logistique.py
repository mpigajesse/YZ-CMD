"""
Script de diagnostic spécifique pour les commandes renvoyées par la logistique.
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

def diagnostic_renvoi_logistique():
    """
    Diagnostic spécifique pour les commandes renvoyées par la logistique.
    """
    print("🔍 Diagnostic des commandes renvoyées par la logistique")
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
    
    # 1. Récupérer toutes les commandes affectées à cet opérateur
    print("\n1. Commandes affectées à l'opérateur:")
    
    commandes_affectees = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).exclude(
        etats__enum_etat__libelle__in=['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct()
    
    print(f"   - {commandes_affectees.count()} commandes affectées")
    
    # 2. Analyser chaque commande pour voir si elle devrait être dans "renvoyees_logistique"
    print("\n2. Analyse des commandes pour l'onglet 'Renvoyées par logistique':")
    
    commandes_renvoyees_logistique = []
    
    for cmd in commandes_affectees:
        print(f"\n   📦 Commande {cmd.id_yz} ({cmd.num_cmd}):")
        
        # Récupérer tous les états de la commande
        etats_commande = cmd.etats.all().order_by('date_debut')
        
        # Trouver l'état actuel
        etat_actuel = None
        for etat in etats_commande:
            if etat.enum_etat.libelle in ['À imprimer', 'En préparation'] and not etat.date_fin:
                etat_actuel = etat
                break
        
        if etat_actuel:
            print(f"      État actuel: {etat_actuel.enum_etat.libelle} ({etat_actuel.date_debut.strftime('%d/%m/%Y %H:%M')})")
            
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
    
    print(f"\n3. Résumé:")
    print(f"   - Commandes identifiées comme 'renvoyées par logistique': {len(commandes_renvoyees_logistique)}")
    
    # 4. Tester la logique de filtrage actuelle
    print("\n4. Test de la logique de filtrage actuelle:")
    
    commandes_filtrees = []
    for commande in commandes_affectees:
        from commande.models import Operation
        
        # Vérifier que la commande n'a pas d'états ultérieurs problématiques
        etats_commande = commande.etats.all().order_by('date_debut')
        etat_actuel = None
        
        # Trouver l'état actuel (En préparation)
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
            
            if a_etats_ultérieurs_problematiques:
                print(f"   ❌ Commande {commande.id_yz}: Ignorée (états ultérieurs problématiques)")
                continue
            
            # Vérifier les opérations de traçabilité
            operation_renvoi = Operation.objects.filter(
                commande=commande,
                type_operation='RENVOI_PREPARATION'
            ).first()
            
            if operation_renvoi:
                print(f"   ✅ Commande {commande.id_yz}: Ajoutée (opération de renvoi)")
                commandes_filtrees.append(commande)
                continue
            
            # Vérifier l'historique des états de la commande
            # Trouver l'état précédent
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                    if etat.enum_etat.libelle == 'En cours de livraison':
                        print(f"   ✅ Commande {commande.id_yz}: Ajoutée (état précédent: En cours de livraison)")
                        commandes_filtrees.append(commande)
                        break
                    else:
                        print(f"   ❌ Commande {commande.id_yz}: Ignorée (état précédent: {etat.enum_etat.libelle})")
                        break
    
    print(f"\n5. Résultat du filtrage:")
    print(f"   - Commandes après filtrage: {len(commandes_filtrees)}")
    
    # 6. Comparaison
    print(f"\n6. Comparaison:")
    print(f"   - Commandes identifiées manuellement: {len(commandes_renvoyees_logistique)}")
    print(f"   - Commandes après filtrage automatique: {len(commandes_filtrees)}")
    
    if len(commandes_renvoyees_logistique) != len(commandes_filtrees):
        print(f"   ⚠️ Différence détectée !")
        
        # Identifier les commandes manquantes
        commandes_manquantes = []
        for cmd in commandes_renvoyees_logistique:
            if cmd not in commandes_filtrees:
                commandes_manquantes.append(cmd)
        
        if commandes_manquantes:
            print(f"   - Commandes manquantes dans le filtrage:")
            for cmd in commandes_manquantes:
                print(f"     * Commande {cmd.id_yz} ({cmd.num_cmd})")
    
    print("\n" + "=" * 60)
    print("✅ DIAGNOSTIC TERMINÉ")
    print("=" * 60)

if __name__ == "__main__":
    diagnostic_renvoi_logistique() 