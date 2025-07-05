#!/usr/bin/env python3
"""
Script simple pour ajouter des opérations de test
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Configuration Django
sys.path.append('/workspaces/YZ-CMD')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from parametre.models import Operateur
from commande.models import Commande, Operation, EtatCommande, EnumEtatCmd
from client.models import Client
from decimal import Decimal
import random

def main():
    print("=== Ajout d'opérations de test ===")
    
    # Vérifier les opérateurs
    operateurs = list(Operateur.objects.exclude(type_operateur='ADMIN'))
    print(f"Opérateurs trouvés: {len(operateurs)}")
    
    if not operateurs:
        print("Aucun opérateur trouvé !")
        return
    
    # Vérifier les commandes 
    commandes = list(Commande.objects.all())
    print(f"Commandes trouvées: {len(commandes)}")
    
    if not commandes:
        print("Pas de commandes, création d'une commande de test...")
        # Créer un client de test
        if not Client.objects.exists():
            client = Client.objects.create(
                nom='Client Test',
                prenom='Test',
                numero_tel='0600000000'
            )
        else:
            client = Client.objects.first()
            
        # Créer une commande de test
        commande = Commande.objects.create(
            client=client,
            date_cmd=timezone.now().date(),
            total_cmd=500.0,
            adresse='Adresse test'
        )
        commandes = [commande]
        print(f"Commande créée: {commande.num_cmd}")
    
    # Supprimer les anciennes opérations de test
    Operation.objects.filter(conclusion__contains='Test operation').delete()
    print("Anciennes opérations de test supprimées")
    
    # Créer 20 opérations sur les 3 derniers jours
    types_ops = ['APPEL', 'Appel Whatsapp', 'Message Whatsapp', 'ENVOI_SMS']
    
    for i in range(20):
        # Date aléatoire dans les 3 derniers jours
        jours_arriere = random.randint(0, 2)
        date_op = timezone.now() - timedelta(days=jours_arriere, hours=random.randint(0, 8))
        
        # Opérateur et commande aléatoires
        operateur = random.choice(operateurs)
        commande = random.choice(commandes)
        type_op = random.choice(types_ops)
        
        operation = Operation.objects.create(
            commande=commande,
            operateur=operateur,
            type_operation=type_op,
            date_operation=date_op,
            conclusion=f"Test operation {i+1} - {type_op} effectué"
        )
        
        print(f"Opération {i+1}: {operateur.nom} - {type_op} sur {commande.num_cmd}")
        
        # 50% de chance d'ajouter un état de commande
        if random.random() < 0.5:
            # Créer ou récupérer des états de test
            etats_noms = ['Reçue', 'En traitement', 'Confirmée']
            etat_nom = random.choice(etats_noms)
            
            enum_etat, created = EnumEtatCmd.objects.get_or_create(
                libelle=etat_nom,
                defaults={'ordre': 1, 'couleur': '#6B7280'}
            )
            
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=enum_etat,
                operateur=operateur,
                date_debut=date_op,
                commentaire=f"État test {etat_nom}"
            )
    
    print(f"\n✅ {Operation.objects.count()} opérations au total")
    print("Test terminé ! Vous pouvez maintenant voir les données dans l'interface.")

if __name__ == "__main__":
    main()
