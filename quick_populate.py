#!/usr/bin/env python
"""
Script simple pour ajouter des données de test minimales
"""

import os
import sys
import django
from datetime import datetime, timedelta
import random
from decimal import Decimal

# Configuration Django
sys.path.append('/workspaces/YZ-CMD')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from client.models import Client
from article.models import Article
from commande.models import Commande, Panier, EnumEtatCmd, EtatCommande, Operation
from parametre.models import Ville, Region, Operateur

def add_quick_test_data():
    """Ajouter rapidement des données de test pour les KPIs"""
    print("🚀 Ajout rapide de données de test...")
    
    # 1. Vérifier s'il y a des villes, sinon en créer quelques unes
    if not Ville.objects.exists():
        print("Création de quelques villes...")
        region, _ = Region.objects.get_or_create(nom_region="Casablanca-Settat")
        for ville_nom in ["Casablanca", "Rabat", "Marrakech"]:
            Ville.objects.get_or_create(
                nom=ville_nom,
                region=region,
                defaults={
                    'frais_livraison': 30.0,
                    'frequence_livraison': 'Quotidienne'
                }
            )
    
    # 2. Créer quelques articles s'il n'y en a pas assez
    if Article.objects.count() < 10:
        print("Création d'articles...")
        for i in range(10):
            Article.objects.get_or_create(
                nom=f"Chaussure Test {i+1}",
                couleur="Noir",
                pointure="42",
                defaults={
                    'reference': f"TEST{i+1}",
                    'prix_unitaire': Decimal(str(300 + i*10)),
                    'categorie': "Chaussures Homme",
                    'qte_disponible': random.randint(5, 50),
                    'description': f"Article de test {i+1}",
                    'actif': True
                }
            )
    
    # 3. Créer quelques clients
    if Client.objects.count() < 50:
        print("Création de clients...")
        for i in range(50):
            Client.objects.get_or_create(
                numero_tel=f"06{random.randint(10000000, 99999999)}",
                defaults={
                    'nom': f"Client{i+1}",
                    'prenom': f"Prenom{i+1}",
                    'adresse': f"Adresse {i+1}"
                }
            )
    
    # 4. Créer des états de commande
    etats_data = [
        {"libelle": "Non affectée", "ordre": 10, "couleur": "#6B7280"},
        {"libelle": "Confirmée", "ordre": 40, "couleur": "#10B981"},
        {"libelle": "Livrée", "ordre": 70, "couleur": "#059669"},
        {"libelle": "Annulée", "ordre": 80, "couleur": "#EF4444"},
    ]
    
    for etat_data in etats_data:
        EnumEtatCmd.objects.get_or_create(
            libelle=etat_data["libelle"],
            defaults={
                'ordre': etat_data["ordre"],
                'couleur': etat_data["couleur"]
            }
        )
    
    # 5. Créer des commandes pour les 30 derniers jours
    if Commande.objects.count() < 100:
        print("Création de commandes...")
        clients = list(Client.objects.all())
        articles = list(Article.objects.all())
        villes = list(Ville.objects.all())
        etats = list(EnumEtatCmd.objects.all())
        
        end_date = datetime.now().date()
        
        for i in range(150):  # 150 commandes
            # Date aléatoire des 30 derniers jours
            days_ago = random.randint(0, 30)
            date_commande = end_date - timedelta(days=days_ago)
            
            client = random.choice(clients)
            ville = random.choice(villes)
            
            # Créer la commande
            commande = Commande.objects.create(
                date_cmd=date_commande,
                client=client,
                ville=ville,
                adresse=f"Adresse livraison {i+1}",
                total_cmd=0,
                is_upsell=random.choice([True, False]) if random.random() < 0.2 else False
            )
            
            # Ajouter 1-3 articles par commande
            total = 0
            for _ in range(random.randint(1, 3)):
                article = random.choice(articles)
                quantite = random.randint(1, 2)
                sous_total = float(article.prix_unitaire) * quantite
                
                Panier.objects.create(
                    commande=commande,
                    article=article,
                    quantite=quantite,
                    sous_total=sous_total
                )
                total += sous_total
            
            commande.total_cmd = total
            commande.save()
            
            # Ajouter un état à la commande
            etat = random.choice(etats)
            EtatCommande.objects.create(
                commande=commande,
                enum_etat=etat,
                date_debut=date_commande
            )
            
            if i % 25 == 0:
                print(f"   {i}/150 commandes créées...")
    
    print("✅ Données de test créées avec succès !")
    print(f"📊 Résumé :")
    print(f"   - {Ville.objects.count()} villes")
    print(f"   - {Article.objects.count()} articles")
    print(f"   - {Client.objects.count()} clients")
    print(f"   - {Commande.objects.count()} commandes")
    print(f"   - {Panier.objects.count()} entrées panier")

if __name__ == "__main__":
    add_quick_test_data()
