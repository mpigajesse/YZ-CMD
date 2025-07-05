#!/usr/bin/env python3
"""
Script pour générer des données de test pour les performances d'opérateurs
"""

import os
import sys
import django
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Ajouter le chemin du projet Django
sys.path.append('/workspaces/YZ-CMD')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialiser Django
django.setup()

from commande.models import Commande, EtatCommande, Operation, EnumEtatCmd
from parametre.models import Operateur
from article.models import Article
from client.models import Client, Region, Ville
from django.contrib.auth.models import User

def generer_donnees_test_operateurs():
    """Génère des données de test pour les performances d'opérateurs"""
    
    print("=== Génération de données test pour les performances d'opérateurs ===\n")
    
    # Vérifier qu'on a des opérateurs
    operateurs = Operateur.objects.exclude(type_operateur='ADMIN')
    if not operateurs.exists():
        print("Aucun opérateur trouvé (hors ADMIN). Veuillez d'abord créer des opérateurs.")
        return
    
    print(f"Opérateurs disponibles: {operateurs.count()}")
    for op in operateurs[:5]:
        print(f"  - {op.nom} ({op.type_operateur})")
    
    # Vérifier qu'on a des commandes
    commandes = Commande.objects.all()
    if not commandes.exists():
        print("Aucune commande trouvée. Création de quelques commandes de test...")
        creer_commandes_test()
        commandes = Commande.objects.all()
    
    print(f"\nCommandes disponibles: {commandes.count()}")
    
    # Générer des opérations pour les 7 derniers jours
    debut_periode = timezone.now().date() - timedelta(days=7)
    fin_periode = timezone.now().date()
    
    print(f"Génération d'opérations du {debut_periode} au {fin_periode}")
    
    # Nettoyer les anciennes opérations de test
    Operation.objects.filter(
        date_operation__gte=debut_periode,
        date_operation__lte=fin_periode
    ).delete()
    print("Anciennes opérations supprimées.")
    
    # Nettoyer les anciens états de test
    EtatCommande.objects.filter(
        date_debut__gte=debut_periode,
        date_debut__lte=fin_periode
    ).delete()
    print("Anciens états supprimés.")
    
    # Types d'opérations possibles (selon le modèle)
    types_operations = [
        'APPEL', 'Appel Whatsapp', 'Message Whatsapp', 
        'Vocal Whatsapp', 'ENVOI_SMS', 'REMPLACEMENT', 
        'MODIFICATION_PREPA'
    ]
    
    # États possibles
    etats_possibles = ['Reçue', 'En traitement', 'Confirmée', 'En préparation', 'Expédiée']
    
    operations_creees = 0
    etats_crees = 0
    
    # Pour chaque jour de la période
    for jour in range((fin_periode - debut_periode).days + 1):
        date_courante = debut_periode + timedelta(days=jour)
        
        # Générer 10-30 opérations par jour
        nb_operations_jour = random.randint(10, 30)
        
        for _ in range(nb_operations_jour):
            # Choisir un opérateur aléatoire
            operateur = random.choice(operateurs)
            
            # Choisir une commande aléatoire
            commande = random.choice(commandes)
            
            # Créer une opération
            type_operation = random.choice(types_operations)
            heure_operation = random.randint(8, 18)
            minute_operation = random.randint(0, 59)
            
            date_operation = timezone.make_aware(
                datetime.combine(date_courante, datetime.min.time().replace(
                    hour=heure_operation, 
                    minute=minute_operation
                ))
            )
            
            operation = Operation.objects.create(
                commande=commande,
                operateur=operateur,
                type_operation=type_operation,
                date_operation=date_operation,
                conclusion=f"Opération {type_operation} effectuée sur commande {commande.num_cmd}"
            )
            operations_creees += 1
            
            # 70% de chance de créer un état de commande correspondant
            if random.random() < 0.7:
                # Choisir un état approprié selon le type d'opérateur
                if operateur.type_operateur == 'CONFIRMATION':
                    etats_candidats = ['Reçue', 'En traitement', 'Confirmée']
                elif operateur.type_operateur == 'LOGISTIQUE':
                    etats_candidats = ['En préparation', 'Expédiée']
                elif operateur.type_operateur == 'PREPARATION':
                    etats_candidats = ['En préparation']
                else:
                    etats_candidats = etats_possibles
                
                etat_nom = random.choice(etats_candidats)
                
                # Vérifier si l'EnumEtatCmd existe
                try:
                    enum_etat = EnumEtatCmd.objects.get(libelle=etat_nom)
                except EnumEtatCmd.DoesNotExist:
                    # Créer l'état s'il n'existe pas
                    enum_etat = EnumEtatCmd.objects.create(
                        libelle=etat_nom,
                        code=etat_nom.upper().replace(' ', '_'),
                        description=f"État {etat_nom}"
                    )
                
                # Créer l'état de commande
                etat = EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=enum_etat,
                    operateur=operateur,
                    date_debut=date_operation,
                    commentaire=f"État {etat_nom} par {operateur.nom}"
                )
                
                # 30% de chance de finir l'état (pour simuler des états terminés)
                if random.random() < 0.3:
                    duree_etat = random.randint(30, 240)  # 30 min à 4h
                    etat.date_fin = date_operation + timedelta(minutes=duree_etat)
                    etat.save()
                
                etats_crees += 1
    
    print(f"\n✅ Données générées avec succès !")
    print(f"   - Opérations créées: {operations_creees}")
    print(f"   - États de commandes créés: {etats_crees}")
    
    # Statistiques par opérateur
    print(f"\n📊 Statistiques par opérateur:")
    for operateur in operateurs:
        ops_count = Operation.objects.filter(
            operateur=operateur,
            date_operation__gte=debut_periode,
            date_operation__lte=fin_periode
        ).count()
        
        confirm_count = Operation.objects.filter(
            operateur=operateur,
            date_operation__gte=debut_periode,
            date_operation__lte=fin_periode,
            type_operation__icontains='Confirmation'
        ).count()
        
        print(f"   - {operateur.nom} ({operateur.type_operateur}): {ops_count} ops, {confirm_count} confirmations")

def creer_commandes_test():
    """Crée quelques commandes de test si elles n'existent pas"""
    
    # Vérifier qu'on a des clients
    if not Client.objects.exists():
        print("Création de clients de test...")
        
        # Créer une région et ville de test
        region, _ = Region.objects.get_or_create(
            nom_region='Test Region',
            defaults={'code_region': 'TEST'}
        )
        
        ville, _ = Ville.objects.get_or_create(
            nom_ville='Test Ville',
            defaults={'region': region, 'code_postal': '12345'}
        )
        
        # Créer quelques clients
        for i in range(5):
            Client.objects.create(
                nom=f'Client Test {i+1}',
                prenom=f'Prénom {i+1}',
                telephone=f'06000000{i:02d}',
                ville=ville
            )
    
    # Créer quelques commandes
    clients = Client.objects.all()
    for i in range(10):
        date_cmd = timezone.now().date() - timedelta(days=random.randint(0, 30))
        
        commande = Commande.objects.create(
            num_cmd=f'CMD-TEST-{i+1:04d}',
            client=random.choice(clients),
            date_cmd=date_cmd,
            total_cmd=Decimal(str(random.randint(100, 1000))),
            statut_paiement='EN_ATTENTE'
        )
        
        print(f"Commande créée: {commande.num_cmd}")

if __name__ == "__main__":
    generer_donnees_test_operateurs()
