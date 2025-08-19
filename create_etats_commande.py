#!/usr/bin/env python3
"""
Script pour créer les états de commande de base
Usage: python create_etats_commande.py
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import EnumEtatCmd

def create_etats_commande():
    """Crée les états de commande de base"""
    
    print("🚀 Création des états de commande de base...")
    
    # États de commande standards
    etats_de_base = [
        {'libelle': 'Non affectée', 'ordre': 1, 'couleur': '#6B7280'},
        {'libelle': 'Affectée', 'ordre': 2, 'couleur': '#3B82F6'},
        {'libelle': 'En cours de confirmation', 'ordre': 3, 'couleur': '#F59E0B'},
        {'libelle': 'Confirmée', 'ordre': 4, 'couleur': '#10B981'},
        {'libelle': 'Doublon', 'ordre': 5, 'couleur': '#EF4444'},
        {'libelle': 'Erronée', 'ordre': 6, 'couleur': '#F97316'},
        {'libelle': 'Retournée', 'ordre': 7, 'couleur': '#EF4444'},
        {'libelle': 'Livrée', 'ordre': 8, 'couleur': '#EF4444'},
        {'libelle': 'En preparation', 'ordre': 9, 'couleur': '#EF4444'},
        {'libelle': 'Preparée', 'ordre': 10, 'couleur': '#EF4444'},
    ]
    
    created_count = 0
    existing_count = 0
    
    for etat_data in etats_de_base:
        etat, created = EnumEtatCmd.objects.get_or_create(
            libelle=etat_data['libelle'],
            defaults={
                'ordre': etat_data['ordre'],
                'couleur': etat_data['couleur']
            }
        )
        
        if created:
            created_count += 1
            print(f"✅ État créé: {etat.libelle} (ordre: {etat.ordre})")
        else:
            existing_count += 1
            print(f"ℹ️  État existant: {etat.libelle}")
    
    print(f"\n📊 Résumé:")
    print(f"✅ États créés: {created_count}")
    print(f"ℹ️  États existants: {existing_count}")
    print(f"📈 Total états en base: {EnumEtatCmd.objects.count()}")
    
    # Afficher tous les états
    print(f"\n📋 Liste des états dans la base:")
    etats = EnumEtatCmd.objects.all().order_by('ordre')
    for etat in etats:
        print(f"   • {etat.ordre}. {etat.libelle} ({etat.couleur})")

if __name__ == "__main__":
    create_etats_commande() 