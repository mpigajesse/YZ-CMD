#!/usr/bin/env python
"""
Script pour supprimer toutes les tables de la base de données PostgreSQL
ATTENTION: Ce script supprime TOUTES les données sans possibilité de récupération !
"""

import os
import sys
import django
from pathlib import Path

# Ajouter le répertoire du projet au path Python
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.conf import settings

def delete_all_tables():
    """
    Supprime toutes les tables de la base de données PostgreSQL
    """
    print("🚨 ATTENTION: Ce script va supprimer TOUTES les tables de la base de données !")
    print("📊 Base de données:", settings.DATABASES['default']['NAME'])
    print("🏠 Hôte:", settings.DATABASES['default']['HOST'])
    print("👤 Utilisateur:", settings.DATABASES['default']['USER'])
    
    confirmation = input("\n❓ Êtes-vous SÛR de vouloir continuer ? (tapez 'OUI' pour confirmer): ")
    
    if confirmation != 'OUI':
        print("❌ Opération annulée.")
        return
    
    try:
        with connection.cursor() as cursor:
            print("\n🔄 Début de la suppression des tables...")
            
            # Désactiver les contraintes de clés étrangères
            cursor.execute("SET session_replication_role = replica;")
            print("✅ Contraintes de clés étrangères désactivées")
            
            # Récupérer toutes les tables
            cursor.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename NOT LIKE 'pg_%'
                ORDER BY tablename;
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            print(f"📋 {len(tables)} tables trouvées:")
            
            for table in tables:
                print(f"   - {table}")
            
            # Supprimer toutes les tables
            for table in tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                    print(f"🗑️  Table '{table}' supprimée")
                except Exception as e:
                    print(f"⚠️  Erreur lors de la suppression de '{table}': {e}")
            
            # Réactiver les contraintes de clés étrangères
            cursor.execute("SET session_replication_role = DEFAULT;")
            print("✅ Contraintes de clés étrangères réactivées")
            
            # Vérifier qu'il ne reste plus de tables
            cursor.execute("""
                SELECT COUNT(*) 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename NOT LIKE 'pg_%';
            """)
            
            remaining_tables = cursor.fetchone()[0]
            
            if remaining_tables == 0:
                print("\n🎉 SUCCÈS: Toutes les tables ont été supprimées !")
                print("📝 La base de données est maintenant vide.")
            else:
                print(f"\n⚠️  ATTENTION: Il reste encore {remaining_tables} table(s)")
                
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        return False
    
    return True

def reset_migrations():
    """
    Supprime toutes les entrées de la table django_migrations
    """
    print("\n🔄 Suppression des entrées de migrations...")
    
    try:
        with connection.cursor() as cursor:
            # Vérifier si la table django_migrations existe encore
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'django_migrations'
                );
            """)
            
            if cursor.fetchone()[0]:
                cursor.execute("DELETE FROM django_migrations;")
                print("✅ Entrées de migrations supprimées")
            else:
                print("ℹ️  Table django_migrations déjà supprimée")
                
    except Exception as e:
        print(f"⚠️  Erreur lors de la suppression des migrations: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🗑️  SCRIPT DE SUPPRESSION COMPLÈTE DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    # Supprimer toutes les tables
    if delete_all_tables():
        # Supprimer les entrées de migrations
        reset_migrations()
        
        print("\n" + "=" * 60)
        print("✅ OPÉRATION TERMINÉE AVEC SUCCÈS")
        print("=" * 60)
        print("\n📋 Prochaines étapes:")
        print("1. Exécutez: python manage.py makemigrations")
        print("2. Exécutez: python manage.py migrate")
        print("3. Créez un superutilisateur: python manage.py createsuperuser")
        print("\n🎯 Votre base de données est maintenant prête pour un nouveau départ !")
    else:
        print("\n❌ L'opération a échoué.")
        sys.exit(1)
