#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import Operation, Commande, Operateur, EtatCommande
from django.db.models import Q
from django.utils import timezone

def create_retroactive_operations():
    print("=== CRÉATION D'OPÉRATIONS RÉTROACTIVES ===")
    
    # Trouver toutes les commandes en préparation qui n'ont pas d'opération d'affectation
    commandes_en_prepa = Commande.objects.filter(
        etats__enum_etat__libelle__in=['À imprimer', 'En préparation', 'Collectée', 'Emballée'],
        etats__date_fin__isnull=True
    ).distinct()
    
    operations_created = 0
    
    for commande in commandes_en_prepa:
        # Vérifier s'il y a déjà une opération d'affectation pour cette commande
        existing_operation = Operation.objects.filter(
            commande=commande,
            type_operation__in=['AFFECTATION_SUPERVISION', 'AFFECTATION_ADMIN']
        ).first()
        
        if existing_operation:
            print(f"Commande {commande.id_yz}: Opération d'affectation déjà existante")
            continue
        
        # Trouver l'état de préparation actuel
        etat_prepa = commande.etats.filter(
            enum_etat__libelle__in=['À imprimer', 'En préparation', 'Collectée', 'Emballée'],
            date_fin__isnull=True
        ).first()
        
        if not etat_prepa or not etat_prepa.operateur:
            print(f"Commande {commande.id_yz}: Pas d'état de préparation ou d'opérateur trouvé")
            continue
        
        # Trouver qui a créé cet état (probablement un admin ou superviseur)
        # Chercher dans l'historique des états pour trouver qui a affecté cette commande
        etat_confirm = commande.etats.filter(
            enum_etat__libelle='Confirmée'
        ).order_by('-date_debut').first()
        
        if etat_confirm and etat_confirm.operateur:
            # Si l'état Confirmée a un opérateur, c'est probablement celui qui a fait l'affectation
            operateur_affecteur = etat_confirm.operateur
        else:
            # Sinon, on suppose que c'est un admin par défaut
            operateur_affecteur = Operateur.objects.filter(type_operateur='ADMIN').first()
        
        if not operateur_affecteur:
            print(f"Commande {commande.id_yz}: Impossible de déterminer l'opérateur d'affectation")
            continue
        
        # Créer l'opération d'affectation
        if operateur_affecteur.type_operateur == 'SUPERVISEUR_PREPARATION':
            type_operation = 'AFFECTATION_SUPERVISION'
            conclusion = f"Commande affectée à {etat_prepa.operateur.nom_complet} par le superviseur de préparation (opération rétroactive)."
        else:
            type_operation = 'AFFECTATION_ADMIN'
            conclusion = f"Commande affectée à {etat_prepa.operateur.nom_complet} par l'administrateur (opération rétroactive)."
        
        Operation.objects.create(
            commande=commande,
            type_operation=type_operation,
            operateur=operateur_affecteur,
            conclusion=conclusion,
            date_operation=etat_prepa.date_debut or timezone.now()
        )
        
        operations_created += 1
        print(f"Commande {commande.id_yz}: Opération {type_operation} créée par {operateur_affecteur.nom_complet}")
    
    print(f"\n=== RÉSULTAT ===")
    print(f"Opérations créées: {operations_created}")

if __name__ == "__main__":
    create_retroactive_operations()
