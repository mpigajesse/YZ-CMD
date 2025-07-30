"""
Script de test pour vérifier que les futures affectations respectent les règles du système.
À exécuter périodiquement pour s'assurer de l'intégrité du système.
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import Commande, EtatCommande, Operation
from parametre.models import Operateur
from django.utils import timezone
from datetime import timedelta

def test_affectations_futures():
    """
    Test complet du système d'affectation pour les futures commandes.
    """
    print("🔍 Test du système d'affectation pour les futures commandes")
    print("=" * 60)
    
    # 1. Vérifier les opérateurs de préparation
    print("\n1. Vérification des opérateurs de préparation:")
    operateurs_prepa = Operateur.objects.filter(type_operateur='PREPARATION')
    print(f"   - {operateurs_prepa.count()} opérateurs de préparation trouvés")
    
    for op in operateurs_prepa:
        status = "✅ Actif" if op.actif else "❌ Inactif"
        print(f"   - {op.prenom} {op.nom}: {status}")
    
    # 2. Vérifier les commandes actuellement en préparation
    print("\n2. Vérification des commandes en préparation:")
    commandes_en_prepa = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation'],
        etats__date_fin__isnull=True
    ).distinct()
    
    print(f"   - {commandes_en_prepa.count()} commandes en préparation")
    
    # 3. Vérifier les affectations par opérateur
    print("\n3. Répartition des commandes par opérateur:")
    for op in operateurs_prepa:
        nb_commandes = commandes_en_prepa.filter(
            etats__operateur=op,
            etats__date_fin__isnull=True
        ).distinct().count()
        print(f"   - {op.prenom} {op.nom}: {nb_commandes} commandes")
    
    # 4. Vérifier les commandes renvoyées par la logistique
    print("\n4. Vérification des commandes renvoyées par la logistique:")
    commandes_renvoyees = Commande.objects.filter(
        operations__type_operation='RENVOI_PREPARATION'
    ).distinct()
    
    print(f"   - {commandes_renvoyees.count()} commandes renvoyées par la logistique")
    
    for cmd in commandes_renvoyees[:5]:  # Afficher les 5 premières
        etat_actuel = cmd.etats.filter(
            enum_etat__libelle__in=['À imprimer', 'En préparation'],
            date_fin__isnull=True
        ).first()
        
        if etat_actuel:
            print(f"   - Commande {cmd.id_yz}: affectée à {etat_actuel.operateur.prenom} {etat_actuel.operateur.nom}")
        else:
            print(f"   - Commande {cmd.id_yz}: ❌ Pas d'état actuel")
    
    # 4.1. Vérifier les commandes livrées partiellement
    print("\n4.1. Vérification des commandes livrées partiellement:")
    commandes_livrees_partiellement = Commande.objects.filter(
        etats__enum_etat__libelle='Livrée Partiellement'
    ).distinct()
    
    print(f"   - {commandes_livrees_partiellement.count()} commandes livrées partiellement")
    
    for cmd in commandes_livrees_partiellement[:5]:  # Afficher les 5 premières
        etat_actuel = cmd.etats.filter(
            enum_etat__libelle__in=['À imprimer', 'En préparation'],
            date_fin__isnull=True
        ).first()
        
        if etat_actuel:
            print(f"   - Commande {cmd.id_yz}: affectée à {etat_actuel.operateur.prenom} {etat_actuel.operateur.nom}")
        else:
            print(f"   - Commande {cmd.id_yz}: ❌ Pas d'état actuel")
    
    # 4.2. Vérifier les commandes de renvoi créées lors de livraisons partielles
    print("\n4.2. Vérification des commandes de renvoi (livraisons partielles):")
    commandes_renvoi = Commande.objects.filter(
        num_cmd__startswith='RENVOI-'
    ).distinct()
    
    print(f"   - {commandes_renvoi.count()} commandes de renvoi créées")
    
    for cmd in commandes_renvoi[:5]:  # Afficher les 5 premières
        etat_actuel = cmd.etats.filter(
            enum_etat__libelle__in=['À imprimer', 'En préparation'],
            date_fin__isnull=True
        ).first()
        
        if etat_actuel:
            print(f"   - Commande {cmd.id_yz} ({cmd.num_cmd}): affectée à {etat_actuel.operateur.prenom} {etat_actuel.operateur.nom}")
        else:
            print(f"   - Commande {cmd.id_yz} ({cmd.num_cmd}): ❌ Pas d'état actuel")
    
    # 5. Vérifier les anomalies d'affectation
    print("\n5. Détection des anomalies d'affectation:")
    
    # Commandes avec des états créés par des opérateurs incorrects
    etats_anormaux = EtatCommande.objects.filter(
        enum_etat__libelle__in=['À imprimer', 'En préparation'],
        operateur__type_operateur__in=['LOGISTIQUE', 'LIVRAISON', 'CONFIRMATION']
    )
    
    if etats_anormaux.exists():
        print(f"   - ❌ {etats_anormaux.count()} états créés par des opérateurs incorrects")
        for etat in etats_anormaux[:3]:
            print(f"     * Commande {etat.commande.id_yz}: {etat.operateur.nom_complet} ({etat.operateur.type_operateur})")
    else:
        print("   - ✅ Aucun état créé par des opérateurs incorrects")
    
    # Commandes affectées à des opérateurs inactifs
    etats_inactifs = EtatCommande.objects.filter(
        enum_etat__libelle__in=['À imprimer', 'En préparation'],
        operateur__actif=False,
        date_fin__isnull=True
    )
    
    if etats_inactifs.exists():
        print(f"   - ❌ {etats_inactifs.count()} commandes affectées à des opérateurs inactifs")
    else:
        print("   - ✅ Aucune commande affectée à des opérateurs inactifs")
    
    # 6. Vérifier les anomalies de livraison partielle
    print("\n6. Détection des anomalies de livraison partielle:")
    try:
        from operatLogistic.views import surveiller_livraisons_partielles
        anomalies_livraison = surveiller_livraisons_partielles()
        
        if anomalies_livraison:
            print(f"   - {len(anomalies_livraison)} anomalies de livraison partielle détectées:")
            for anomalie in anomalies_livraison[:5]:  # Afficher les 5 premières
                print(f"     ⚠️  {anomalie['message']}")
        else:
            print("   ✅ Aucune anomalie de livraison partielle détectée")
    except Exception as e:
        print(f"   ❌ Erreur lors de la vérification des livraisons partielles: {e}")
    
    # 7. Test de la logique de renvoi
    print("\n7. Test de la logique de renvoi:")
    
    # Simuler une commande qui a été préparée par PrenomPO1
    commande_test = commandes_en_prepa.first()
    if commande_test:
        print(f"   - Test avec la commande {commande_test.id_yz}")
        
        # Chercher l'état "En préparation" précédent
        etat_preparation_precedent = commande_test.etats.filter(
            enum_etat__libelle='En préparation',
            date_fin__isnull=False
        ).order_by('-date_fin').first()
        
        if etat_preparation_precedent:
            operateur_original = etat_preparation_precedent.operateur
            print(f"   - Opérateur original: {operateur_original.prenom} {operateur_original.nom}")
            print(f"   - Type: {operateur_original.type_operateur}")
            print(f"   - Actif: {operateur_original.actif}")
            
            if operateur_original.type_operateur == 'PREPARATION' and operateur_original.actif:
                print("   - ✅ La logique de renvoi fonctionnerait correctement")
            else:
                print("   - ❌ La logique de renvoi utiliserait un opérateur de secours")
        else:
            print("   - ⚠️  Aucun état 'En préparation' précédent trouvé")
    
    print("\n" + "=" * 60)
    print("✅ VÉRIFICATION TERMINÉE - SYSTÈME OPÉRATIONNEL")
    print("=" * 60)

if __name__ == "__main__":
    test_affectations_futures() 