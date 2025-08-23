#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import EnumEtatCmd

def create_validee_state():
    """Créer l'état 'Validée' dans la base de données"""
    print("=== CRÉATION DE L'ÉTAT 'VALIDÉE' ===")
    
    # Vérifier si l'état existe déjà
    try:
        etat_validee = EnumEtatCmd.objects.get(libelle='Validée')
        print(f"L'état 'Validée' existe déjà (ID: {etat_validee.id})")
        return etat_validee
    except EnumEtatCmd.DoesNotExist:
        pass
    
    # Créer l'état "Validée"
    try:
        # Trouver l'ordre maximum actuel
        max_ordre = EnumEtatCmd.objects.aggregate(
            max_ordre=django.db.models.Max('ordre')
        )['max_ordre'] or 0
        
        etat_validee = EnumEtatCmd.objects.create(
            libelle='Validée',
            ordre=max_ordre + 1,
            couleur='#10B981'  # Vert pour indiquer la validation
        )
        
        print(f"État 'Validée' créé avec succès (ID: {etat_validee.id})")
        print(f"Libellé: {etat_validee.libelle}")
        print(f"Ordre: {etat_validee.ordre}")
        print(f"Couleur: {etat_validee.couleur}")
        
        return etat_validee
        
    except Exception as e:
        print(f"Erreur lors de la création de l'état 'Validée': {e}")
        return None

def list_all_states():
    """Lister tous les états existants"""
    print("\n=== ÉTATS EXISTANTS ===")
    etats = EnumEtatCmd.objects.all().order_by('ordre')
    
    for etat in etats:
        print(f"ID: {etat.id} | Libellé: {etat.libelle} | Ordre: {etat.ordre} | Couleur: {etat.couleur}")

if __name__ == '__main__':
    # Créer l'état "Validée"
    etat_validee = create_validee_state()
    
    # Lister tous les états
    list_all_states()
    
    if etat_validee:
        print(f"\n✅ État 'Validée' créé avec succès!")
    else:
        print(f"\n❌ Échec de la création de l'état 'Validée'")
