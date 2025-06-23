#!/usr/bin/env python
"""
Script pour populer les tables avec des données de test réalistes pour Yoozak
Données générées : articles, clients, commandes, opérateurs, opérations sur plusieurs mois
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

from django.contrib.auth.models import User, Group
from client.models import Client
from article.models import Article
from commande.models import Commande, Panier, EnumEtatCmd, EtatCommande, Operation
from parametre.models import Ville, Region, Operateur

def clear_existing_data():
    """Nettoyer les données existantes (optionnel)"""
    print("🧹 Nettoyage des données existantes...")
    Operation.objects.all().delete()
    EtatCommande.objects.all().delete()
    Panier.objects.all().delete()
    Commande.objects.all().delete()
    Article.objects.all().delete()
    Client.objects.all().delete()
    # Ne pas supprimer les opérateurs et villes car ils peuvent être utilisés

def create_regions_and_cities():
    """Créer les régions et villes du Maroc"""
    print("🌍 Création des régions et villes...")
    
    regions_villes = {
        "Casablanca-Settat": ["Casablanca", "Settat", "El Jadida", "Berrechid", "Mohammedia"],
        "Rabat-Salé-Kénitra": ["Rabat", "Salé", "Kénitra", "Témara", "Skhirat"],
        "Marrakech-Safi": ["Marrakech", "Safi", "Essaouira", "Kelaa des Sraghna"],
        "Fès-Meknès": ["Fès", "Meknès", "Ifrane", "Sefrou"],
        "Tanger-Tétouan-Al Hoceïma": ["Tanger", "Tétouan", "Al Hoceïma", "Larache"],
        "Oriental": ["Oujda", "Nador", "Berkane", "Taourirt"],
        "Souss-Massa": ["Agadir", "Tiznit", "Taroudant", "Inezgane"],
        "Drâa-Tafilalet": ["Errachidia", "Ouarzazate", "Zagora"],
        "Béni Mellal-Khénifra": ["Béni Mellal", "Khénifra", "Khouribga"],
        "Grand Casablanca": ["Ain Sebaa", "Sidi Bernoussi", "Hay Hassani"]
    }
    
    created_villes = []
    for region_nom, villes in regions_villes.items():
        region, created = Region.objects.get_or_create(
            nom_region=region_nom  # Utiliser nom_region au lieu de nom
        )
        
        for ville_nom in villes:
            ville, created = Ville.objects.get_or_create(
                nom=ville_nom,
                region=region,
                defaults={
                    'frais_livraison': random.choice([25.0, 30.0, 35.0, 40.0]),
                    'frequence_livraison': random.choice(['Quotidienne', 'Bi-hebdomadaire', 'Hebdomadaire'])
                }
            )
            created_villes.append(ville)
    
    return created_villes

def create_operators():
    """Créer des opérateurs de test"""
    print("👨‍💼 Création des opérateurs...")
    
    operateurs_data = [
        {"nom": "Benali", "prenom": "Youssef", "type": "CONFIRMATION", "username": "youssef_conf"},
        {"nom": "Benjelloun", "prenom": "Aicha", "type": "CONFIRMATION", "username": "aicha_conf"},
        {"nom": "Kassmi", "prenom": "Hassan", "type": "CONFIRMATION", "username": "hassan_conf"},
        {"nom": "Zahra", "prenom": "Fatima", "type": "CONFIRMATION", "username": "fatima_conf"},
        {"nom": "Lahlou", "prenom": "Omar", "type": "LOGISTIQUE", "username": "omar_log"},
        {"nom": "Alami", "prenom": "Zineb", "type": "LOGISTIQUE", "username": "zineb_log"},
        {"nom": "Admin", "prenom": "System", "type": "ADMIN", "username": "admin_sys"},
    ]
    
    created_operators = []
    for op_data in operateurs_data:
        # Créer l'utilisateur Django
        user, user_created = User.objects.get_or_create(
            username=op_data["username"],
            defaults={
                'email': f"{op_data['username']}@yoozak.ma",
                'first_name': op_data["prenom"],
                'last_name': op_data["nom"],
            }
        )
        if user_created:
            user.set_password('password123')
            user.save()
        
        # Créer l'opérateur
        operateur, created = Operateur.objects.get_or_create(
            user=user,
            defaults={
                'nom': op_data["nom"],
                'prenom': op_data["prenom"],
                'mail': f"{op_data['username']}@yoozak.ma",
                'type_operateur': op_data["type"],
                'telephone': f"0{random.randint(600000000, 799999999)}",
                'actif': True
            }
        )
        created_operators.append(operateur)
    
    return created_operators

def create_command_states():
    """Créer les états de commande"""
    print("📋 Création des états de commande...")
    
    etats_data = [
        {"libelle": "Non affectée", "ordre": 10, "couleur": "#6B7280"},
        {"libelle": "Affectée", "ordre": 20, "couleur": "#3B82F6"},
        {"libelle": "En cours de confirmation", "ordre": 30, "couleur": "#F59E0B"},
        {"libelle": "Confirmée", "ordre": 40, "couleur": "#10B981"},
        {"libelle": "En préparation", "ordre": 50, "couleur": "#8B5CF6"},
        {"libelle": "En livraison", "ordre": 60, "couleur": "#EC4899"},
        {"libelle": "Livrée", "ordre": 70, "couleur": "#059669"},
        {"libelle": "Annulée", "ordre": 80, "couleur": "#EF4444"},
        {"libelle": "Erronée", "ordre": 90, "couleur": "#F97316"},
        {"libelle": "Doublon", "ordre": 95, "couleur": "#DC2626"},
    ]
    
    created_states = []
    for etat_data in etats_data:
        etat, created = EnumEtatCmd.objects.get_or_create(
            libelle=etat_data["libelle"],
            defaults={
                'ordre': etat_data["ordre"],
                'couleur': etat_data["couleur"]
            }
        )
        created_states.append(etat)
    
    return created_states

def create_articles():
    """Créer des articles Yoozak (chaussures et sandales)"""
    print("👟 Création des articles...")
    
    # Modèles de chaussures marocaines authentiques
    modeles_chaussures = [
        "Derby Classic Cuir", "Oxford Premium", "Mocassin Traditionnel", 
        "Bottine Moderne", "Chaussure de Ville", "Derby Sport",
        "Oxford Casual", "Mocassin Confort", "Bottine Classique",
        "Chaussure Business", "Derby Weekend", "Oxford Style"
    ]
    
    modeles_sandales = [
        "Sandale Premium Cuir", "Sandale Confort Été", "Sandale Traditionnelle",
        "Sandale Sport", "Sandale Casual", "Sandale Élégante",
        "Sandale Plage", "Sandale Urbaine"
    ]
    
    couleurs = ["Noir", "Marron", "Beige", "Cognac", "Bordeaux", "Bleu Marine"]
    pointures_homme = ["38", "39", "40", "41", "42", "43", "44", "45", "46"]
    pointures_femme = ["35", "36", "37", "38", "39", "40", "41", "42"]
    
    categories = [
        ("Chaussures Homme", modeles_chaussures, pointures_homme),
        ("Chaussures Femme", modeles_chaussures, pointures_femme),
        ("Sandales Homme", modeles_sandales, pointures_homme),
        ("Sandales Femme", modeles_sandales, pointures_femme),
    ]
    
    created_articles = []
    reference_counter = 1000
    
    for categorie, modeles, pointures in categories:
        for modele in modeles[:8]:  # 8 modèles par catégorie
            for couleur in couleurs[:4]:  # 4 couleurs par modèle
                for pointure in pointures:
                    # Prix réalistes selon le type
                    if "Premium" in modele or "Business" in modele:
                        prix_base = random.uniform(450, 650)
                    elif "Classic" in modele or "Traditionnel" in modele:
                        prix_base = random.uniform(350, 500)
                    else:
                        prix_base = random.uniform(250, 400)
                    
                    # Stock réaliste selon pointure (38-42 plus populaires)
                    if pointure in ["38", "39", "40", "41", "42"]:
                        stock_base = random.randint(15, 80)
                    else:
                        stock_base = random.randint(5, 25)
                    
                    # Parfois stock critique ou épuisé
                    if random.random() < 0.15:  # 15% de chance
                        stock_base = random.randint(0, 8)
                    
                    article, created = Article.objects.get_or_create(
                        nom=modele,
                        couleur=couleur,
                        pointure=pointure,
                        defaults={
                            'reference': f"YZ{reference_counter}",
                            'prix_unitaire': Decimal(str(round(prix_base, 2))),
                            'categorie': categorie,
                            'qte_disponible': stock_base,
                            'description': f"{modele} en {couleur.lower()}, pointure {pointure}. Cuir véritable de qualité marocaine.",
                            'actif': True
                        }
                    )
                    if created:
                        created_articles.append(article)
                        reference_counter += 1
                    else:
                        # Mettre à jour le stock si l'article existe déjà
                        article.qte_disponible = stock_base
                        article.save()
                        created_articles.append(article)
    
    print(f"✅ {len(created_articles)} articles créés")
    return created_articles

def create_clients():
    """Créer des clients réalistes"""
    print("👥 Création des clients...")
    
    prenoms_hommes = ["Mohammed", "Ahmed", "Youssef", "Hassan", "Omar", "Abdelaziz", "Khalid", "Said", "Rachid", "Karim"]
    prenoms_femmes = ["Fatima", "Aicha", "Khadija", "Zineb", "Nadia", "Samira", "Latifa", "Amina", "Salma", "Hasna"]
    noms = ["Alami", "Benali", "Benjelloun", "Hassani", "Tazi", "Fassi", "Chraibi", "Lahlou", "Bennani", "Kadiri",
           "Amrani", "Berrada", "Cherkaoui", "Filali", "Guerraoui", "Hafidi", "Idrissi", "Jellal", "Kabbaj", "Lamrani"]
    
    villes = list(Ville.objects.all())
    created_clients = []
    
    for i in range(500):  # 500 clients
        is_female = random.choice([True, False])
        prenom = random.choice(prenoms_femmes if is_female else prenoms_hommes)
        nom = random.choice(noms)
        
        # Téléphone marocain réaliste
        prefixes = ["06", "07"]
        telephone = f"{random.choice(prefixes)}{random.randint(10000000, 99999999)}"
        
        client = Client.objects.create(
            nom=nom,
            prenom=prenom,
            numero_tel=telephone,
            ville=random.choice(villes) if villes else None,
            adresse=f"{random.randint(1, 999)} Rue {random.choice(['Mohammed V', 'Hassan II', 'Al Massira', 'Anfa', 'Agdal'])}"
        )
        created_clients.append(client)
    
    print(f"✅ {len(created_clients)} clients créés")
    return created_clients

def create_commands_and_operations(clients, articles, operators, states, villes):
    """Créer des commandes réalistes avec historique sur plusieurs mois"""
    print("📦 Création des commandes et opérations...")
    
    # Répartition réaliste des états
    etats_dict = {etat.libelle: etat for etat in states}
    
    # Dates sur les 6 derniers mois avec patterns réalistes
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=180)
    
    created_commands = []
    operations_counter = 0
    
    for i in range(2500):  # 2500 commandes sur 6 mois
        # Date de commande avec patterns réalistes (plus récent = plus de commandes)
        days_ago = random.choices(
            range(180),
            weights=[max(1, 180-d) for d in range(180)],  # Plus récent = plus probable
            k=1
        )[0]
        date_commande = end_date - timedelta(days=days_ago)
        
        # Client aléatoire
        client = random.choice(clients)
        ville = random.choice(villes)
        
        # Créer la commande
        commande = Commande.objects.create(
            date_cmd=date_commande,
            client=client,
            ville=ville,
            adresse=f"{random.randint(1, 999)} {random.choice(['Avenue', 'Rue', 'Boulevard'])} {random.choice(['Mohammed V', 'Hassan II', 'Al Massira'])}",
            total_cmd=0,  # Sera calculé après ajout des articles
            is_upsell=random.choice([True, False]) if random.random() < 0.3 else False,
            produit_init=random.choice(["Chaussure homme", "Sandale femme", "Mocassin", "Derby"])
        )
        
        # Ajouter des articles au panier (1-4 articles par commande)
        nb_articles = random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]
        total_commande = 0
        
        for _ in range(nb_articles):
            article = random.choice(articles)
            quantite = random.choices([1, 2, 3], weights=[80, 15, 5])[0]
            sous_total = float(article.prix_unitaire) * quantite
            
            Panier.objects.create(
                commande=commande,
                article=article,
                quantite=quantite,
                sous_total=sous_total
            )
            total_commande += sous_total
        
        commande.total_cmd = total_commande
        commande.save()
        
        # Simuler l'évolution des états selon l'âge de la commande
        current_date = date_commande
        current_state = None
        
        # États de base selon l'âge de la commande
        if days_ago < 1:  # Commandes très récentes
            possible_states = ["Non affectée", "Affectée"]
        elif days_ago < 3:  # Commandes récentes
            possible_states = ["Affectée", "En cours de confirmation", "Confirmée"]
        elif days_ago < 7:  # Commandes de la semaine
            possible_states = ["Confirmée", "En préparation", "En livraison"]
        elif days_ago < 30:  # Commandes du mois
            possible_states = ["En livraison", "Livrée", "Annulée"]
        else:  # Commandes anciennes
            possible_states = ["Livrée", "Annulée"]
            if random.random() < 0.05:  # 5% de doublons/erreurs
                possible_states.extend(["Doublon", "Erronée"])
        
        # Créer les états et opérations
        for state_name in possible_states[:random.randint(1, min(3, len(possible_states)))]:
            if state_name in etats_dict:
                etat = etats_dict[state_name]
                operateur = random.choice([op for op in operators if op.type_operateur in ['CONFIRMATION', 'LOGISTIQUE']])
                
                # Créer l'état
                etat_commande = EtatCommande.objects.create(
                    commande=commande,
                    enum_etat=etat,
                    operateur=operateur,
                    date_debut=current_date,
                    commentaire=f"État {state_name} appliqué automatiquement"
                )
                
                # Terminer l'état précédent
                if current_state:
                    current_state.date_fin = current_date
                    current_state.save()
                
                current_state = etat_commande
                
                # Créer des opérations réalistes selon l'état
                if state_name in ["Affectée", "En cours de confirmation"]:
                    # Opérations de confirmation
                    for _ in range(random.randint(1, 3)):
                        operation_type = random.choice(["APPEL", "Appel Whatsapp", "Message Whatsapp"])
                        conclusion = random.choice([
                            "Client intéressé", "Client hésitant", "Client non joignable",
                            "Client non intéressé", "Commande confirmée", "commande reportée"
                        ])
                        
                        Operation.objects.create(
                            commande=commande,
                            operateur=operateur,
                            type_operation=operation_type,
                            conclusion=conclusion,
                            date_operation=current_date
                        )
                        operations_counter += 1
                
                # Avancer la date pour le prochain état
                current_date += timedelta(hours=random.randint(2, 48))
        
        created_commands.append(commande)
        
        if i % 250 == 0:
            print(f"   {i}/2500 commandes créées...")
    
    print(f"✅ {len(created_commands)} commandes créées")
    print(f"✅ {operations_counter} opérations créées")
    return created_commands

def main():
    print("🚀 Démarrage de la population des données Yoozak...")
    print("=" * 50)
    
    # Étape 1: Nettoyer (optionnel)
    # clear_existing_data()
    
    # Étape 2: Créer les données de base
    villes = create_regions_and_cities()
    operators = create_operators()
    states = create_command_states()
    
    # Étape 3: Créer les données métier
    articles = create_articles()
    clients = create_clients()
    
    # Étape 4: Créer les commandes et opérations
    commands = create_commands_and_operations(clients, articles, operators, states, villes)
    
    print("=" * 50)
    print("✅ Population des données terminée avec succès !")
    print(f"📊 Résumé :")
    print(f"   - {len(villes)} villes")
    print(f"   - {len(operators)} opérateurs")
    print(f"   - {len(states)} états de commande")
    print(f"   - {len(articles)} articles")
    print(f"   - {len(clients)} clients")
    print(f"   - {len(commands)} commandes")
    print(f"   - {Operation.objects.count()} opérations")
    print(f"   - {Panier.objects.count()} entrées panier")
    print(f"   - {EtatCommande.objects.count()} états de commande")

if __name__ == "__main__":
    main()
