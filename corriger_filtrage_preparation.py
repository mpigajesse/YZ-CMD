"""
Script de correction du filtrage dans l'interface de préparation.
Corrige la logique pour exclure les commandes avec des états ultérieurs problématiques.
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

def corriger_filtrage_preparation():
    """
    Corrige la logique de filtrage dans l'interface de préparation.
    """
    print("🔧 Correction du filtrage dans l'interface de préparation")
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
    
    # 1. Identifier les commandes problématiques
    print("\n1. Identification des commandes problématiques:")
    
    commandes_affectees = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct()
    
    commandes_problematiques = []
    
    for cmd in commandes_affectees:
        # Récupérer tous les états de la commande
        etats_commande = cmd.etats.all().order_by('date_debut')
        
        # Trouver l'état actuel
        etat_actuel = None
        for etat in etats_commande:
            if etat.enum_etat.libelle in ['À imprimer', 'En préparation'] and not etat.date_fin:
                etat_actuel = etat
                break
        
        if etat_actuel:
            # Vérifier s'il y a des états ultérieurs problématiques
            for etat in etats_commande:
                if (etat.date_debut > etat_actuel.date_debut and 
                    etat.enum_etat.libelle in ['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']):
                    commandes_problematiques.append({
                        'commande': cmd,
                        'etat_actuel': etat_actuel,
                        'etat_problematique': etat
                    })
                    break
    
    print(f"   - {len(commandes_problematiques)} commandes problématiques identifiées")
    
    for pb in commandes_problematiques:
        cmd = pb['commande']
        etat_actuel = pb['etat_actuel']
        etat_problematique = pb['etat_problematique']
        
        print(f"   ⚠️ Commande {cmd.id_yz} ({cmd.num_cmd}):")
        print(f"      État actuel: {etat_actuel.enum_etat.libelle}")
        print(f"      État problématique: {etat_problematique.enum_etat.libelle} ({etat_problematique.date_debut.strftime('%d/%m/%Y %H:%M')})")
    
    # 2. Corriger les états problématiques
    print("\n2. Correction des états problématiques:")
    
    for pb in commandes_problematiques:
        cmd = pb['commande']
        etat_actuel = pb['etat_actuel']
        etat_problematique = pb['etat_problematique']
        
        # Si l'état problématique est plus récent que l'état actuel, 
        # cela signifie que l'état actuel ne devrait pas être actif
        if etat_problematique.date_debut > etat_actuel.date_debut:
            print(f"   🔧 Correction de la commande {cmd.id_yz}:")
            print(f"      Terminer l'état '{etat_actuel.enum_etat.libelle}' car il y a un état ultérieur '{etat_problematique.enum_etat.libelle}'")
            
            # Terminer l'état actuel problématique
            etat_actuel.date_fin = etat_problematique.date_debut
            etat_actuel.save()
            
            print(f"      ✅ État '{etat_actuel.enum_etat.libelle}' terminé le {etat_actuel.date_fin.strftime('%d/%m/%Y %H:%M')}")
    
    # 3. Vérifier les commandes de renvoi problématiques
    print("\n3. Vérification des commandes de renvoi problématiques:")
    
    commandes_renvoi_problematiques = []
    
    commandes_renvoi = Commande.objects.filter(
        num_cmd__startswith='RENVOI-',
        etats__enum_etat__libelle='En préparation',
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct()
    
    for cmd in commandes_renvoi:
        # Récupérer tous les états de la commande
        etats_commande = cmd.etats.all().order_by('date_debut')
        
        # Trouver l'état actuel
        etat_actuel = None
        for etat in etats_commande:
            if etat.enum_etat.libelle == 'En préparation' and not etat.date_fin:
                etat_actuel = etat
                break
        
        if etat_actuel:
            # Vérifier s'il y a des états ultérieurs problématiques
            for etat in etats_commande:
                if (etat.date_debut > etat_actuel.date_debut and 
                    etat.enum_etat.libelle in ['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']):
                    commandes_renvoi_problematiques.append({
                        'commande': cmd,
                        'etat_actuel': etat_actuel,
                        'etat_problematique': etat
                    })
                    break
    
    print(f"   - {len(commandes_renvoi_problematiques)} commandes de renvoi problématiques identifiées")
    
    for pb in commandes_renvoi_problematiques:
        cmd = pb['commande']
        etat_actuel = pb['etat_actuel']
        etat_problematique = pb['etat_problematique']
        
        print(f"   ⚠️ Commande de renvoi {cmd.id_yz} ({cmd.num_cmd}):")
        print(f"      État actuel: {etat_actuel.enum_etat.libelle}")
        print(f"      État problématique: {etat_problematique.enum_etat.libelle} ({etat_problematique.date_debut.strftime('%d/%m/%Y %H:%M')})")
        
        # Corriger l'état problématique
        if etat_problematique.date_debut > etat_actuel.date_debut:
            print(f"   🔧 Correction de la commande de renvoi {cmd.id_yz}:")
            print(f"      Terminer l'état '{etat_actuel.enum_etat.libelle}' car il y a un état ultérieur '{etat_problematique.enum_etat.libelle}'")
            
            # Terminer l'état actuel problématique
            etat_actuel.date_fin = etat_problematique.date_debut
            etat_actuel.save()
            
            print(f"      ✅ État '{etat_actuel.enum_etat.libelle}' terminé le {etat_actuel.date_fin.strftime('%d/%m/%Y %H:%M')}")
    
    # 4. Vérification finale
    print("\n4. Vérification finale:")
    
    commandes_finales = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct()
    
    print(f"   - {commandes_finales.count()} commandes finales après correction")
    
    # Vérifier qu'il n'y a plus de commandes problématiques
    commandes_encore_problematiques = []
    
    for cmd in commandes_finales:
        etats_commande = cmd.etats.all().order_by('date_debut')
        etat_actuel = None
        
        for etat in etats_commande:
            if etat.enum_etat.libelle in ['À imprimer', 'En préparation'] and not etat.date_fin:
                etat_actuel = etat
                break
        
        if etat_actuel:
            for etat in etats_commande:
                if (etat.date_debut > etat_actuel.date_debut and 
                    etat.enum_etat.libelle in ['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']):
                    commandes_encore_problematiques.append(cmd)
                    break
    
    if commandes_encore_problematiques:
        print(f"   ⚠️ {len(commandes_encore_problematiques)} commandes encore problématiques:")
        for cmd in commandes_encore_problematiques:
            print(f"      - Commande {cmd.id_yz} ({cmd.num_cmd})")
    else:
        print("   ✅ Aucune commande problématique restante")
    
    print("\n" + "=" * 60)
    print("✅ CORRECTION TERMINÉE")
    print("=" * 60)

if __name__ == "__main__":
    corriger_filtrage_preparation() 