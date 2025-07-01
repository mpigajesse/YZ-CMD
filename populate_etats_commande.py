#!/usr/bin/env python3
"""
Script pour peupler la base de données avec tous les états de commande requis
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import EnumEtatCmd

def populate_etats_commande():
    """Peuple la base de données avec tous les états de commande"""
    
    # Définition des états avec leurs propriétés
    etats_data = [
        # États initiaux
        {'libelle': 'Reçue', 'ordre': 1, 'couleur': '#3B82F6'},  # Bleu
        {'libelle': 'Non affectée', 'ordre': 2, 'couleur': '#EAB308'},  # Jaune
        {'libelle': 'Affectée', 'ordre': 3, 'couleur': '#10B981'},  # Vert
        
        # États de confirmation
        {'libelle': 'En cours de confirmation', 'ordre': 4, 'couleur': '#6366F1'},  # Indigo
        {'libelle': 'Confirmée', 'ordre': 5, 'couleur': '#059669'},  # Emerald
        
        # États problématiques
        {'libelle': 'Erronée', 'ordre': 6, 'couleur': '#DC2626'},  # Rouge
        {'libelle': 'Doublon', 'ordre': 7, 'couleur': '#EA580C'},  # Orange
        
        # États de préparation
        {'libelle': 'En cours de préparation', 'ordre': 8, 'couleur': '#0891B2'},  # Cyan
        {'libelle': 'Préparée', 'ordre': 9, 'couleur': '#0D9488'},  # Teal
        
        # États de livraison
        {'libelle': 'En cours de livraison', 'ordre': 10, 'couleur': '#7C3AED'},  # Purple
        {'libelle': 'Livrée', 'ordre': 11, 'couleur': '#16A34A'},  # Green foncé
        {'libelle': 'Retournée', 'ordre': 12, 'couleur': '#6B7280'},  # Gris
    ]
    
    created_count = 0
    updated_count = 0
    
    print("🔄 Mise à jour des états de commande...")
    
    for etat_data in etats_data:
        etat, created = EnumEtatCmd.objects.get_or_create(
            libelle=etat_data['libelle'],
            defaults={
                'ordre': etat_data['ordre'],
                'couleur': etat_data['couleur']
            }
        )
        
        if created:
            created_count += 1
            print(f"✅ Créé: {etat.libelle} (ordre: {etat.ordre}, couleur: {etat.couleur})")
        else:
            # Mettre à jour l'ordre et la couleur si nécessaire
            if etat.ordre != etat_data['ordre'] or etat.couleur != etat_data['couleur']:
                etat.ordre = etat_data['ordre']
                etat.couleur = etat_data['couleur']
                etat.save()
                updated_count += 1
                print(f"🔄 Mis à jour: {etat.libelle} (ordre: {etat.ordre}, couleur: {etat.couleur})")
            else:
                print(f"⏭️  Déjà existant: {etat.libelle}")
    
    print(f"\n📊 Résumé:")
    print(f"   • États créés: {created_count}")
    print(f"   • États mis à jour: {updated_count}")
    print(f"   • Total d'états: {EnumEtatCmd.objects.count()}")
    
    # Afficher tous les états pour vérification
    print(f"\n📋 Liste complète des états:")
    for etat in EnumEtatCmd.objects.all().order_by('ordre'):
        print(f"   {etat.ordre:2d}. {etat.libelle} ({etat.couleur})")

def main():
    """Fonction principale"""
    try:
        populate_etats_commande()
        print("\n✅ Population des états de commande terminée avec succès!")
    except Exception as e:
        print(f"\n❌ Erreur lors de la population: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
