import os
import sys
import django
from collections import defaultdict

def setup_django():
    """Initialise l'environnement Django pour exécuter le script."""
    # Ajoute le répertoire du projet au path pour que les modules soient trouvables
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
    
    # Définit le fichier de settings Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    # Charge la configuration de Django
    django.setup()

def find_duplicate_villes():
    """
    Script de diagnostic pour trouver les villes en double dans la base de données.
    Les doublons sont identifiés sur la base du nom de la ville, insensible à la casse.
    """
    print("--- Lancement du diagnostic des villes en double ---")
    
    # Importation du modèle après l'initialisation de Django
    from parametre.models import Ville

    # Utilise un dictionnaire pour regrouper les villes par leur nom en minuscules
    villes_by_name = defaultdict(list)
    
    # Récupère toutes les villes avec leur région pour un affichage plus informatif
    all_villes = Ville.objects.select_related('region').order_by('nom')
    
    for ville in all_villes:
        # La clé du dictionnaire est le nom de la ville en minuscules
        villes_by_name[ville.nom.lower()].append(ville)
    
    # Filtre et affiche les groupes qui contiennent plus d'une ville
    duplicates_found = 0
    for name_lower, villes_list in villes_by_name.items():
        if len(villes_list) > 1:
            duplicates_found += 1
            print(f"\n[!] Doublons trouvés pour le nom '{name_lower}':")
            
            # Affiche chaque entrée dupliquée avec ses détails
            for v in villes_list:
                region_info = f" (Région: {v.region.nom_region})" if v.region else " (Aucune région)"
                frais_info = f" (Frais: {v.frais_livraison} DH)"
                print(f"  - ID: {v.id:<5} | Nom exact: '{v.nom}'{region_info}{frais_info}")
    
    print("-" * 50)
    if duplicates_found == 0:
        print("--- ✅ Aucune ville en double trouvée. La base de données est saine. ---")
    else:
        print(f"--- ⚠️ {duplicates_found} groupe(s) de doublons trouvés. ---")
        print("\nAction recommandée :")
        print("1. Allez dans l'interface d'administration de Django.")
        print("2. Dans la section 'Villes', utilisez les IDs ci-dessus pour trouver et corriger les doublons.")
        print("3. Vous pouvez soit supprimer les entrées incorrectes, soit les fusionner en déplaçant les commandes associées vers la bonne entrée avant de supprimer la mauvaise.")
        print("-" * 50)

if __name__ == "__main__":
    setup_django()
    find_duplicate_villes() 