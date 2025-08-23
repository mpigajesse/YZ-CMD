#!/usr/bin/env python
"""
Script pour supprimer toutes les migrations de tous les apps
ATTENTION: Ce script supprime TOUTES les migrations sans exception !
"""

import os
import sys
import shutil
from pathlib import Path

# Ajouter le répertoire du projet au path Python
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

def delete_all_migrations():
    """
    Supprime toutes les migrations de tous les apps
    """
    print("🗑️  SCRIPT DE SUPPRESSION DE TOUTES LES MIGRATIONS")
    print("=" * 60)
    
    # Liste des apps Django
    apps = [
        'article',
        'client', 
        'commande',
        'livraison',
        'parametre',
        'operatConfirme',
        'operatLogistic',
        'synchronisation',
        'Prepacommande',
        'kpis',
    ]
    
    confirmation = input("❓ Êtes-vous SÛR de vouloir supprimer TOUTES les migrations ? (tapez 'OUI' pour confirmer): ")
    
    if confirmation != 'OUI':
        print("❌ Opération annulée.")
        return False
    
    total_deleted = 0
    
    for app in apps:
        migrations_dir = BASE_DIR / app / 'migrations'
        
        if migrations_dir.exists():
            print(f"\n📁 Traitement de l'app: {app}")
            
            # Supprimer tous les fichiers .py sauf __init__.py
            for migration_file in migrations_dir.glob('*.py'):
                if migration_file.name != '__init__.py':
                    try:
                        migration_file.unlink()
                        print(f"   🗑️  Supprimé: {migration_file.name}")
                        total_deleted += 1
                    except Exception as e:
                        print(f"   ⚠️  Erreur lors de la suppression de {migration_file.name}: {e}")
            
            # Supprimer le dossier __pycache__ s'il existe
            pycache_dir = migrations_dir / '__pycache__'
            if pycache_dir.exists():
                try:
                    shutil.rmtree(pycache_dir)
                    print(f"   🗑️  Supprimé: __pycache__")
                except Exception as e:
                    print(f"   ⚠️  Erreur lors de la suppression de __pycache__: {e}")
        else:
            print(f"\n📁 App {app}: pas de dossier migrations")
    
    print(f"\n🎉 SUCCÈS: {total_deleted} fichiers de migration supprimés !")
    return True

def create_init_files():
    """
    Crée les fichiers __init__.py dans les dossiers migrations
    """
    print("\n🔄 Création des fichiers __init__.py...")
    
    apps = [
        'article',
        'client', 
        'commande',
        'livraison',
        'parametre',
        'operatConfirme',
        'operatLogistic',
        'synchronisation',
        'Prepacommande',
        'kpis',
    ]
    
    for app in apps:
        migrations_dir = BASE_DIR / app / 'migrations'
        
        if migrations_dir.exists():
            init_file = migrations_dir / '__init__.py'
            if not init_file.exists():
                init_file.touch()
                print(f"   ✅ Créé: {app}/migrations/__init__.py")
        else:
            # Créer le dossier migrations et le fichier __init__.py
            migrations_dir.mkdir(parents=True, exist_ok=True)
            init_file = migrations_dir / '__init__.py'
            init_file.touch()
            print(f"   ✅ Créé: {app}/migrations/ (dossier et __init__.py)")

if __name__ == "__main__":
    if delete_all_migrations():
        create_init_files()
        
        print("\n" + "=" * 60)
        print("✅ SUPPRESSION DES MIGRATIONS TERMINÉE")
        print("=" * 60)
        print("\n📋 Prochaines étapes:")
        print("1. Exécutez: python manage.py makemigrations")
        print("2. Exécutez: python manage.py migrate")
        print("3. Créez un superutilisateur: python manage.py createsuperuser")
        print("\n🎯 Votre projet est maintenant prêt pour de nouvelles migrations !")
    else:
        print("\n❌ L'opération a échoué.")
        sys.exit(1)
