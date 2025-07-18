#!/usr/bin/env python3
"""
Générateur de commandes pour YZ-CMD
Génère 573 commandes au format CSV similaire à CMDInit.csv
"""

import csv
import random
import os
from datetime import datetime, timedelta

# Données de base pour la génération
NOMS_FRANCAIS = [
    "Ahmed", "Mohamed", "Hassan", "Youssef", "Karim", "Omar", "Noureddine", "Abdelkader",
    "Fatima", "Aicha", "Khadija", "Zineb", "Salma", "Nadia", "Latifa", "Samira",
    "Redouane", "Brahim", "Mustapha", "Driss", "Ismail", "Hamid", "Lahcen", "Said",
    "Houda", "Naima", "Rajae", "Ikram", "Layla", "Malika", "Souad", "Widad"
]

NOMS_ARABES = [
    "محمد", "أحمد", "حسن", "يوسف", "كريم", "عمر", "نور الدين", "عبد القادر",
    "فاطمة", "عائشة", "خديجة", "زينب", "سلمى", "نادية", "لطيفة", "سميرة",
    "رضوان", "إبراهيم", "مصطفى", "إدريس", "إسماعيل", "حميد", "لحسن", "سعيد",
    "هدى", "نعيمة", "رجاء", "إكرام", "ليلى", "مليكة", "سعاد", "وداد"
]

NOMS_FAMILLE = [
    "Benali", "El Fassi", "Bennani", "Amrani", "Idrissi", "Tazi", "Alaoui", "Chafik",
    "Bouziane", "Zahidi", "Ouardi", "Lahlou", "Essabri", "Touhami", "Skalli", "Abouali",
    "بن علي", "الفاسي", "بناني", "العمراني", "الإدريسي", "التازي", "العلوي", "الشافعي"
]

VILLES_MAROC = [
    "Casablanca", "Rabat", "Fès", "Marrakech", "Agadir", "Tanger", "Meknès", "Oujda",
    "Kénitra", "Tétouan", "Safi", "El Jadida", "Beni Mellal", "Errachidia", "Taza",
    "Essaouira", "Khouribga", "Ouarzazate", "Settat", "Larache", "Khemisset", "Guercif",
    "الدار البيضاء", "الرباط", "فاس", "مراكش", "أگادير", "طنجة", "مكناس", "وجدة",
    "القنيطرة", "تطوان", "آسفي", "الجديدة", "بني ملال", "الراشيدية", "تازة"
]

PRODUITS = [
    {"nom": "ESP HOM YZ650", "tailles": ["40", "41", "42", "43", "44"], "couleurs": ["أسود أبيض / noir blanc", "الأزرق / bleu", "الرمادي / gris"], "prix": 299},
    {"nom": "CHAUSS FEM YZ 244", "tailles": ["37", "38", "39", "40", "41"], "couleurs": ["أسود / noir", "أحمر / rouge", "أزرق / bleu"], "prix": 249},
    {"nom": "SDL HOM YZ740", "tailles": ["41", "42", "43", "44", "45"], "couleurs": ["noir / أسود", "marron / بني"], "prix": 345},
    {"nom": "CHAUSS FEM YZ 247", "tailles": ["36", "37", "38", "39", "40"], "couleurs": ["Noir / noir", "Rouge / rouge", "Bleu / bleu"], "prix": 239},
    {"nom": "CHAUSS HOM YZ 303", "tailles": ["40", "41", "42", "43", "44"], "couleurs": ["Marron / marron", "Noir / noir"], "prix": 289},
    {"nom": "CHAUSS FEM YZ 248", "tailles": ["37", "38", "39", "40", "41"], "couleurs": ["Rouge / rouge", "Bleu / bleu", "Vert / vert"], "prix": 259},
    {"nom": "CHAUSS HOM YZ 304", "tailles": ["41", "42", "43", "44", "45"], "couleurs": ["Noir / noir", "Marron / marron"], "prix": 279},
    {"nom": "CHAUSS FEM YZ 249", "tailles": ["36", "37", "38", "39", "40"], "couleurs": ["Bleu / bleu", "Rose / rose"], "prix": 249}
]

STATUTS = ["Non affectée", "Doublon", "Erronée"]
STATUTS_PROBABILITES = [0.85, 0.10, 0.05]  # 85% non affectées, 10% doublons, 5% erronées

OPERATEURS = ["", "Op1", "Op2", "Op3", "Marketing", "Vente"]

def generer_numero_telephone():
    """Génère un numéro de téléphone marocain réaliste"""
    prefixes = ["06", "07"]
    prefix = random.choice(prefixes)
    
    # Générer 8 chiffres supplémentaires au format xx-xx-xx-xx
    nums = [f"{random.randint(10, 99):02d}" for _ in range(4)]
    return f"{prefix}-{'-'.join(nums)}"

def generer_nom_client():
    """Génère un nom de client (mélange français/arabe)"""
    if random.random() < 0.6:  # 60% noms français
        prenom = random.choice(NOMS_FRANCAIS)
        nom = random.choice(NOMS_FAMILLE[:8])  # Noms français uniquement
    else:  # 40% noms arabes
        prenom = random.choice(NOMS_ARABES)
        nom = random.choice(NOMS_FAMILLE[8:])  # Noms arabes
    
    return f"{prenom} {nom}"

def generer_produit():
    """Génère un produit avec taille et couleur"""
    produit = random.choice(PRODUITS)
    taille = random.choice(produit["tailles"])
    couleur = random.choice(produit["couleurs"])
    
    produit_complet = f"{produit['nom']} - {taille}/{couleur}"
    return produit_complet, produit["prix"]

def generer_date_creation():
    """Génère une date de création réaliste (entre janvier 2023 et maintenant)"""
    start_date = datetime(2023, 1, 1)
    end_date = datetime.now()
    
    # Calculer la différence en jours
    days_diff = (end_date - start_date).days
    random_days = random.randint(0, days_diff)
    
    # Ajouter des heures/minutes aléatoires
    random_hours = random.randint(8, 22)  # Heures de travail
    random_minutes = random.randint(0, 59)
    random_seconds = random.randint(0, 59)
    
    date_creation = start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes, seconds=random_seconds)
    
    return date_creation.strftime("%Y-%m-%d %H:%M:%S")

def generer_motif_doublon(numero_original):
    """Génère un motif pour les doublons"""
    ligne_fictive = random.randint(1, 500)
    return f"{numero_original} (L{ligne_fictive})"

def generer_commandes(nb_commandes=573):
    """Génère le fichier CSV avec les commandes"""
    
    filename = "CMDInit_Generated.csv"
    commandes_existantes = set()  # Pour éviter les doublons de numéros
    
    # En-têtes CSV
    headers = [
        "N° Commande", "Statut", "Opérateur", "Client", "Téléphone", 
        "Adresse", "Ville", "Produit", "Quantité", "Prix", 
        "Date Création", "Motifs", "Modification"
    ]
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)
        
        for i in range(1, nb_commandes + 1):
            # Génération du numéro de commande
            if random.random() < 0.7:  # 70% format YCN
                numero_commande = f"YCN-{i:06d}"
            else:  # 30% format SHP
                numero_commande = f"SHP-{i:06d}"
            
            # Vérifier l'unicité
            while numero_commande in commandes_existantes:
                i += 1
                if random.random() < 0.7:
                    numero_commande = f"YCN-{i:06d}"
                else:
                    numero_commande = f"SHP-{i:06d}"
            
            commandes_existantes.add(numero_commande)
            
            # Statut avec probabilités
            statut = random.choices(STATUTS, weights=STATUTS_PROBABILITES)[0]
            
            # Opérateur (souvent vide)
            operateur = random.choice(OPERATEURS) if random.random() < 0.15 else ""
            
            # Client
            client = generer_nom_client()
            
            # Téléphone
            if statut == "Erronée" and random.random() < 0.3:
                # Quelques numéros invalides pour les commandes erronées
                telephone = f"01-{random.randint(10, 99)}-{random.randint(10, 99)}-{random.randint(10, 99)}-{random.randint(10, 99)}"
            else:
                telephone = generer_numero_telephone()
            
            # Adresse (souvent N/A)
            if random.random() < 0.8:
                adresse = "N/A"
            else:
                adresses = [
                    "12 Rue Al Qods", "5 Lot Ennakhil", "33 Rue Omar Ibn Khattab",
                    "8 Rue Al Massira", "21 Rue Moulay Ismail", "Rés. Al Amal 2, App 5",
                    "7 Rue El Harouchi", "Lotissement Chourouk", "15 Bd Hassan II"
                ]
                adresse = random.choice(adresses)
            
            # Ville
            ville = random.choice(VILLES_MAROC)
            
            # Produit et prix
            produit, prix = generer_produit()
            
            # Quantité (principalement 1)
            quantite = 1 if random.random() < 0.95 else random.randint(1, 3)
            
            # Date de création
            date_creation = generer_date_creation()
            
            # Motifs (pour les doublons)
            motifs = ""
            if statut == "Doublon":
                # Référencer une commande précédente fictive
                ref_commande = random.choice(list(commandes_existantes - {numero_commande})) if len(commandes_existantes) > 1 else "YCN-000001"
                motifs = generer_motif_doublon(ref_commande)
            elif statut == "Erronée":
                motifs_erreur = [
                    "Numéro de téléphone invalide",
                    "Adresse incomplète", 
                    "Client non joignable",
                    "Informations manquantes"
                ]
                motifs = random.choice(motifs_erreur)
            
            # Modification (vide)
            modification = ""
            
            # Écrire la ligne
            writer.writerow([
                numero_commande, statut, operateur, client, telephone,
                adresse, ville, produit, quantite, prix,
                date_creation, motifs, modification
            ])
            
            # Affichage du progrès
            if i % 50 == 0:
                print(f"✅ Générées: {i}/{nb_commandes} commandes")
    
    print(f"\n🎉 Fichier '{filename}' généré avec succès !")
    print(f"📊 Total: {nb_commandes} commandes")
    
    # Statistiques
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        commandes = list(reader)
        
        # Compter les statuts
        statuts_count = {}
        for cmd in commandes:
            statut = cmd['Statut']
            statuts_count[statut] = statuts_count.get(statut, 0) + 1
        
        print("\n📈 Statistiques:")
        for statut, count in statuts_count.items():
            pourcentage = (count / len(commandes)) * 100
            print(f"   • {statut}: {count} ({pourcentage:.1f}%)")
    
    return filename

if __name__ == "__main__":
    print("🚀 Générateur de commandes YZ-CMD")
    print("=" * 50)
    
    try:
        filename = generer_commandes(573)
        print(f"\n✅ Fichier disponible: {os.path.abspath(filename)}")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {e}") 