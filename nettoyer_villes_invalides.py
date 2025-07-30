import os
import sys
import django
from django.db import transaction
from collections import defaultdict

def setup_django():
    """Initialise l'environnement Django pour exécuter le script."""
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

def find_and_clean_invalid_villes():
    """
    Script pour identifier, détacher les commandes et supprimer les villes invalides.
    """
    print("--- Lancement du nettoyage des villes invalides ---")
    
    from parametre.models import Ville
    from commande.models import Commande

    # Critères pour identifier une ville invalide.
    invalid_patterns = [
        'h', 'jour', 'lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche',
        'quotidienne', 'j+1', '/', '_',
    ]

    # Construit une query pour trouver les villes potentiellement invalides
    query = Ville.objects.none()
    for pattern in invalid_patterns:
        query |= Ville.objects.filter(nom__icontains=pattern)

    # Ajoute les villes qui sont entièrement numériques
    query |= Ville.objects.filter(nom__regex=r'^\\d+$')

    # Exclut quelques faux positifs possibles (ex: "Bouchemaine")
    query = query.exclude(nom__icontains='chemain')
    
    # Récupère les villes uniques qui correspondent aux critères
    invalid_villes = query.distinct()

    if not invalid_villes.exists():
        print("\n--- ✅ Aucune ville invalide trouvée selon les critères actuels. ---")
        return

    print(f"\n[!] {invalid_villes.count()} villes potentiellement invalides ont été trouvées.")
    
    villes_to_delete = []
    commands_to_update = defaultdict(list)

    for ville in invalid_villes:
        related_commands = Commande.objects.filter(ville=ville)
        if related_commands.exists():
            for cmd in related_commands:
                commands_to_update[ville.id].append(cmd.id_yz)
        villes_to_delete.append(ville)

    print("\n--- RÉSUMÉ DE L'OPÉRATION PROPOSÉE ---")
    print(f"Les {len(villes_to_delete)} villes suivantes seront SUPPRIMÉES :")
    for ville in villes_to_delete:
        print(f"  - ID: {ville.id}, Nom: '{ville.nom}'")
        if commands_to_update[ville.id]:
            count = len(commands_to_update[ville.id])
            print(f"    -> {count} commande(s) ser(a/ont) mise(s) à jour (champ 'ville' mis à nul).")

    print("-" * 50)
    
    # Demande de confirmation à l'utilisateur
    confirm = input("Voulez-vous procéder à ce nettoyage ? (o/N) : ").strip().lower()

    if confirm != 'o':
        print("\n--- ❌ Opération annulée par l'utilisateur. ---")
        return

    # Exécution de l'opération de nettoyage
    try:
        with transaction.atomic():
            print("\n--- 🚀 Lancement du nettoyage... ---")
            
            # 1. Mettre à jour les commandes
            updated_commands_count = 0
            for ville_id, cmd_ids in commands_to_update.items():
                cmds = Commande.objects.filter(id_yz__in=cmd_ids)
                count = cmds.update(ville=None)
                updated_commands_count += count
                print(f"  - {count} commande(s) détachée(s) de la ville ID {ville_id}.")

            # 2. Supprimer les villes invalides
            deleted_villes_count = 0
            for ville in villes_to_delete:
                ville.delete()
                deleted_villes_count += 1
            print(f"  - {deleted_villes_count} villes invalides supprimées.")

            print("\n--- ✅ Nettoyage terminé avec succès ! ---")
            print(f"Résumé : {updated_commands_count} commande(s) mise(s) à jour, {deleted_villes_count} ville(s) supprimée(s).")

    except Exception as e:
        print(f"\n--- 🚨 Une erreur est survenue lors du nettoyage : {e} ---")
        print("--- L'opération a été annulée. Votre base de données n'a pas été modifiée. ---")

if __name__ == "__main__":
    setup_django()
    find_and_clean_invalid_villes()