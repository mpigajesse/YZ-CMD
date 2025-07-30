"""
Script pour comprendre pourquoi la Commande 12 est exclue par le filtre exclude.
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

def debug_commande_12_exclusion():
    """
    Débogue pourquoi la Commande 12 est exclue par le filtre exclude.
    """
    print("🔍 Débogage de l'exclusion de la Commande 12")
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
    
    # Récupérer la Commande 12
    commande_12 = Commande.objects.filter(id_yz=12).first()
    
    if not commande_12:
        print("❌ Commande 12 non trouvée")
        return
    
    print(f"✅ Commande 12 trouvée: {commande_12.num_cmd}")
    
    # 1. Vérifier le filtre de base (sans exclude)
    print("\n1. Test du filtre de base (sans exclude):")
    
    commandes_base = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct()
    
    print(f"   - {commandes_base.count()} commandes avec le filtre de base")
    
    if commande_12 in commandes_base:
        print(f"   ✅ Commande 12 est dans le filtre de base")
    else:
        print(f"   ❌ Commande 12 n'est PAS dans le filtre de base")
    
    # 2. Vérifier l'état actuel de la Commande 12
    print("\n2. Vérification de l'état actuel de la Commande 12:")
    
    etat_actuel_12 = commande_12.etats.filter(
        enum_etat__libelle__in=['À imprimer', 'En préparation'],
        operateur=operateur_prepa,
        date_fin__isnull=True
    ).first()
    
    if etat_actuel_12:
        print(f"   ✅ État actuel: {etat_actuel_12.enum_etat.libelle}")
        print(f"      Date début: {etat_actuel_12.date_debut.strftime('%d/%m/%Y %H:%M')}")
        print(f"      Opérateur: {etat_actuel_12.operateur.prenom} {etat_actuel_12.operateur.nom}")
    else:
        print(f"   ❌ Pas d'état actuel trouvé")
    
    # 3. Vérifier les états problématiques de la Commande 12
    print("\n3. Vérification des états problématiques de la Commande 12:")
    
    etats_problematiques = commande_12.etats.filter(
        enum_etat__libelle__in=['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison'],
        date_fin__isnull=True  # États actifs
    )
    
    print(f"   - {etats_problematiques.count()} états problématiques actifs")
    
    for etat in etats_problematiques:
        print(f"   ⚠️ État problématique: {etat.enum_etat.libelle} ({etat.date_debut.strftime('%d/%m/%Y %H:%M')})")
        print(f"      Opérateur: {etat.operateur.prenom} {etat.operateur.nom}")
    
    # 4. Tester le filtre avec exclude
    print("\n4. Test du filtre avec exclude:")
    
    commandes_avec_exclude = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__operateur=operateur_prepa,
        etats__date_fin__isnull=True
    ).exclude(
        etats__enum_etat__libelle__in=['Livrée', 'Livrée Partiellement', 'Préparée', 'En cours de livraison']
    ).select_related('client', 'ville', 'ville__region').prefetch_related('etats').distinct()
    
    print(f"   - {commandes_avec_exclude.count()} commandes avec le filtre exclude")
    
    if commande_12 in commandes_avec_exclude:
        print(f"   ✅ Commande 12 est dans le filtre avec exclude")
    else:
        print(f"   ❌ Commande 12 n'est PAS dans le filtre avec exclude")
        print(f"   🔍 La Commande 12 est exclue par le filtre exclude")
    
    # 5. Analyser pourquoi l'exclude fonctionne
    print("\n5. Analyse de l'exclusion:")
    
    if etats_problematiques.exists():
        print(f"   La Commande 12 a des états problématiques actifs:")
        for etat in etats_problematiques:
            print(f"      - {etat.enum_etat.libelle} (actif depuis {etat.date_debut.strftime('%d/%m/%Y %H:%M')})")
        print(f"   Le filtre exclude les retire car ils sont actifs.")
    else:
        print(f"   Aucun état problématique actif trouvé.")
    
    # 6. Solution
    print("\n6. Solution:")
    print(f"   Le problème est que la Commande 12 a un état 'Préparée' actif.")
    print(f"   Le filtre exclude retire toutes les commandes qui ont des états problématiques actifs.")
    print(f"   Pour les commandes avec opération de renvoi, on devrait ignorer cette exclusion.")
    
    print("\n" + "=" * 60)
    print("✅ DÉBOGAGE TERMINÉ")
    print("=" * 60)

if __name__ == "__main__":
    debug_commande_12_exclusion() 