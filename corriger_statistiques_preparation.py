"""
Script de correction des statistiques et du filtrage dans l'interface de préparation.
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

def corriger_statistiques_preparation():
    """
    Corrige la logique de calcul des statistiques et du filtrage.
    """
    print("🔧 Correction des statistiques et du filtrage")
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
    
    # 1. Analyser toutes les commandes affectées
    print("\n1. Analyse de toutes les commandes affectées:")
    
    commandes_affectees = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).exclude(
        etats__enum_etat__libelle__in=['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct()
    
    print(f"   - {commandes_affectees.count()} commandes affectées")
    
    # 2. Catégoriser les commandes
    print("\n2. Catégorisation des commandes:")
    
    commandes_renvoyees_logistique = []
    commandes_livrees_partiellement = []
    commandes_normales = []
    
    for cmd in commandes_affectees:
        print(f"\n   📦 Commande {cmd.id_yz} ({cmd.num_cmd}):")
        
        # Vérifier si c'est une commande de renvoi (livraison partielle)
        if cmd.num_cmd and cmd.num_cmd.startswith('RENVOI-'):
            print(f"      🔄 Commande de renvoi détectée (livraison partielle)")
            commandes_livrees_partiellement.append(cmd)
            continue
        
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
                elif etat_precedent.enum_etat.libelle == 'Livrée Partiellement':
                    print(f"      ⚠️ Commande livrée partiellement")
                    commandes_livrees_partiellement.append(cmd)
                else:
                    print(f"      📋 Commande normale")
                    commandes_normales.append(cmd)
            else:
                print(f"      ❓ Aucun état précédent trouvé")
                commandes_normales.append(cmd)
    
    # 3. Résumé des catégories
    print(f"\n3. Résumé des catégories:")
    print(f"   - Commandes renvoyées par logistique: {len(commandes_renvoyees_logistique)}")
    print(f"   - Commandes livrées partiellement: {len(commandes_livrees_partiellement)}")
    print(f"   - Commandes normales: {len(commandes_normales)}")
    
    # 4. Afficher les commandes par catégorie
    print(f"\n4. Détail par catégorie:")
    
    print(f"\n   🚛 Commandes renvoyées par logistique ({len(commandes_renvoyees_logistique)}):")
    for cmd in commandes_renvoyees_logistique:
        print(f"      - Commande {cmd.id_yz} ({cmd.num_cmd})")
    
    print(f"\n   ⚠️ Commandes livrées partiellement ({len(commandes_livrees_partiellement)}):")
    for cmd in commandes_livrees_partiellement:
        print(f"      - Commande {cmd.id_yz} ({cmd.num_cmd})")
    
    print(f"\n   📋 Commandes normales ({len(commandes_normales)}):")
    for cmd in commandes_normales:
        print(f"      - Commande {cmd.id_yz} ({cmd.num_cmd})")
    
    # 5. Vérifier les statistiques actuelles
    print(f"\n5. Vérification des statistiques actuelles:")
    
    # Calculer les statistiques comme dans la vue
    stats_par_type = {
        'renvoyees_logistique': 0,
        'livrees_partiellement': 0
    }
    
    # Recalculer les statistiques pour tous les types
    toutes_commandes = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).exclude(
        etats__enum_etat__libelle__in=['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct()
    
    for cmd in toutes_commandes:
        # Vérifier si c'est une commande renvoyée par la logistique
        operation_renvoi = Operation.objects.filter(
            commande=cmd,
            type_operation='RENVOI_PREPARATION'
        ).first()
        
        if operation_renvoi:
            stats_par_type['renvoyees_logistique'] += 1
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
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                    if etat.enum_etat.libelle == 'En cours de livraison':
                        stats_par_type['renvoyees_logistique'] += 1
                        break
                    elif etat.enum_etat.libelle == 'Livrée Partiellement':
                        stats_par_type['livrees_partiellement'] += 1
                        break
    
    # Calculer le nombre de commandes de renvoi
    commandes_renvoi_count = Commande.objects.filter(
        num_cmd__startswith='RENVOI-',
        etats__enum_etat__libelle='En préparation',
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).exclude(
        etats__enum_etat__libelle__in=['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']
    ).distinct().count()
    
    # Mettre à jour le compteur
    stats_par_type['livrees_partiellement'] = commandes_renvoi_count
    
    print(f"   - Statistiques calculées par la vue:")
    print(f"     * Renvoyées par logistique: {stats_par_type['renvoyees_logistique']}")
    print(f"     * Livrées partiellement: {stats_par_type['livrees_partiellement']}")
    
    print(f"\n   - Statistiques calculées manuellement:")
    print(f"     * Renvoyées par logistique: {len(commandes_renvoyees_logistique)}")
    print(f"     * Livrées partiellement: {len(commandes_livrees_partiellement)}")
    
    # 6. Identifier les problèmes
    print(f"\n6. Identification des problèmes:")
    
    if stats_par_type['renvoyees_logistique'] != len(commandes_renvoyees_logistique):
        print(f"   ⚠️ Différence dans 'renvoyees_logistique':")
        print(f"      Vue: {stats_par_type['renvoyees_logistique']}")
        print(f"      Manuel: {len(commandes_renvoyees_logistique)}")
    
    if stats_par_type['livrees_partiellement'] != len(commandes_livrees_partiellement):
        print(f"   ⚠️ Différence dans 'livrees_partiellement':")
        print(f"      Vue: {stats_par_type['livrees_partiellement']}")
        print(f"      Manuel: {len(commandes_livrees_partiellement)}")
    
    print("\n" + "=" * 60)
    print("✅ ANALYSE TERMINÉE")
    print("=" * 60)

if __name__ == "__main__":
    corriger_statistiques_preparation() 