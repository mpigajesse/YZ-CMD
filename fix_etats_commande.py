#!/usr/bin/env python3
"""
Script simple pour vérifier et créer les états de commande nécessaires
sans utiliser django.setup() pour éviter les problèmes de dépendances
"""

import sqlite3
import os

def fix_etats_commande():
    """Vérifier et créer les états de commande dans la base SQLite"""
    
    # Chemin vers la base de données SQLite
    db_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
    
    if not os.path.exists(db_path):
        print("Base de donnees SQLite non trouvee")
        return
    
    print(f"Connexion a la base de donnees: {db_path}")
    
    try:
        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vérifier si la table EnumEtatCmd existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='commande_enumetatcmd'
        """)
        
        if not cursor.fetchone():
            print("Table commande_enumetatcmd non trouvee")
            return
        
        # Lister les états existants
        cursor.execute("SELECT id, libelle, ordre, couleur FROM commande_enumetatcmd ORDER BY ordre")
        etats_existants = cursor.fetchall()
        
        print("Etats existants dans la base:")
        for etat in etats_existants:
            print(f"   - {etat[2]}. {etat[1]} ({etat[3]})")
        
        # États requis
        etats_requis = [
            ('Non affectée', 1, '#6B7280'),
            ('Affectée', 2, '#3B82F6'),
            ('En cours de confirmation', 3, '#F59E0B'),
            ('Confirmée', 4, '#10B981'),
            ('Annulée', 5, '#EF4444'),
            ('Doublon', 6, '#EF4444'),
            ('Erronée', 7, '#F97316'),
            ('Retour Confirmation', 8, '#8B5CF6'),
            ('À imprimer', 9, '#06B6D4'),
            ('En préparation', 10, '#06B6D4'),
            ('Préparée', 11, '#14B8A6'),
            ('En cours de livraison', 12, '#F59E0B'),
            ('Livrée', 13, '#22C55E'),
        ]
        
        # Vérifier si l'état "Confirmée" existe
        confirmee_existe = any(etat[1] == 'Confirmée' for etat in etats_existants)
        
        if confirmee_existe:
            print("L'etat 'Confirmee' existe deja dans la base")
        else:
            print("L'etat 'Confirmee' n'existe pas dans la base")
            
            # Créer l'état "Confirmée"
            cursor.execute("""
                INSERT INTO commande_enumetatcmd (libelle, ordre, couleur)
                VALUES (?, ?, ?)
            """, ('Confirmée', 4, '#10B981'))
            
            print("Etat 'Confirmee' cree avec succes")
        
        # Vérifier et créer les autres états manquants
        libelles_existants = [etat[1] for etat in etats_existants]
        etats_crees = 0
        
        for libelle, ordre, couleur in etats_requis:
            if libelle not in libelles_existants:
                cursor.execute("""
                    INSERT INTO commande_enumetatcmd (libelle, ordre, couleur)
                    VALUES (?, ?, ?)
                """, (libelle, ordre, couleur))
                print(f"Etat cree: {libelle}")
                etats_crees += 1
        
        # Valider les changements
        conn.commit()
        
        print(f"\nResume: {etats_crees} nouveaux etats crees")
        
        # Vérification finale
        cursor.execute("SELECT libelle FROM commande_enumetatcmd WHERE libelle = 'Confirmée'")
        if cursor.fetchone():
            print("Verification finale: L'etat 'Confirmee' est bien present")
        else:
            print("Probleme: L'etat 'Confirmee' n'a pas pu etre cree")
        
    except Exception as e:
        print(f"Erreur: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_etats_commande()