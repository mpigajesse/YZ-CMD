#!/usr/bin/env python3
"""
Script d'importation des commandes depuis le fichier CSV généré
Usage: python import_commandes_csv.py
"""

import os
import sys
import django
import csv
import re
from datetime import datetime
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from client.models import Client
from commande.models import Commande, Panier, EtatCommande, EnumEtatCmd
from article.models import Article
from parametre.models import Ville, Region, Operateur
from django.db import transaction
from django.utils import timezone

def clean_phone_number(phone_str):
    """Nettoie le numéro de téléphone"""
    if not phone_str:
        return ""
    
    # Supprimer les caractères non numériques sauf les tirets
    phone_clean = re.sub(r'[^\d\-]', '', str(phone_str))
    
    # S'assurer qu'il commence par 06 ou 07 pour les numéros marocains
    if phone_clean.startswith('06') or phone_clean.startswith('07'):
        return phone_clean
    
    return phone_str

def parse_client_name(client_str):
    """Parse le nom du client pour extraire prénom et nom"""
    if not client_str:
        return "", ""
    
    # Nettoyer la chaîne
    client_clean = client_str.strip()
    
    # Séparer par espaces
    parts = client_clean.split()
    
    if len(parts) == 0:
        return "", ""
    elif len(parts) == 1:
        return parts[0], ""
    else:
        # Premier mot = prénom, reste = nom
        prenom = parts[0]
        nom = " ".join(parts[1:])
        return prenom, nom

def parse_product_info(product_str):
    """Parse l'information produit pour extraire nom, pointure et couleur"""
    if not product_str:
        return "", "", ""
    
    # Format attendu: "NOM_PRODUIT - POINTURE/COULEUR"
    # Exemple: "ESP HOM YZ650 - 42/أسود أبيض / noir blanc"
    
    try:
        # Séparer par le tiret principal
        if ' - ' in product_str:
            nom_partie, taille_couleur = product_str.split(' - ', 1)
            nom = nom_partie.strip()
            
            # Séparer la taille de la couleur par le premier "/"
            if '/' in taille_couleur:
                pointure = taille_couleur.split('/')[0].strip()
                couleur = '/'.join(taille_couleur.split('/')[1:]).strip()
            else:
                pointure = taille_couleur.strip()
                couleur = ""
                
        else:
            # Format non standard, prendre tout comme nom
            nom = product_str.strip()
            pointure = ""
            couleur = ""
            
        return nom, pointure, couleur
        
    except Exception as e:
        print(f"Erreur parsing produit '{product_str}': {e}")
        return product_str, "", ""

def get_or_create_region_ville(ville_name):
    """Crée ou récupère une ville (avec région par défaut)"""
    if not ville_name:
        ville_name = "Non spécifiée"
    
    # Créer une région par défaut si nécessaire
    region, _ = Region.objects.get_or_create(
        nom_region="Maroc",
        defaults={'nom_region': "Maroc"}
    )
    
    # Créer ou récupérer la ville
    ville, created = Ville.objects.get_or_create(
        nom=ville_name,
        region=region,
        defaults={
            'frais_livraison': 25.0,  # Frais par défaut
            'frequence_livraison': 'Quotidienne'
        }
    )
    
    if created:
        print(f"  📍 Ville créée: {ville_name}")
    
    return ville

def get_or_create_client(nom_complet, telephone):
    """Crée ou récupère un client"""
    prenom, nom = parse_client_name(nom_complet)
    telephone_clean = clean_phone_number(telephone)
    
    # Chercher par téléphone d'abord (clé unique)
    try:
        client = Client.objects.get(numero_tel=telephone_clean)
        return client, False
    except Client.DoesNotExist:
        pass
    
    # Créer nouveau client
    client = Client.objects.create(
        prenom=prenom,
        nom=nom,
        numero_tel=telephone_clean,
        is_active=True
    )
    
    return client, True

def get_or_create_article(nom, pointure, couleur, prix):
    """Crée ou récupère un article"""
    if not nom:
        nom = "Produit inconnu"
    if not pointure:
        pointure = "N/A"
    if not couleur:
        couleur = "N/A"
    
    # Déterminer la catégorie basée sur le nom
    nom_upper = nom.upper()
    if 'FEM' in nom_upper:
        categorie = 'Chaussures Femme'
    elif 'HOM' in nom_upper:
        categorie = 'Chaussures Homme'
    elif 'SDL' in nom_upper:
        categorie = 'Sandales'
    elif 'ESP' in nom_upper:
        categorie = 'Espadrilles'
    else:
        categorie = 'Chaussures'
    
    # Chercher l'article existant
    try:
        article = Article.objects.get(nom=nom, couleur=couleur, pointure=pointure)
        return article, False
    except Article.DoesNotExist:
        pass
    
    # Créer nouvel article
    article = Article.objects.create(
        nom=nom,
        couleur=couleur,
        pointure=pointure,
        prix_unitaire=prix,
        categorie=categorie,
        qte_disponible=100,  # Stock par défaut
        actif=True
    )
    
    return article, True

def get_or_create_etat_commande(statut):
    """Crée ou récupère un état de commande"""
    # Mapping des statuts CSV vers les états système
    statut_mapping = {
        'Non affectée': 'non_affectee',
        'Doublon': 'doublon',
        'Erronée': 'erronnee',
        'Affectée': 'affectee',
        'Confirmée': 'confirmee'
    }
    
    statut_clean = statut_mapping.get(statut, 'non_affectee')
    
    # Créer ou récupérer l'état
    etat, created = EnumEtatCmd.objects.get_or_create(
        libelle=statut,
        defaults={
            'ordre': 1,
            'couleur': '#6B7280'
        }
    )
    
    if created:
        print(f"  📋 État créé: {statut}")
    
    return etat

def parse_date(date_str):
    """Parse la date de création avec timezone"""
    if not date_str:
        return timezone.now()
    
    try:
        # Format: "2023-03-25 17:09:35"
        naive_dt = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")
        return timezone.make_aware(naive_dt)
    except Exception:
        try:
            # Format alternatif: "27/04/2025"
            naive_dt = datetime.strptime(date_str.strip(), "%d/%m/%Y")
            return timezone.make_aware(naive_dt)
        except Exception:
            print(f"  ⚠️  Date non parsable: {date_str}, utilisation de maintenant")
            return timezone.now()

def import_commandes(start_from_line=2):
    """Importe les commandes depuis le fichier CSV"""
    
    print(f"🚀 Début de l'importation des commandes depuis CMDInit_Generated.csv...")
    if start_from_line > 2:
        print(f"📍 Reprise à partir de la ligne {start_from_line}")
    
    # Compteurs
    commandes_created = 0
    commandes_skipped = 0
    clients_created = 0
    articles_created = 0
    errors = 0
    
    filename = 'CMDInit_Generated.csv'
    
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            batch_size = 50
            batch_count = 0
            
            for row_num, row in enumerate(reader, start=2):
                # Skip les lignes jusqu'à la ligne de reprise
                if row_num < start_from_line:
                    continue
                    
                try:
                    # Extraction des données
                    numero_commande = row['N° Commande'].strip()
                    statut = row['Statut'].strip()
                    operateur_name = row['Opérateur'].strip()
                    client_name = row['Client'].strip()
                    telephone = row['Téléphone'].strip()
                    adresse = row['Adresse'].strip() if row['Adresse'].strip() != 'N/A' else 'Adresse non spécifiée'
                    ville_name = row['Ville'].strip()
                    produit = row['Produit'].strip()
                    quantite = int(row['Quantité']) if row['Quantité'].strip() else 1
                    prix = float(row['Prix']) if row['Prix'].strip() else 0.0
                    date_creation_str = row['Date Création'].strip()
                    motifs = row['Motifs'].strip()
                    
                    # Skip les lignes vides ou invalides
                    if not numero_commande or not client_name or not telephone:
                        print(f"⚠️  Ligne {row_num}: Données manquantes - ignorée")
                        commandes_skipped += 1
                        continue
                    
                    # Vérifier si la commande existe déjà
                    if Commande.objects.filter(num_cmd=numero_commande).exists():
                        print(f"⚠️  Commande {numero_commande} existe déjà - ignorée")
                        commandes_skipped += 1
                        continue
                    
                    # Traitement avec transaction atomique individuelle
                    with transaction.atomic():
                        try:
                            # 1. Créer ou récupérer le client
                            client, client_created = get_or_create_client(client_name, telephone)
                            if client_created:
                                clients_created += 1
                            
                            # 2. Créer ou récupérer la ville
                            ville = get_or_create_region_ville(ville_name)
                            
                            # 3. Parser et créer l'article
                            nom_produit, pointure, couleur = parse_product_info(produit)
                            article, article_created = get_or_create_article(nom_produit, pointure, couleur, prix)
                            if article_created:
                                articles_created += 1
                            
                            # 4. Parse la date
                            date_creation = parse_date(date_creation_str)
                            
                            # 5. Créer la commande
                            total_commande = prix * quantite
                            
                            commande = Commande.objects.create(
                                num_cmd=numero_commande,
                                client=client,
                                ville=ville,
                                adresse=adresse,
                                total_cmd=total_commande,
                                date_cmd=date_creation.date(),
                                date_creation=date_creation,
                                ville_init=ville_name,
                                produit_init=produit,
                                motif_annulation=motifs if motifs else None,
                                origine='SYNC'
                            )
                            
                            # 6. Créer le panier (article dans la commande)
                            Panier.objects.create(
                                commande=commande,
                                article=article,
                                quantite=quantite,
                                sous_total=total_commande
                            )
                            
                            # 7. Créer l'état de commande
                            etat_enum = get_or_create_etat_commande(statut)
                            EtatCommande.objects.create(
                                commande=commande,
                                enum_etat=etat_enum,
                                date_debut=date_creation,
                                commentaire=motifs if motifs else None
                            )
                            
                            commandes_created += 1
                            batch_count += 1
                            
                            if batch_count % batch_size == 0:
                                print(f"✅ Batch traité: {batch_count} commandes créées")
                            else:
                                print(f"✅ Commande créée: {numero_commande} - {client_name} - {total_commande}DH")
                                
                        except Exception as db_error:
                            print(f"❌ Erreur DB ligne {row_num}: {str(db_error)}")
                            print(f"   Commande: {numero_commande}")
                            errors += 1
                            # Transaction rollback automatique
                            continue
                        
                except Exception as e:
                    errors += 1
                    print(f"❌ Erreur générale ligne {row_num}: {str(e)}")
                    print(f"   Données: {row}")
                    continue
    
    except FileNotFoundError:
        print(f"❌ Fichier '{filename}' non trouvé!")
        print("   Assurez-vous que le fichier est dans le même répertoire que ce script.")
        return
    
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {str(e)}")
        return
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DE L'IMPORTATION")
    print("="*70)
    print(f"✅ Commandes créées: {commandes_created}")
    print(f"⏭️  Commandes ignorées: {commandes_skipped}")
    print(f"👥 Nouveaux clients: {clients_created}")
    print(f"📦 Nouveaux articles: {articles_created}")
    print(f"❌ Erreurs: {errors}")
    print(f"📈 Total commandes en base: {Commande.objects.count()}")
    print(f"📈 Total clients en base: {Client.objects.count()}")
    print(f"📈 Total articles en base: {Article.objects.count()}")

def show_stats():
    """Affiche les statistiques des commandes"""
    print("\n" + "="*70)
    print("📊 STATISTIQUES DES COMMANDES")
    print("="*70)
    
    total_commandes = Commande.objects.count()
    total_clients = Client.objects.count()
    total_articles = Article.objects.count()
    
    print(f"📦 Total commandes: {total_commandes}")
    print(f"👥 Total clients: {total_clients}")
    print(f"🛍️  Total articles: {total_articles}")
    
    # Statistiques par statut
    print("\n📋 PAR STATUT:")
    etats = EnumEtatCmd.objects.all()
    for etat in etats:
        count = EtatCommande.objects.filter(enum_etat=etat, date_fin__isnull=True).count()
        if count > 0:
            print(f"   • {etat.libelle}: {count} commandes")
    
    # Statistiques par ville
    print("\n🏙️ TOP 10 VILLES:")
    from django.db.models import Count
    villes_stats = Commande.objects.values('ville__nom').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    for ville_stat in villes_stats:
        print(f"   • {ville_stat['ville__nom']}: {ville_stat['count']} commandes")
    
    # Statistiques financières
    from django.db.models import Sum
    total_ca = Commande.objects.aggregate(total=Sum('total_cmd'))['total'] or 0
    ca_moyen = total_ca / total_commandes if total_commandes > 0 else 0
    
    print(f"\n💰 CHIFFRE D'AFFAIRES:")
    print(f"   • Total: {total_ca:.2f} DH")
    print(f"   • Panier moyen: {ca_moyen:.2f} DH")
    
    # Articles les plus vendus
    print("\n🔥 TOP 5 ARTICLES LES PLUS VENDUS:")
    from django.db.models import Sum
    articles_stats = Panier.objects.values('article__nom', 'article__couleur', 'article__pointure').annotate(
        total_vendu=Sum('quantite')
    ).order_by('-total_vendu')[:5]
    
    for article_stat in articles_stats:
        print(f"   • {article_stat['article__nom']} - {article_stat['article__couleur']} - {article_stat['article__pointure']}: {article_stat['total_vendu']} unités")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'stats':
            show_stats()
        elif sys.argv[1] == 'continue' and len(sys.argv) > 2:
            try:
                start_line = int(sys.argv[2])
                import_commandes(start_line)
                show_stats()
            except ValueError:
                print("❌ Numéro de ligne invalide. Usage: python import_commandes_csv.py continue <ligne>")
        else:
            print("Usage:")
            print("  python import_commandes_csv.py                    # Import complet")
            print("  python import_commandes_csv.py continue <ligne>   # Reprendre à partir d'une ligne")
            print("  python import_commandes_csv.py stats              # Afficher seulement les stats")
    else:
        import_commandes()
        show_stats() 