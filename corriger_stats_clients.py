#!/usr/bin/env python
"""
Script pour corriger automatiquement les problèmes de statistiques des clients
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from client.models import Client
from commande.models import Commande
from django.db.models import Count, Q
from django.db import transaction

def corriger_doublons_clients():
    """Corrige les doublons de clients basés sur le numéro de téléphone"""
    print("🔧 CORRECTION DES DOUBLONS DE CLIENTS")
    print("=" * 50)
    
    # Trouver les numéros de téléphone en double
    doublons_tel = Client.objects.values('numero_tel').annotate(
        count=Count('id')
    ).filter(count__gt=1).order_by('-count')
    
    if not doublons_tel:
        print("✅ Aucun doublon détecté")
        return 0
    
    clients_fusionnes = 0
    
    for doublon in doublons_tel:
        numero_tel = doublon['numero_tel']
        clients_dupliques = Client.objects.filter(numero_tel=numero_tel).order_by('date_creation')
        
        if clients_dupliques.count() > 1:
            print(f"\n📞 Traitement du numéro: {numero_tel}")
            
            # Garder le premier client (le plus ancien)
            client_principal = clients_dupliques.first()
            clients_a_fusionner = clients_dupliques.exclude(id=client_principal.id)
            
            print(f"   • Client principal: {client_principal.get_full_name()} (ID: {client_principal.id})")
            
            with transaction.atomic():
                # Transférer toutes les commandes vers le client principal
                for client_dup in clients_a_fusionner:
                    print(f"   • Fusion avec: {client_dup.get_full_name()} (ID: {client_dup.id})")
                    
                    # Transférer les commandes
                    commandes_transferees = client_dup.commandes.count()
                    if commandes_transferees > 0:
                        client_dup.commandes.update(client=client_principal)
                        print(f"     → {commandes_transferees} commandes transférées")
                    
                    # Mettre à jour les informations du client principal si nécessaire
                    if not client_principal.email and client_dup.email:
                        client_principal.email = client_dup.email
                    if not client_principal.adresse and client_dup.adresse:
                        client_principal.adresse = client_dup.adresse
                    if not client_principal.nom and client_dup.nom:
                        client_principal.nom = client_dup.nom
                    if not client_principal.prenom and client_dup.prenom:
                        client_principal.prenom = client_dup.prenom
                    
                    # Supprimer le client en double
                    client_dup.delete()
                    clients_fusionnes += 1
                
                # Sauvegarder les modifications du client principal
                client_principal.save()
                print(f"   ✅ Fusion terminée pour {numero_tel}")
    
    print(f"\n✅ Correction terminée: {clients_fusionnes} clients fusionnés")
    return clients_fusionnes

def nettoyer_clients_orphelins():
    """Supprime les clients sans commandes et sans informations complètes"""
    print("\n🧹 NETTOYAGE DES CLIENTS ORPHELINS")
    print("=" * 40)
    
    # Clients sans commandes ET sans informations complètes
    clients_orphelins = Client.objects.filter(
        commandes__isnull=True
    ).filter(
        Q(nom__isnull=True) | Q(nom__exact='') |
        Q(prenom__isnull=True) | Q(prenom__exact='') |
        Q(numero_tel__isnull=True) | Q(numero_tel__exact='')
    )
    
    count_orphelins = clients_orphelins.count()
    
    if count_orphelins == 0:
        print("✅ Aucun client orphelin détecté")
        return 0
    
    print(f"⚠️  {count_orphelins} clients orphelins détectés")
    
    # Demander confirmation (mode interactif)
    reponse = input("Voulez-vous supprimer ces clients ? (oui/non): ").lower()
    
    if reponse in ['oui', 'o', 'yes', 'y']:
        clients_orphelins.delete()
        print(f"✅ {count_orphelins} clients orphelins supprimés")
        return count_orphelins
    else:
        print("❌ Suppression annulée")
        return 0

def corriger_donnees_manquantes():
    """Corrige les données manquantes des clients"""
    print("\n📝 CORRECTION DES DONNÉES MANQUANTES")
    print("=" * 40)
    
    corrections = 0
    
    # Corriger les noms/prénoms vides
    clients_sans_nom = Client.objects.filter(
        Q(nom__isnull=True) | Q(nom__exact='') |
        Q(prenom__isnull=True) | Q(prenom__exact='')
    ).filter(commandes__isnull=False).distinct()
    
    for client in clients_sans_nom:
        if not client.nom or client.nom == '':
            client.nom = "Client"
        if not client.prenom or client.prenom == '':
            client.prenom = f"#{client.id}"
        client.save()
        corrections += 1
        print(f"   ✅ Corrigé: {client.get_full_name()} (ID: {client.id})")
    
    print(f"✅ {corrections} clients corrigés")
    return corrections

def verifier_coherence_stats():
    """Vérifie la cohérence des statistiques après correction"""
    print("\n📊 VÉRIFICATION DE LA COHÉRENCE")
    print("=" * 40)
    
    total_clients = Client.objects.count()
    total_commandes = Commande.objects.count()
    clients_avec_commandes = Client.objects.filter(commandes__isnull=False).distinct().count()
    
    print(f"   • Total clients: {total_clients}")
    print(f"   • Total commandes: {total_commandes}")
    print(f"   • Clients avec commandes: {clients_avec_commandes}")
    print(f"   • Ratio: {(clients_avec_commandes/total_clients*100):.1f}%" if total_clients > 0 else "   • Ratio: 0%")
    
    # Vérifier les incohérences
    if clients_avec_commandes > total_clients:
        print("   ❌ ERREUR: Plus de clients avec commandes que de clients total!")
        return False
    
    if total_commandes > 0 and clients_avec_commandes == 0:
        print("   ❌ ERREUR: Des commandes existent mais aucun client n'a de commandes!")
        return False
    
    print("   ✅ Statistiques cohérentes")
    return True

def main():
    """Fonction principale de correction"""
    print("🚀 SCRIPT DE CORRECTION DES STATISTIQUES CLIENTS")
    print("=" * 60)
    
    # 1. Corriger les doublons
    clients_fusionnes = corriger_doublons_clients()
    
    # 2. Corriger les données manquantes
    corrections = corriger_donnees_manquantes()
    
    # 3. Nettoyer les clients orphelins (optionnel)
    orphelins_supprimes = nettoyer_clients_orphelins()
    
    # 4. Vérifier la cohérence finale
    coherent = verifier_coherence_stats()
    
    # Résumé
    print(f"\n📋 RÉSUMÉ DES CORRECTIONS:")
    print(f"   • Clients fusionnés: {clients_fusionnes}")
    print(f"   • Données corrigées: {corrections}")
    print(f"   • Clients orphelins supprimés: {orphelins_supprimes}")
    print(f"   • Cohérence: {'✅ OK' if coherent else '❌ Problème'}")
    
    print(f"\n✅ Script terminé!")

if __name__ == "__main__":
    main() 