#!/usr/bin/env python
"""
Script d'importation des régions et villes depuis le fichier CSV
Usage: python import_regions_villes.py
"""

import os
import sys
import django
import csv
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from parametre.models import Region, Ville

def clean_tarif(tarif_str):
    """Nettoie et convertit le tarif en float"""
    if not tarif_str or tarif_str.strip() == '' or tarif_str.strip() == 'DHs':
        return 0.0
    
    # Supprime les caractères non numériques sauf le point
    cleaned = ''.join(c for c in tarif_str if c.isdigit() or c == '.')
    
    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0

def clean_frequence(frequence_str):
    """Nettoie la fréquence de livraison"""
    if not frequence_str or frequence_str.strip() == '':
        return 'Non défini'
    
    # Mapping des fréquences communes
    frequence_mapping = {
        'Chaque Jour': 'Quotidien',
        '24H': '24H',
        '24H-48H': '24H-48H',
        '48H': '48H',
        '12H-24H': '12H-24H',
        'JOUR+1': 'J+1',
        'JOURS+1': 'J+1',
        'JOURS +1': 'J+1',
    }
    
    # Vérifie les mappings exacts
    for key, value in frequence_mapping.items():
        if frequence_str.strip() == key:
            return value
    
    # Pour les fréquences avec des jours spécifiques, on garde tel quel
    return frequence_str.strip()

def import_data():
    """Importe les données depuis le fichier CSV"""
    
    print("🚀 Début de l'importation des régions et villes...")
    
    # Compteurs
    regions_created = 0
    villes_created = 0
    errors = 0
    
    try:
        with open('CMD_REGION - CMD_REGION.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row_num, row in enumerate(reader, start=2):  # Start=2 car ligne 1 = headers
                try:
                    # Extraction des données
                    ville_nom = row['Ville'].strip()
                    region_nom = row['Region'].strip()
                    frequence = clean_frequence(row['Delai'])
                    tarif = clean_tarif(row['Tarif'])
                    
                    # Skip les lignes vides
                    if not ville_nom or not region_nom:
                        print(f"⚠️  Ligne {row_num}: Ville ou région vide - ignorée")
                        continue
                    
                    # Créer ou récupérer la région
                    region, region_created = Region.objects.get_or_create(
                        nom_region=region_nom
                    )
                    
                    if region_created:
                        regions_created += 1
                        print(f"✅ Région créée: {region_nom}")
                    
                    # Créer ou récupérer la ville
                    ville, ville_created = Ville.objects.get_or_create(
                        nom=ville_nom,
                        region=region,
                        defaults={
                            'frais_livraison': tarif,
                            'frequence_livraison': frequence
                        }
                    )
                    
                    if ville_created:
                        villes_created += 1
                        print(f"✅ Ville créée: {ville_nom} ({region_nom}) - {tarif}DH - {frequence}")
                    else:
                        # Mettre à jour si la ville existe déjà
                        ville.frais_livraison = tarif
                        ville.frequence_livraison = frequence
                        ville.save()
                        print(f"🔄 Ville mise à jour: {ville_nom}")
                
                except Exception as e:
                    errors += 1
                    print(f"❌ Erreur ligne {row_num}: {str(e)}")
                    print(f"   Données: {row}")
                    continue
    
    except FileNotFoundError:
        print("❌ Fichier 'CMD_REGION - CMD_REGION.csv' non trouvé!")
        print("   Assurez-vous que le fichier est dans le même répertoire que ce script.")
        return
    
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {str(e)}")
        return
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DE L'IMPORTATION")
    print("="*60)
    print(f"✅ Régions créées: {regions_created}")
    print(f"✅ Villes créées: {villes_created}")
    print(f"❌ Erreurs: {errors}")
    print(f"📈 Total régions en base: {Region.objects.count()}")
    print(f"📈 Total villes en base: {Ville.objects.count()}")
    
    # Affichage des régions créées
    if regions_created > 0:
        print("\n🌍 RÉGIONS CRÉÉES:")
        for region in Region.objects.all().order_by('nom_region'):
            ville_count = region.villes.count()
            print(f"   • {region.nom_region} ({ville_count} villes)")
    
    print("\n🎉 Importation terminée avec succès!")

def show_stats():
    """Affiche les statistiques de la base de données"""
    print("\n" + "="*60)
    print("📊 STATISTIQUES DE LA BASE DE DONNÉES")
    print("="*60)
    
    regions = Region.objects.all().order_by('nom_region')
    
    for region in regions:
        villes = region.villes.all().order_by('nom')
        tarif_moyen = sum(v.frais_livraison for v in villes) / len(villes) if villes else 0
        
        print(f"\n🌍 {region.nom_region}")
        print(f"   📍 Nombre de villes: {villes.count()}")
        print(f"   💰 Tarif moyen: {tarif_moyen:.1f} DH")
        
        # Affiche quelques villes exemple
        if villes.count() > 0:
            print(f"   🏙️  Villes principales:")
            for ville in villes[:5]:  # Affiche les 5 premières
                print(f"      • {ville.nom} - {ville.frais_livraison}DH - {ville.frequence_livraison}")
            
            if villes.count() > 5:
                print(f"      ... et {villes.count() - 5} autres villes")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'stats':
        show_stats()
    else:
        import_data()
        show_stats() 