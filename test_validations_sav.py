#!/usr/bin/env python
"""
Script de test pour vérifier les validations SAV et les calculs.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import Commande, EtatCommande
from parametre.models import Operateur
from django.utils import timezone

def test_validations_sav():
    """
    Test des validations pour le système SAV.
    """
    print("🔍 Test des validations SAV")
    print("=" * 50)
    
    # 1. Tester les commandes livrées partiellement
    print("\n1. Vérification des commandes livrées partiellement:")
    commandes_livrees_partiellement = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée Partiellement',
        etats__date_fin__isnull=True
    ).distinct()
    
    print(f"   - {commandes_livrees_partiellement.count()} commandes livrées partiellement")
    
    for cmd in commandes_livrees_partiellement:
        print(f"   - Commande {cmd.id_yz}: État {cmd.etat_actuel.enum_etat.libelle}")
        
        # Vérifier si elle peut avoir un SAV
        etats_sav_autorises = ['Retournée', 'Livrée', 'Livrée Partiellement', 'Livrée avec changement']
        peut_avoir_sav = cmd.etat_actuel.enum_etat.libelle in etats_sav_autorises
        
        if peut_avoir_sav:
            print(f"     ✅ Peut créer une commande SAV")
        else:
            print(f"     ❌ Ne peut pas créer de commande SAV")
    
    # 2. Tester les commandes retournées
    print("\n2. Vérification des commandes retournées:")
    commandes_retournees = Commande.objects.filter(
        etats__enum_etat__libelle='Retournée',
        etats__date_fin__isnull=True
    ).distinct()
    
    print(f"   - {commandes_retournees.count()} commandes retournées")
    
    for cmd in commandes_retournees:
        print(f"   - Commande {cmd.id_yz}: État {cmd.etat_actuel.enum_etat.libelle}")
        print(f"     ✅ Peut créer une commande SAV")
    
    # 3. Tester les calculs de commandes
    print("\n3. Vérification des calculs de commandes:")
    commandes_test = Commande.objects.filter(
        paniers__isnull=False
    ).distinct()[:5]
    
    for cmd in commandes_test:
        print(f"   - Commande {cmd.id_yz}:")
        
        # Calculer le total des articles
        total_articles = sum(panier.sous_total for panier in cmd.paniers.all())
        frais_livraison = cmd.ville.frais_livraison if cmd.ville else 0
        total_attendu = total_articles + frais_livraison
        
        print(f"     Articles: {total_articles:.2f} DH")
        print(f"     Frais livraison: {frais_livraison:.2f} DH")
        print(f"     Total attendu: {total_attendu:.2f} DH")
        print(f"     Total enregistré: {cmd.total_cmd:.2f} DH")
        
        # Vérifier la cohérence
        if abs(total_attendu - (cmd.total_cmd + frais_livraison)) < 0.01:
            print(f"     ✅ Calculs cohérents")
        else:
            print(f"     ⚠️  Incohérence détectée")
    
    # 4. Tester les opérateurs logistiques
    print("\n4. Vérification des opérateurs logistiques:")
    operateurs_logistique = Operateur.objects.filter(
        type_operateur='LOGISTIQUE',
        actif=True
    )
    
    print(f"   - {operateurs_logistique.count()} opérateurs logistiques actifs")
    
    for op in operateurs_logistique:
        # Compter les commandes en cours
        commandes_en_cours = Commande.objects.filter(
            etats__operateur=op,
            etats__date_fin__isnull=True
        ).distinct().count()
        
        print(f"   - {op.prenom} {op.nom}: {commandes_en_cours} commandes en cours")
    
    # 5. Tester les anomalies SAV
    print("\n5. Détection des anomalies SAV:")
    
    # Commandes avec des états incohérents
    commandes_etat_multiple = Commande.objects.filter(
        etats__date_fin__isnull=True
    ).annotate(
        nb_etats_actifs=django.db.models.Count('etats')
    ).filter(nb_etats_actifs__gt=1)
    
    if commandes_etat_multiple.exists():
        print(f"   ⚠️  {commandes_etat_multiple.count()} commandes avec plusieurs états actifs")
        for cmd in commandes_etat_multiple[:3]:
            etats_actifs = cmd.etats.filter(date_fin__isnull=True)
            print(f"     - Commande {cmd.id_yz}: {etats_actifs.count()} états actifs")
    else:
        print("   ✅ Aucune commande avec plusieurs états actifs")
    
    # Commandes SAV sans commande originale
    from django.db.models import Q
    commandes_sav = Commande.objects.filter(
        Q(num_cmd__startswith='SAV-') | Q(num_cmd__startswith='RENVOI-')
    )
    
    print(f"   - {commandes_sav.count()} commandes SAV/RENVOI trouvées")
    
    commandes_sav_orphelines = []
    for cmd_sav in commandes_sav:
        if cmd_sav.num_cmd.startswith('SAV-'):
            num_original = cmd_sav.num_cmd.replace('SAV-', '')
        else:
            num_original = cmd_sav.num_cmd.replace('RENVOI-', '')
        
        commande_originale = Commande.objects.filter(num_cmd=num_original).first()
        if not commande_originale:
            commandes_sav_orphelines.append(cmd_sav)
    
    if commandes_sav_orphelines:
        print(f"   ⚠️  {len(commandes_sav_orphelines)} commandes SAV/RENVOI orphelines")
        for cmd in commandes_sav_orphelines[:3]:
            print(f"     - {cmd.num_cmd} (ID: {cmd.id_yz})")
    else:
        print("   ✅ Toutes les commandes SAV/RENVOI ont une commande originale")
    
    print("\n" + "=" * 50)
    print("✅ VÉRIFICATION SAV TERMINÉE")
    print("=" * 50)

if __name__ == "__main__":
    test_validations_sav() 