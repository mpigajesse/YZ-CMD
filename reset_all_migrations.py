#!/usr/bin/env python
"""
Script pour supprimer toutes les migrations et recréer la base de données
"""
import os
import sys
import django
import shutil
from pathlib import Path

# Configuration Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection

def delete_all_migrations():
    """Supprime toutes les migrations de tous les apps"""
    print("🗑️  Suppression de toutes les migrations...")
    
    apps = [
        'article', 'client', 'commande', 'livraison', 'parametre', 
        'operatConfirme', 'operatLogistic', 'synchronisation', 
        'Prepacommande', 'kpis', 'Superpreparation'
    ]
    
    for app in apps:
        migrations_dir = BASE_DIR / app / 'migrations'
        if migrations_dir.exists():
            print(f"   📁 Suppression des migrations de {app}...")
            for migration_file in migrations_dir.glob('*.py'):
                if migration_file.name != '__init__.py':
                    migration_file.unlink()
                    print(f"      ❌ Supprimé: {migration_file.name}")
            
            # Supprimer __pycache__
            pycache_dir = migrations_dir / '__pycache__'
            if pycache_dir.exists():
                shutil.rmtree(pycache_dir)
                print(f"      ❌ Supprimé: __pycache__")
    
    print("✅ Toutes les migrations supprimées")

def recreate_init_files():
    """Recrée les fichiers __init__.py dans les dossiers migrations"""
    print("📝 Recréation des fichiers __init__.py...")
    
    apps = [
        'article', 'client', 'commande', 'livraison', 'parametre', 
        'operatConfirme', 'operatLogistic', 'synchronisation', 
        'Prepacommande', 'kpis', 'Superpreparation'
    ]
    
    for app in apps:
        migrations_dir = BASE_DIR / app / 'migrations'
        if migrations_dir.exists():
            init_file = migrations_dir / '__init__.py'
            if not init_file.exists():
                init_file.touch()
                print(f"   ✅ Créé: {app}/migrations/__init__.py")
    
    print("✅ Fichiers __init__.py recréés")

def reset_database():
    """Supprime toutes les tables et recrée la base de données"""
    print("🗄️  Réinitialisation de la base de données...")
    
    with connection.cursor() as cursor:
        # Désactiver les contraintes de clés étrangères
        cursor.execute("SET session_replication_role = replica;")
        
        # Récupérer TOUTES les tables (y compris Django)
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Supprimer toutes les tables
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
            print(f"   ❌ Supprimé: {table}")
        
        # Réactiver les contraintes
        cursor.execute("SET session_replication_role = DEFAULT;")
    
    print("✅ Base de données réinitialisée")

def main():
    print("=" * 60)
    print("🔄 SCRIPT DE RÉINITIALISATION COMPLÈTE")
    print("=" * 60)
    
    # Demander confirmation
    response = input("\n⚠️  ATTENTION: Ce script va supprimer TOUTES les migrations et TOUTES les données de la base de données.\nÊtes-vous sûr de vouloir continuer ? (oui/non): ")
    
    if response.lower() != 'oui':
        print("❌ Opération annulée")
        return
    
    try:
        # Étape 1: Supprimer toutes les migrations
        delete_all_migrations()
        
        # Étape 2: Recréer les fichiers __init__.py
        recreate_init_files()
        
        # Étape 3: Réinitialiser la base de données
        reset_database()
        
        print("\n" + "=" * 60)
        print("✅ RÉINITIALISATION TERMINÉE AVEC SUCCÈS")
        print("=" * 60)
        print("\n📋 Prochaines étapes:")
        print("1. python manage.py makemigrations")
        print("2. python manage.py migrate")
        print("3. python manage.py createsuperuser")
        
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        return

if __name__ == "__main__":
    main()
