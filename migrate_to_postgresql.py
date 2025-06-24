#!/usr/bin/env python3
"""
Script d'aide pour la migration vers PostgreSQL
Projet YZ-CMD
"""

import os
import sys
import django
from pathlib import Path

def check_postgresql_config():
    """Vérifie la configuration PostgreSQL"""
    print("=== Vérification de la configuration PostgreSQL ===")
    
    # Variables d'environnement requises
    required_vars = ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']
    
    print("\n1. Variables d'environnement :")
    for var in required_vars:
        value = os.getenv(var, 'NON DÉFINIE')
        print(f"   {var}: {value}")
    
    print("\n2. Créez un fichier .env avec le contenu suivant :")
    print("""
# Configuration Base de Données PostgreSQL
DB_NAME=yzcmd_db
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432

# Configuration Django
SECRET_KEY=django-insecure-beulebpje4!9xvoqg(@rn7$j0rt2)n2%8z=!euaw%t3&3j_z8*
DEBUG=True
    """)

def check_postgresql_connection():
    """Teste la connexion PostgreSQL"""
    try:
        import psycopg2
        from django.conf import settings
        
        print("\n=== Test de connexion PostgreSQL ===")
        
        db_config = settings.DATABASES['default']
        
        conn = psycopg2.connect(
            database=db_config['NAME'],
            user=db_config['USER'],
            password=db_config['PASSWORD'],
            host=db_config['HOST'],
            port=db_config['PORT']
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Connexion réussie à PostgreSQL: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur de connexion PostgreSQL: {e}")
        return False

def show_migration_steps():
    """Affiche les étapes de migration"""
    print("\n=== Étapes de migration vers PostgreSQL ===")
    print("""
1. 📋 Créer la base de données PostgreSQL :
   - Ouvrez pgAdmin ou psql
   - Créez une nouvelle base de données : yzcmd_db
   - Ou utilisez la commande SQL : CREATE DATABASE yzcmd_db;

2. 📝 Configurer les variables d'environnement :
   - Créez un fichier .env dans la racine du projet
   - Ajoutez les variables DB_NAME, DB_USER, DB_PASSWORD, etc.

3. 🏃‍♂️ Exécuter les migrations Django :
   python manage.py makemigrations
   python manage.py migrate

4. 👤 Créer un superutilisateur :
   python manage.py createsuperuser

5. 📊 (Optionnel) Importer les données existantes :
   python manage.py loaddata your_data_backup.json
    """)

if __name__ == "__main__":
    print("🔄 Migration YZ-CMD vers PostgreSQL")
    print("=" * 50)
    
    # Configuration Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    check_postgresql_config()
    show_migration_steps()
    
    # Tentative de test de connexion si Django est configuré
    try:
        django.setup()
        check_postgresql_connection()
    except Exception as e:
        print(f"⚠️  Configuration Django en cours... Erreur: {e}")
        print("   Configurez d'abord le fichier .env puis relancez ce script")

    print("\n🎯 Prochaines étapes recommandées :")
    print("1. Créez le fichier .env avec vos paramètres PostgreSQL")
    print("2. Créez la base de données 'yzcmd_db' dans PostgreSQL")
    print("3. Exécutez : python manage.py migrate")
    print("4. Exécutez : python manage.py createsuperuser") 