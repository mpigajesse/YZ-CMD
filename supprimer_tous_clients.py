#!/usr/bin/env python3
"""
Script pour supprimer tous les clients et leurs commandes associées
Projet YZ-CMD
"""

import os
import sys
import django
from django.db import transaction
from pathlib import Path

def setup_django():
    """Configure Django pour utiliser les modèles"""
    # Ajouter le répertoire du projet au path
    project_path = Path(__file__).resolve().parent
    sys.path.append(str(project_path))
    
    # Configuration Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

def supprimer_tous_clients():
    """Supprime tous les clients et leurs données associées"""
    from client.models import Client
    from commande.models import Commande, Panier
    
    print("🗑️  Script de suppression des clients et commandes")
    print("=" * 60)
    
    try:
        # Statistiques avant suppression
        total_clients = Client.objects.count()
        total_commandes = Commande.objects.count()
        total_paniers = Panier.objects.count()
        
        print(f"📊 Statistiques actuelles :")
        print(f"   - Clients : {total_clients}")
        print(f"   - Commandes : {total_commandes}")
        print(f"   - Paniers : {total_paniers}")
        print()
        
        if total_clients == 0:
            print("✅ Aucun client à supprimer.")
            return
        
        # Demander confirmation
        print("⚠️  ATTENTION : Cette action va supprimer DÉFINITIVEMENT :")
        print(f"   - Tous les {total_clients} clients")
        print(f"   - Toutes les {total_commandes} commandes associées") 
        print(f"   - Tous les {total_paniers} paniers associés")
        print()
        
        confirmation = input("Tapez 'SUPPRIMER' pour confirmer cette action : ")
        
        if confirmation != 'SUPPRIMER':
            print("❌ Suppression annulée.")
            return
        
        print("\n🔄 Suppression en cours...")
        
        # Utiliser une transaction pour assurer la cohérence
        with transaction.atomic():
            # Supprimer tous les clients (les commandes et paniers seront supprimés automatiquement par CASCADE)
            clients_supprimes, details = Client.objects.all().delete()
            
            print("✅ Suppression terminée avec succès !")
            print(f"📋 Détails de la suppression :")
            
            for model, count in details.items():
                if count > 0:
                    print(f"   - {model}: {count} éléments supprimés")
        
        # Vérification finale
        clients_restants = Client.objects.count()
        commandes_restantes = Commande.objects.count()
        paniers_restants = Panier.objects.count()
        
        print(f"\n📊 Statistiques après suppression :")
        print(f"   - Clients restants : {clients_restants}")
        print(f"   - Commandes restantes : {commandes_restantes}")
        print(f"   - Paniers restants : {paniers_restants}")
        
        if clients_restants == 0 and commandes_restantes == 0:
            print("\n🎉 Toutes les données ont été supprimées avec succès !")
        else:
            print("\n⚠️  Il reste encore des données. Vérifiez les contraintes de base de données.")
            
    except Exception as e:
        print(f"❌ Erreur lors de la suppression : {e}")
        print("🔄 Aucune donnée n'a été supprimée (transaction annulée).")

def afficher_aide():
    """Affiche l'aide du script"""
    print("""
🔧 Script de suppression des clients - YZ-CMD

Usage:
    python supprimer_tous_clients.py

⚠️  ATTENTION :
- Ce script supprime TOUS les clients de la base de données
- Toutes les commandes associées seront également supprimées
- Cette action est IRRÉVERSIBLE
- Assurez-vous d'avoir une sauvegarde avant d'exécuter ce script

🛡️  Sécurité :
- Le script demande une confirmation explicite
- Utilise des transactions pour maintenir la cohérence des données
- Affiche des statistiques avant et après la suppression

📝 Modèles affectés :
- Client : Tous les clients
- Commande : Toutes les commandes liées aux clients
- Panier : Tous les paniers liés aux commandes
- EtatCommande : Tous les états liés aux commandes
- Operation : Toutes les opérations liées aux commandes
""")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        afficher_aide()
        sys.exit(0)
    
    try:
        setup_django()
        supprimer_tous_clients()
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation : {e}")
        print("💡 Assurez-vous que :")
        print("   1. Vous êtes dans le répertoire racine du projet")
        print("   2. L'environnement virtuel est activé")
        print("   3. Les variables d'environnement sont configurées")
        sys.exit(1) 