#!/usr/bin/env python
"""
Script d'importation des articles depuis le fichier CSV
Usage: python import_articles.py
"""

import os
import sys
import django
import csv
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from article.models import Article

def clean_price(price_str):
    """Nettoie et convertit le prix en float"""
    if not price_str or price_str.strip() == '':
        return 0.0
    
    # Supprime les caractères non numériques sauf le point
    cleaned = ''.join(c for c in str(price_str) if c.isdigit() or c == '.')
    
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def clean_quantity(qty_str):
    """Nettoie et convertit la quantité en int"""
    if not qty_str or qty_str.strip() == '':
        return 0
    
    # Supprime les caractères non numériques
    cleaned = ''.join(c for c in str(qty_str) if c.isdigit())
    
    try:
        return int(cleaned) if cleaned else 0
    except ValueError:
        return 0

def determine_category(name):
    """Détermine la catégorie basée sur le nom du produit"""
    name_upper = name.upper()
    
    if 'SAB' in name_upper and 'FEM' in name_upper:
        return 'Chaussures Femme'
    elif 'SAB' in name_upper and 'HOM' in name_upper:
        return 'Chaussures Homme'
    elif 'SAB' in name_upper:
        return 'Chaussures'
    elif 'BASKET' in name_upper:
        return 'Baskets'
    elif 'SANDAL' in name_upper:
        return 'Sandales'
    else:
        return 'Chaussures'

def import_articles():
    """Importe les articles depuis le fichier CSV"""
    
    print("🚀 Début de l'importation des articles...")
    
    # Compteurs
    articles_created = 0
    articles_updated = 0
    errors = 0
    
    try:
        with open('CMD_PRODUCT - CMD_PRODUCT.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row_num, row in enumerate(reader, start=2):  # Start=2 car ligne 1 = headers
                try:
                    # Extraction des données
                    reference = row['reference'].strip()
                    nom = row['name'].strip()
                    couleur = row['color'].strip()
                    pointure = row['size'].strip()
                    prix = clean_price(row['price'])
                    quantite = clean_quantity(row['quantity'])
                    
                    # Skip les lignes vides
                    if not nom or not couleur or not pointure:
                        print(f"⚠️  Ligne {row_num}: Données manquantes - ignorée")
                        continue
                    
                    # Déterminer la catégorie
                    categorie = determine_category(nom)
                    
                    # Créer ou mettre à jour l'article
                    article, created = Article.objects.get_or_create(
                        reference=reference,  # Utiliser la référence comme identifiant unique
                        defaults={
                            'nom': nom,
                            'couleur': couleur,
                            'pointure': pointure,
                            'prix_unitaire': prix,
                            'qte_disponible': quantite,
                            'categorie': categorie,
                            'actif': True
                        }
                    )
                    
                    if created:
                        articles_created += 1
                        print(f"✅ Article créé: {reference} - {nom} - {couleur} - {pointure} - {prix}DH (Stock: {quantite})")
                    else:
                        # Mettre à jour tous les champs
                        article.nom = nom
                        article.couleur = couleur
                        article.pointure = pointure
                        article.prix_unitaire = prix
                        article.qte_disponible = quantite
                        article.categorie = categorie
                        article.save()
                        articles_updated += 1
                        print(f"🔄 Article mis à jour: {reference} - {nom} - {couleur} - {pointure} - {prix}DH (Stock: {quantite})")
                
                except Exception as e:
                    errors += 1
                    print(f"❌ Erreur ligne {row_num}: {str(e)}")
                    print(f"   Données: {row}")
                    continue
    
    except FileNotFoundError:
        print("❌ Fichier 'CMD_PRODUCT - CMD_PRODUCT.csv' non trouvé!")
        print("   Assurez-vous que le fichier est dans le même répertoire que ce script.")
        return
    
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {str(e)}")
        return
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DE L'IMPORTATION")
    print("="*60)
    print(f"✅ Articles créés: {articles_created}")
    print(f"🔄 Articles mis à jour: {articles_updated}")
    print(f"❌ Erreurs: {errors}")
    print(f"📈 Total articles en base: {Article.objects.count()}")
    
    # Statistiques par catégorie
    print("\n📦 RÉPARTITION PAR CATÉGORIE:")
    categories = Article.objects.values('categorie').distinct().order_by('categorie')
    for cat in categories:
        count = Article.objects.filter(categorie=cat['categorie']).count()
        print(f"   • {cat['categorie']}: {count} articles")
    
    print("\n🎉 Importation terminée avec succès!")

def show_stats():
    """Affiche les statistiques des articles"""
    print("\n" + "="*60)
    print("📊 STATISTIQUES DES ARTICLES")
    print("="*60)
    
    total_articles = Article.objects.count()
    articles_actifs = Article.objects.filter(actif=True).count()
    articles_disponibles = Article.objects.filter(qte_disponible__gt=0, actif=True).count()
    
    print(f"📦 Total articles: {total_articles}")
    print(f"✅ Articles actifs: {articles_actifs}")
    print(f"📈 Articles en stock: {articles_disponibles}")
    
    # Statistiques par catégorie
    print("\n📂 PAR CATÉGORIE:")
    categories = Article.objects.values('categorie').distinct().order_by('categorie')
    for cat in categories:
        articles = Article.objects.filter(categorie=cat['categorie'])
        count = articles.count()
        stock_total = sum(a.qte_disponible for a in articles)
        prix_moyen = sum(a.prix_unitaire for a in articles) / count if count > 0 else 0
        
        print(f"   • {cat['categorie']}: {count} articles, Stock: {stock_total}, Prix moyen: {prix_moyen:.0f}DH")
    
    # Statistiques par couleur
    print("\n🎨 PAR COULEUR:")
    couleurs = Article.objects.values('couleur').distinct().order_by('couleur')
    for couleur in couleurs:
        count = Article.objects.filter(couleur=couleur['couleur']).count()
        print(f"   • {couleur['couleur']}: {count} articles")
    
    # Articles les plus chers
    print("\n💰 TOP 5 ARTICLES LES PLUS CHERS:")
    articles_chers = Article.objects.filter(actif=True).order_by('-prix_unitaire')[:5]
    for article in articles_chers:
        print(f"   • {article.nom} - {article.couleur} - {article.pointure} - {article.prix_unitaire}DH")
    
    # Articles en rupture de stock
    rupture_stock = Article.objects.filter(qte_disponible=0, actif=True).count()
    print(f"\n⚠️  Articles en rupture de stock: {rupture_stock}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'stats':
        show_stats()
    else:
        import_articles()
        show_stats() 