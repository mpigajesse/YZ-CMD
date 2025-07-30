#!/usr/bin/env python
"""
Script de test pour vérifier l'affichage des états de confirmation
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db.models import Q
from commande.models import Commande, EtatCommande
from parametre.models import Operateur

def tester_etats_confirmation():
    """Test de l'affichage des états de confirmation"""
    print("=" * 80)
    print("TEST DES ÉTATS DE CONFIRMATION")
    print("=" * 80)
    
    # Simuler un opérateur de préparation
    try:
        operateur = Operateur.objects.filter(type_operateur='PREPARATION').first()
        if not operateur:
            print("❌ Aucun opérateur de préparation trouvé")
            return
        print(f"✅ Opérateur de préparation trouvé : {operateur.user.username}")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération de l'opérateur : {e}")
        return
    
    # Récupérer les commandes affectées à cet opérateur
    commandes_affectees = Commande.objects.filter(
        Q(etats__enum_etat__libelle='À imprimer') | Q(etats__enum_etat__libelle='En préparation'),
        etats__operateur=operateur,
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('paniers__article', 'etats').distinct()
    
    print(f"\n📊 Commandes affectées trouvées : {commandes_affectees.count()}")
    
    # Analyser chaque commande
    for commande in commandes_affectees[:5]:  # Limiter aux 5 premières
        print(f"\n🔍 Commande {commande.id_yz} ({commande.num_cmd})")
        print("-" * 50)
        
        # Récupérer tous les états de la commande dans l'ordre chronologique
        etats_commande = commande.etats.all().order_by('date_debut')
        
        print("📋 Historique des états :")
        for etat in etats_commande:
            status = "🟢 ACTIF" if not etat.date_fin else "🔴 TERMINÉ"
            print(f"   {etat.date_debut.strftime('%d/%m/%Y %H:%i')} - {etat.enum_etat.libelle} - {status}")
            if etat.date_fin:
                print(f"      Terminé le : {etat.date_fin.strftime('%d/%m/%Y %H:%i')}")
        
        # Trouver l'état actuel
        etat_actuel = None
        for etat in etats_commande:
            if etat.enum_etat.libelle in ['À imprimer', 'En préparation'] and not etat.date_fin:
                etat_actuel = etat
                break
        
        if etat_actuel:
            print(f"\n✅ État actuel : {etat_actuel.enum_etat.libelle}")
            
            # Trouver l'état précédent
            etat_precedent = None
            for etat in reversed(etats_commande):
                if etat.date_fin and etat.date_fin < etat_actuel.date_debut:
                    if etat.enum_etat.libelle not in ['À imprimer', 'En préparation']:
                        etat_precedent = etat
                        break
            
            if etat_precedent:
                print(f"📤 État précédent : {etat_precedent.enum_etat.libelle} (terminé le {etat_precedent.date_fin.strftime('%d/%m/%Y %H:%i')})")
            else:
                print("📤 État précédent : Aucun")
            
            # Trouver l'état de confirmation
            etat_confirmation = None
            for etat in etats_commande:
                if etat.enum_etat.libelle == 'Confirmée':
                    etat_confirmation = etat
                    break
            
            if etat_confirmation:
                print(f"👤 État de confirmation : Confirmée (le {etat_confirmation.date_debut.strftime('%d/%m/%Y %H:%i')})")
            else:
                print("👤 État de confirmation : Aucun")
            
            # Simuler l'affichage dans le template
            print(f"\n🎨 Affichage dans le template :")
            if etat_precedent:
                if etat_precedent.enum_etat.libelle == 'En cours de livraison':
                    print("   🔴 Renvoyée depuis livraison")
                elif etat_precedent.enum_etat.libelle == 'Préparée':
                    print("   🟡 Renvoyée depuis préparation")
                elif etat_precedent.enum_etat.libelle == 'Confirmée':
                    print("   🟢 Depuis confirmation")
                else:
                    print(f"   ⚪ {etat_precedent.enum_etat.libelle}")
            else:
                if etat_actuel.enum_etat.libelle == 'À imprimer':
                    print("   🟠 À imprimer")
                elif etat_actuel.enum_etat.libelle == 'En préparation':
                    print("   🔵 En préparation")
                elif etat_actuel.enum_etat.libelle == 'Préparée':
                    print("   🟢 Préparée")
                else:
                    print(f"   ⚪ {etat_actuel.enum_etat.libelle}")
            
            # Afficher l'état de confirmation en plus
            if etat_confirmation:
                print("   🟣 Confirmée par admin")
        else:
            print("❌ Aucun état actuel trouvé")
    
    print("\n" + "=" * 80)
    print("TEST TERMINÉ")
    print("=" * 80)

if __name__ == "__main__":
    try:
        tester_etats_confirmation()
    except Exception as e:
        print(f"Erreur lors du test : {e}")
        import traceback
        traceback.print_exc() 