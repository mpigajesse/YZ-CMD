import os
import sys
import django
from django.db import transaction

def setup_django():
    """Initialise l'environnement Django pour exécuter le script."""
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

# --- Fonctions principales ---

def reinitialiser_donnees_geographiques():
    """
    Script pour réinitialiser complètement les données de Villes et Régions.
    1. Détache les commandes des villes pour éviter la suppression en cascade.
    2. Supprime toutes les villes et régions existantes.
    3. Réimporte les données propres depuis le fichier CSV via le script d'importation.
    """
    print("--- DÉBUT DE LA RÉINITIALISATION COMPLÈTE DES DONNÉES GÉOGRAPHIQUES ---")
    print("\nATTENTION : Cette opération est irréversible et va modifier votre base de données.")
    print("Elle est conçue pour être exécutée UNE SEULE FOIS pour nettoyer la base.")

    from commande.models import Commande
    from parametre.models import Ville, Region
    # Importe la fonction spécifique depuis votre script existant
    from import_regions_villes import import_data as importer_donnees_csv

    # Compte les objets existants pour le résumé
    command_count = Commande.objects.count()
    ville_count = Ville.objects.count()
    region_count = Region.objects.count()

    print("\n--- ÉTAT ACTUEL DE LA BASE DE DONNÉES ---")
    print(f"- {command_count} commandes")
    print(f"- {ville_count} villes")
    print(f"- {region_count} régions")

    print("\n--- PLAN DE L'OPÉRATION ---")
    print("1. Le champ 'ville' de TOUTES les commandes sera mis à NULL pour éviter la perte de données.")
    print("2. TOUTES les villes et TOUTES les régions seront SUPPRIMÉES.")
    print("3. Les villes et régions seront rechargées à partir du fichier 'CMD_REGION - CMD_REGION.csv'.")
    print("-" * 60)
    
    # Demande de confirmation claire et explicite à l'utilisateur
    confirm = input("Êtes-vous absolument sûr de vouloir continuer ? Cette action est définitive. (o/N) : ").strip().lower()
    if confirm != 'o':
        print("\n--- ❌ Opération annulée par l'utilisateur. ---")
        return

    try:
        # Utilise une transaction pour s'assurer que toute l'opération réussit ou échoue d'un bloc
        with transaction.atomic():
            print("\n--- 🚀 Lancement de la réinitialisation... ---")
            
            # Étape 1: Détacher toutes les commandes de leurs villes
            print("\nÉtape 1/3: Détachement des commandes pour préserver les données...")
            updated_count = Commande.objects.update(ville=None)
            print(f"-> {updated_count} commandes ont été détachées de leur ville. Aucune commande ne sera perdue.")

            # Étape 2: Supprimer toutes les villes et régions
            print("\nÉtape 2/3: Suppression des anciennes villes et régions...")
            villes_deleted_count, _ = Ville.objects.all().delete()
            regions_deleted_count, _ = Region.objects.all().delete()
            print(f"-> {villes_deleted_count} villes supprimées.")
            print(f"-> {regions_deleted_count} régions supprimées.")

            # Étape 3: Réimporter les données propres depuis le CSV
            print("\nÉtape 3/3: Réimportation des données propres depuis le fichier CSV...")
            importer_donnees_csv()  # Appel de la fonction importée

        print("\n" + "="*60)
        print("--- ✅ RÉINITIALISATION TERMINÉE AVEC SUCCÈS ! ---")
        print("Vos tables de villes et régions ont été purgées et rechargées proprement.")
        print("Le problème de données invalides et de doublons est maintenant définitivement corrigé.")
        print("\nNOTE : Les commandes ne sont plus liées aux objets Ville. Le lien est préservé dans le champ 'ville_init'.")
        print("="*60)

    except Exception as e:
        print(f"\n--- 🚨 UNE ERREUR CRITIQUE EST SURVENUE : {e} ---")
        print("--- L'opération a été automatiquement annulée. Votre base de données n'a PAS été modifiée. ---")

if __name__ == "__main__":
    setup_django()
    reinitialiser_donnees_geographiques()