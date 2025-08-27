#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import EnumEtatCmd

def create_emballee_state():
    """Créer l'état 'Emballée' dans la base de données"""
    print("=== CRÉATION DE L'ÉTAT 'EMBALLÉE' ===")
    
    # Vérifier si l'état existe déjà
    try:
        etat_emballee = EnumEtatCmd.objects.get(libelle='Emballée')
        print(f"L'état 'Emballée' existe déjà (ID: {etat_emballee.id})")
        return etat_emballee
    except EnumEtatCmd.DoesNotExist:
        pass
    
    # Créer l'état "Emballée"
    try:
        # Trouver l'ordre maximum actuel
        max_ordre = EnumEtatCmd.objects.aggregate(
            max_ordre=django.db.models.Max('ordre')
        )['max_ordre'] or 0
        
        etat_emballee = EnumEtatCmd.objects.create(
            libelle='Emballée',
            ordre=max_ordre + 1,
            couleur='#8B5CF6'  # Violet pour indiquer l'emballage
        )
        
        print(f"État 'Emballée' créé avec succès (ID: {etat_emballee.id})")
        print(f"Libellé: {etat_emballee.libelle}")
        print(f"Ordre: {etat_emballee.ordre}")
        print(f"Couleur: {etat_emballee.couleur}")
        
        return etat_emballee
        
    except Exception as e:
        print(f"Erreur lors de la création de l'état 'Emballée': {e}")
        return None

def list_preparation_states():
    """Lister les états liés à la préparation"""
    print("\n=== ÉTATS DE PRÉPARATION ===")
    etats_preparation = ['En préparation', 'Collectée', 'Emballée', 'Validée', 'Préparée']
    
    for libelle in etats_preparation:
        try:
            etat = EnumEtatCmd.objects.get(libelle=libelle)
            print(f"✅ {etat.libelle} (ID: {etat.id}, Ordre: {etat.ordre}, Couleur: {etat.couleur})")
        except EnumEtatCmd.DoesNotExist:
            print(f"❌ {libelle} - N'existe pas")

if __name__ == '__main__':
    # Créer l'état "Emballée"
    etat_emballee = create_emballee_state()
    
    # Lister les états de préparation
    list_preparation_states()
    
    if etat_emballee:
        print(f"\n✅ État 'Emballée' créé avec succès!")
    else:
        print(f"\n❌ Échec de la création de l'état 'Emballée'")
