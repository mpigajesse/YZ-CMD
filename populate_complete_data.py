#!/usr/bin/env python
"""
Script complet pour peupler toutes les tables avec des données de test
pour valider les onglets Vue Générale, Ventes et Clients
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from client.models import Client
from commande.models import Commande, Panier, EtatCommande, EnumEtatCmd
from article.models import Article
from parametre.models import Ville, Operateur, Region

def create_comprehensive_test_data():
    print("🚀 PEUPLEMENT COMPLET DES DONNÉES DE TEST")
    print("=" * 60)
    
    # Nettoyer les données existantes    print("\n🗑️ Nettoyage des données existantes...")
    Panier.objects.all().delete()
    EtatCommande.objects.all().delete()
    Commande.objects.all().delete()
    Client.objects.all().delete()
    Article.objects.all().delete()
    Operateur.objects.all().delete()
    # Supprimer les utilisateurs de test (sauf admin)
    User.objects.exclude(is_superuser=True).delete()
    Ville.objects.all().delete()
    Region.objects.all().delete()
    
    print("✅ Données supprimées")
    
    # 1. CRÉER LES RÉGIONS ET VILLES
    print("\n1️⃣ Création des régions et villes...")
    
    regions_data = [
        {'nom_region': 'Casablanca-Settat', 'villes': ['Casablanca', 'Settat', 'Berrechid']},
        {'nom_region': 'Rabat-Salé-Kénitra', 'villes': ['Rabat', 'Salé', 'Kénitra']},
        {'nom_region': 'Marrakech-Safi', 'villes': ['Marrakech', 'Safi', 'Essaouira']},
        {'nom_region': 'Fès-Meknès', 'villes': ['Fès', 'Meknès', 'Ifrane']},
    ]
    
    villes_created = []
    for region_data in regions_data:
        region = Region.objects.create(nom_region=region_data['nom_region'])
        for ville_nom in region_data['villes']:
            ville = Ville.objects.create(
                nom=ville_nom, 
                region=region,
                frais_livraison=random.uniform(5.0, 15.0),  # Frais de livraison aléatoires
                frequence_livraison=random.choice(['Quotidienne', 'Bi-quotidienne', 'Hebdomadaire'])
            )
            villes_created.append(ville)
            print(f"   ✅ {ville_nom} ({region.nom_region})")
      # 2. CRÉER LES OPÉRATEURS
    print("\n2️⃣ Création des opérateurs...")
    
    operateurs_data = [
        {'nom': 'Alami', 'prenom': 'Hassan', 'telephone': '0661234567', 'username': 'h.alami'},
        {'nom': 'Bennani', 'prenom': 'Fatima', 'telephone': '0662345678', 'username': 'f.bennani'},
        {'nom': 'Chraibi', 'prenom': 'Ahmed', 'telephone': '0663456789', 'username': 'a.chraibi'},
        {'nom': 'Douiri', 'prenom': 'Khadija', 'telephone': '0664567890', 'username': 'k.douiri'},
    ]
    
    operateurs_created = []
    for op_data in operateurs_data:
        # Créer d'abord l'utilisateur Django
        user = User.objects.create_user(
            username=op_data['username'],
            email=f"{op_data['username']}@yoozak.com",
            password='password123'
        )
        
        # Puis créer l'opérateur
        operateur = Operateur.objects.create(
            user=user,
            nom=op_data['nom'],
            prenom=op_data['prenom'],
            mail=f"{op_data['username']}@yoozak.com",
            telephone=op_data['telephone'],
            type_operateur='CONFIRMATION'
        )
        operateurs_created.append(operateur)
        print(f"   ✅ {operateur.prenom} {operateur.nom} ({user.username})")
    
    # 3. CRÉER LES ARTICLES (CHAUSSURES)
    print("\n3️⃣ Création des articles (chaussures)...")
    articles_data = [
        {'nom': 'Sneakers Classic White', 'reference': 'SNK001', 'couleur': 'Blanc', 'pointure': '42', 'categorie': 'Sneakers', 'prix_unitaire': 299.00, 'qte_disponible': 50},
        {'nom': 'Boots Leather Brown', 'reference': 'BOT001', 'couleur': 'Marron', 'pointure': '41', 'categorie': 'Boots', 'prix_unitaire': 459.00, 'qte_disponible': 30},
        {'nom': 'Sandales Summer Blue', 'reference': 'SAN001', 'couleur': 'Bleu', 'pointure': '39', 'categorie': 'Sandales', 'prix_unitaire': 189.00, 'qte_disponible': 80},
        {'nom': 'Escarpins Elegant Black', 'reference': 'ESC001', 'couleur': 'Noir', 'pointure': '38', 'categorie': 'Escarpins', 'prix_unitaire': 399.00, 'qte_disponible': 25},
        {'nom': 'Baskets Sport Red', 'reference': 'BAS001', 'couleur': 'Rouge', 'pointure': '43', 'categorie': 'Baskets', 'prix_unitaire': 249.00, 'qte_disponible': 60},
        {'nom': 'Mocassins Luxury Tan', 'reference': 'MOC001', 'couleur': 'Tan', 'pointure': '40', 'categorie': 'Mocassins', 'prix_unitaire': 549.00, 'qte_disponible': 20},
        {'nom': 'Ballerines Soft Pink', 'reference': 'BAL001', 'couleur': 'Rose', 'pointure': '37', 'categorie': 'Ballerines', 'prix_unitaire': 179.00, 'qte_disponible': 40},
        {'nom': 'Chaussures Business Gray', 'reference': 'BUS001', 'couleur': 'Gris', 'pointure': '44', 'categorie': 'Business', 'prix_unitaire': 429.00, 'qte_disponible': 35},
    ]
    
    articles_created = []
    for art_data in articles_data:
        article = Article.objects.create(**art_data)
        articles_created.append(article)
        print(f"   ✅ {article.nom} - {article.prix_unitaire} DH (Stock: {article.qte_disponible})")
    
    # 4. CRÉER LES CLIENTS
    print("\n4️⃣ Création des clients...")
    
    clients_data = [
        {'nom': 'Benjelloun', 'prenom': 'Youssef', 'numero_tel': '0661111111', 'email': 'youssef.b@email.com'},
        {'nom': 'El Mansouri', 'prenom': 'Aicha', 'numero_tel': '0662222222', 'email': 'aicha.m@email.com'},
        {'nom': 'Tazi', 'prenom': 'Omar', 'numero_tel': '0663333333', 'email': 'omar.t@email.com'},
        {'nom': 'Lahlou', 'prenom': 'Zineb', 'numero_tel': '0664444444', 'email': 'zineb.l@email.com'},
        {'nom': 'Fassi', 'prenom': 'Mehdi', 'numero_tel': '0665555555', 'email': 'mehdi.f@email.com'},
        {'nom': 'Berrada', 'prenom': 'Salma', 'numero_tel': '0666666666', 'email': 'salma.b@email.com'},
        {'nom': 'Zerouali', 'prenom': 'Karim', 'numero_tel': '0667777777', 'email': 'karim.z@email.com'},
        {'nom': 'Alaoui', 'prenom': 'Leila', 'numero_tel': '0668888888', 'email': 'leila.a@email.com'},
        {'nom': 'Chakib', 'prenom': 'Reda', 'numero_tel': '0669999999', 'email': 'reda.c@email.com'},
        {'nom': 'Benali', 'prenom': 'Nadia', 'numero_tel': '0660000000', 'email': 'nadia.b@email.com'},
    ]
    
    clients_created = []
    today = timezone.now().date()
    for i, client_data in enumerate(clients_data):
        # Créer des dates de création variées (sur les 60 derniers jours)
        days_ago = random.randint(0, 60)
        creation_date = timezone.now() - timedelta(days=days_ago)
        
        client = Client.objects.create(**client_data)
        # Modifier la date de création
        Client.objects.filter(id=client.id).update(date_creation=creation_date)
        
        clients_created.append(client)
        print(f"   ✅ {client.prenom} {client.nom} (créé il y a {days_ago} jours)")
    
    # 5. CRÉER LES ÉTATS DE COMMANDE
    print("\n5️⃣ Création des états de commande...")
    
    etats_data = [
        {'libelle': 'En attente', 'description': 'Commande en attente de traitement'},
        {'libelle': 'Confirmée', 'description': 'Commande confirmée par le client'},
        {'libelle': 'En préparation', 'description': 'Commande en cours de préparation'},
        {'libelle': 'Expédiée', 'description': 'Commande expédiée'},
        {'libelle': 'Livrée', 'description': 'Commande livrée au client'},
        {'libelle': 'Annulée', 'description': 'Commande annulée'},
        {'libelle': 'Retournée', 'description': 'Commande retournée par le client'},
    ]
    
    etats_created = []
    for etat_data in etats_data:
        try:
            etat = EnumEtatCmd.objects.create(**etat_data)
            etats_created.append(etat)
            print(f"   ✅ {etat.libelle}")
        except Exception as e:
            print(f"   ⚠️ Erreur création état {etat_data['libelle']}: {e}")
    
    # Si pas d'états créés, utiliser des valeurs par défaut
    if not etats_created:
        print("   ⚠️ Utilisation d'états par défaut...")
        etats_created = list(EnumEtatCmd.objects.all())
    
    # 6. CRÉER LES COMMANDES AVEC HISTORIQUE
    print("\n6️⃣ Création des commandes avec historique...")
    
    # Générer commandes sur les 45 derniers jours
    commandes_created = []
    for i in range(25):  # 25 commandes
        # Répartition temporelle réaliste
        if i < 8:  # 8 commandes récentes (0-7 jours)
            days_ago = random.randint(0, 7)
        elif i < 15:  # 7 commandes moyennes (8-20 jours)
            days_ago = random.randint(8, 20)
        else:  # 10 commandes anciennes (21-45 jours)
            days_ago = random.randint(21, 45)
        
        date_cmd = today - timedelta(days=days_ago)
        
        # Sélectionner client et ville aléatoirement
        client = random.choice(clients_created)
        ville = random.choice(villes_created)
        
        # Calculer total réaliste
        base_total = random.choice([199, 249, 299, 399, 459, 549, 629, 799])
        variation = random.uniform(0.8, 1.2)  # ±20% de variation
        total_cmd = round(base_total * variation, 2)
        
        commande = Commande.objects.create(
            client=client,
            total_cmd=total_cmd,
            date_cmd=date_cmd,
            ville=ville,
            adresse=f"{random.randint(1, 999)} Rue {random.choice(['Mohammed V', 'Hassan II', 'Al Massira', 'Atlas', 'Sebou'])}, {ville.nom}",
            is_upsell=random.choice([True, False]) if random.random() < 0.3 else False
        )
        
        commandes_created.append(commande)
        
        # Ajouter des états à la commande
        if etats_created:
            # Déterminer l'état final selon l'âge de la commande
            if days_ago <= 3:  # Commandes récentes
                etat_final = random.choice(['Confirmée', 'En préparation', 'Expédiée'])
            elif days_ago <= 10:  # Commandes moyennes
                etat_final = random.choice(['Expédiée', 'Livrée'])
            else:  # Commandes anciennes
                etat_final = random.choice(['Livrée', 'Livrée', 'Livrée', 'Annulée', 'Retournée'])
            
            # Trouver l'état correspondant
            try:
                etat_obj = next((e for e in etats_created if e.libelle == etat_final), etats_created[0])
                EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=etat_obj,
                    date_debut=timezone.make_aware(datetime.combine(date_cmd, datetime.min.time()) + timedelta(hours=random.randint(1, 8))),
                    date_fin=None if etat_final in ['En préparation', 'Expédiée'] else timezone.make_aware(datetime.combine(date_cmd, datetime.min.time()) + timedelta(hours=random.randint(12, 48)))
                )
            except Exception as e:
                print(f"   ⚠️ Erreur création état pour commande {commande.id}: {e}")
        
        print(f"   ✅ Commande {commande.num_cmd or commande.id} - {client.prenom} {client.nom} - {total_cmd} DH ({etat_final if 'etat_final' in locals() else 'Sans état'})")
    
    # 7. CRÉER LES PANIERS (ARTICLES DANS COMMANDES)
    print("\n7️⃣ Création des paniers (articles commandés)...")
    
    paniers_created = 0
    for commande in commandes_created:
        # Nombre d'articles par commande (1-3)
        nb_articles = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
        
        articles_choisis = random.sample(articles_created, min(nb_articles, len(articles_created)))
        
        for article in articles_choisis:
            quantite = random.choices([1, 2], weights=[80, 20])[0]
            sous_total = article.prix_unitaire * quantite
            
            Panier.objects.create(
                commande=commande,
                article=article,
                quantite=quantite,
                sous_total=sous_total
            )
            paniers_created += 1
    
    print(f"   ✅ {paniers_created} articles ajoutés aux paniers")
    
    # 8. STATISTIQUES FINALES
    print("\n" + "=" * 60)
    print("📊 RÉCAPITULATIF DES DONNÉES CRÉÉES")
    print("=" * 60)
    
    print(f"🏙️ Régions : {Region.objects.count()}")
    print(f"🌍 Villes : {Ville.objects.count()}")
    print(f"👨‍💼 Opérateurs : {Operateur.objects.count()}")
    print(f"👟 Articles : {Article.objects.count()}")
    print(f"👥 Clients : {Client.objects.count()}")
    print(f"📦 Commandes : {Commande.objects.count()}")
    print(f"🛒 Paniers : {Panier.objects.count()}")
    print(f"📋 États commandes : {EtatCommande.objects.count()}")
    
    # Statistiques business
    total_ca = sum(float(c.total_cmd) for c in commandes_created)
    commandes_30j = Commande.objects.filter(date_cmd__gte=today - timedelta(days=30)).count()
    clients_actifs = len(set(Commande.objects.filter(date_cmd__gte=today - timedelta(days=30)).values_list('client_id', flat=True)))
    
    print(f"\n💰 CA Total : {total_ca:,.2f} DH")
    print(f"📈 Commandes 30j : {commandes_30j}")
    print(f"👥 Clients actifs 30j : {clients_actifs}")
    print(f"🎯 Panier moyen : {total_ca/len(commandes_created):,.2f} DH")
    
    print(f"\n🎉 DONNÉES DE TEST CRÉÉES AVEC SUCCÈS !")
    print(f"🌐 Vous pouvez maintenant tester tous les onglets KPIs !")

if __name__ == '__main__':
    try:
        create_comprehensive_test_data()
    except Exception as e:
        print(f"❌ Erreur : {e}")
        import traceback
        traceback.print_exc()
