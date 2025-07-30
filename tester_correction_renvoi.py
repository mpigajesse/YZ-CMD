"""
Script pour tester la correction de la logique de filtrage des commandes renvoyées.
"""

import os
import sys
import django
import argparse # Importer argparse

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import Commande, EtatCommande, Operation, EnumEtatCmd
from parametre.models import Operateur
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q

def tester_correction_renvoi(filter_type): # Modifier la signature pour recevoir filter_type
    """
    Teste la correction de la logique de filtrage des commandes renvoyées.
    """
    print("🧪 Test de la correction de la logique de filtrage")
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
    
    # 1. Simulation de la logique de filtrage corrigée:
    print("\n1. Simulation de la logique de filtrage corrigée:")
    
    if filter_type == 'livrees_partiellement':
        commandes_affectees_initial = Commande.objects.filter(
            num_cmd__startswith='RENVOI-',
            etats__enum_etat__libelle='En préparation',
            etats__operateur=operateur_prepa,
            etats__date_fin__isnull=True
        ).exclude(
            etats__enum_etat__libelle__in=['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']
        ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article', 'etats').distinct()
    elif filter_type == 'renvoyees_logistique':
        commandes_affectees_initial = Commande.objects.filter(
            Q(etats__enum_etat__libelle='À imprimer') | Q(etats__enum_etat__libelle='En préparation'),
            etats__operateur=operateur_prepa,
            etats__date_fin__isnull=True
        ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article', 'etats').distinct()
    else: # filter_type == 'all'
        commandes_affectees_initial = Commande.objects.filter(
            Q(etats__enum_etat__libelle='À imprimer') | Q(etats__enum_etat__libelle='En préparation'),
            etats__operateur=operateur_prepa,
            etats__date_fin__isnull=True
        ).exclude(
            etats__enum_etat__libelle__in=['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']
        ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article', 'etats').distinct()

    print(f"   - {commandes_affectees_initial.count()} commandes affectées initialement (avant filtre spécifique)")
    
    commandes_filtrees = []
    
    if filter_type == 'renvoyees_logistique':
        for commande in commandes_affectees_initial:
            etats_commande = commande.etats.all().order_by('date_debut')
            etat_actuel = None
            
            for etat in etats_commande:
                if etat.enum_etat.libelle in ['À imprimer', 'En préparation'] and not etat.date_fin:
                    etat_actuel = etat
                    break
            
            if etat_actuel:
                operation_renvoi = Operation.objects.filter(
                    commande=commande,
                    type_operation='RENVOI_PREPARATION'
                ).first()
                
                if operation_renvoi:
                    commandes_filtrees.append(commande)
                    print(f"   ✅ Commande {commande.id_yz} incluse (opération de renvoi)")
                    continue
                
                # Vérifier si c'est une commande de renvoi créée lors d'une livraison partielle
                if commande.num_cmd and commande.num_cmd.startswith('RENVOI-'):
                    # Chercher la commande originale
                    num_cmd_original = commande.num_cmd.replace('RENVOI-', '')
                    commande_originale = Commande.objects.filter(
                        num_cmd=num_cmd_original,
                        etats__enum_etat__libelle='Livrée Partiellement'
                    ).first()
                    
                    if commande_originale:
                        commandes_filtrees.append(commande)
                        print(f"   ✅ Commande {commande.id_yz} incluse (commande de renvoi livraison partielle)")
                        continue
                
                a_etats_ultérieurs_problematiques = False
                for etat in etats_commande:
                    if (etat.date_debut > etat_actuel.date_debut and 
                        etat.enum_etat.libelle in ['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']):
                        a_etats_ultérieurs_problematiques = True
                        break
                
                if a_etats_ultérieurs_problematiques:
                    print(f"   ❌ Commande {commande.id_yz} ignorée (états ultérieurs problématiques)")
                    continue
                
                for etat in reversed(etats_commande):
                    if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                        if etat.enum_etat.libelle == 'En cours de livraison':
                            commandes_filtrees.append(commande)
                            print(f"   ✅ Commande {commande.id_yz} incluse (état précédent: En cours de livraison)")
                            break
    elif filter_type == 'livrees_partiellement':
        # Utiliser la même logique que la vue corrigée
        commandes_renvoi_livraison_partielle = Commande.objects.filter(
            num_cmd__startswith='RENVOI-',
            etats__enum_etat__libelle='En préparation',
            etats__operateur=operateur_prepa,
            etats__date_fin__isnull=True
        ).distinct()
        
        commandes_filtrees = []
        for commande_renvoi in commandes_renvoi_livraison_partielle:
            # Extraire le numéro de commande original
            num_cmd_original = commande_renvoi.num_cmd.replace('RENVOI-', '')
            
            # Vérifier que la commande originale a été livrée partiellement
            commande_originale = Commande.objects.filter(
                num_cmd=num_cmd_original,
                etats__enum_etat__libelle='Livrée Partiellement'
            ).first()
            
            if commande_originale:
                commandes_filtrees.append(commande_renvoi)
    else: # filter_type == 'all'
        commandes_filtrees = list(commandes_affectees_initial)
    
    print(f"\n2. Résultat du filtrage pour '{filter_type}':")
    print(f"   - {len(commandes_filtrees)} commandes dans '{filter_type}'")
    
    for cmd in commandes_filtrees:
        operation_renvoi = Operation.objects.filter(
            commande=cmd,
            type_operation='RENVOI_PREPARATION'
        ).first()
        
        if operation_renvoi:
            print(f"   📦 Commande {cmd.id_yz} ({cmd.num_cmd}): Opération de renvoi")
        else:
            print(f"   📦 Commande {cmd.id_yz} ({cmd.num_cmd}): État précédent")
    
    # 3. Vérifier spécifiquement la Commande 12 pour 'renvoyees_logistique'
    if filter_type == 'renvoyees_logistique':
        print(f"\n3. Vérification spécifique de la Commande 12:")
        
        commande_12 = Commande.objects.filter(id_yz=12).first()
        if commande_12:
            operation_renvoi_12 = Operation.objects.filter(
                commande=commande_12,
                type_operation='RENVOI_PREPARATION'
            ).first()
            
            if operation_renvoi_12:
                print(f"   ✅ Commande 12 a une opération de renvoi (ID: {operation_renvoi_12.id})")
                
                if commande_12 in commandes_filtrees:
                    print(f"   ✅ Commande 12 est incluse dans 'Renvoyées par logistique'")
                else:
                    print(f"   ❌ Commande 12 n'est PAS incluse (problème persistant)")
            else:
                print(f"   ❌ Commande 12 n'a pas d'opération de renvoi")
        else:
            print(f"   ❌ Commande 12 non trouvée")
    
    # 4. Conclusion
    print(f"\n4. Conclusion:")
    if len(commandes_filtrees) > 0:
        print(f"   ✅ La correction fonctionne ! {len(commandes_filtrees)} commandes identifiées pour '{filter_type}'")
        if filter_type == 'renvoyees_logistique' and commande_12 and commande_12 in commandes_filtrees:
            print(f"   ✅ La Commande 12 est maintenant incluse pour 'Renvoyées par logistique'")
    else:
        print(f"   ❌ Aucune commande identifiée (problème persistant) pour '{filter_type}'")
    
    print("\n" + "=" * 60)
    print("✅ TEST TERMINÉ")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Tester la logique de filtrage des commandes.')
    parser.add_argument('--filter_type', type=str, default='renvoyees_logistique',
                        help='Type de filtre (all, renvoyees_logistique, livrees_partiellement)')
    args = parser.parse_args()
    tester_correction_renvoi(filter_type=args.filter_type) 