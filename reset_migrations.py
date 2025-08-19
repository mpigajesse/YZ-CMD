#!/usr/bin/env python
"""
Script pour réinitialiser complètement les migrations et la base de données
"""
import os
import shutil
import subprocess
import sys

def remove_migrations():
    """Supprime tous les fichiers de migration de toutes les apps"""
    print("🧹 Suppression de tous les fichiers de migration...")
    
    # Liste des dossiers d'apps Django
    apps = [
        'article', 'client', 'commande', 'kpis', 'livraison', 
        'operatConfirme', 'operatLogistic', 'parametre', 
        'Prepacommande', 'Superpreparation', 'synchronisation'
    ]
    
    for app in apps:
        migrations_dir = os.path.join(app, 'migrations')
        if os.path.exists(migrations_dir):
            # Supprimer tous les fichiers .py sauf __init__.py
            for file in os.listdir(migrations_dir):
                if file.endswith('.py') and file != '__init__.py':
                    file_path = os.path.join(migrations_dir, file)
                    os.remove(file_path)
                    print(f"   - Supprimé: {file_path}")
    
    print("✅ Tous les fichiers de migration ont été supprimés")

def remove_database():
    """Supprime la base de données SQLite"""
    print("🗑️  Suppression de la base de données...")
    
    db_files = ['db.sqlite3', 'db.sqlite3-journal']
    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"   - Supprimé: {db_file}")
    
    print("✅ Base de données supprimée")

def create_new_migrations():
    """Crée de nouvelles migrations pour toutes les apps"""
    print("🔄 Création de nouvelles migrations...")
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'makemigrations'
        ], capture_output=True, text=True, check=True)
        print("✅ Nouvelles migrations créées")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la création des migrations: {e}")
        print(f"Sortie d'erreur: {e.stderr}")
        return False
    
    return True

def apply_migrations():
    """Applique les nouvelles migrations"""
    print("🚀 Application des migrations...")
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], capture_output=True, text=True, check=True)
        print("✅ Migrations appliquées avec succès")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'application des migrations: {e}")
        print(f"Sortie d'erreur: {e.stderr}")
        return False
    
    return True

def create_superuser():
    """Crée un superuser par défaut"""
    print("👤 Création d'un superuser...")
    
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'createsuperuser',
            '--username', 'admin',
            '--email', 'admin@example.com',
            '--noinput'
        ], capture_output=True, text=True, check=True)
        print("✅ Superuser créé avec succès")
        print("   Username: admin")
        print("   Email: admin@example.com")
        print("   Mot de passe: admin (à changer)")
        
        # Définir le mot de passe
        subprocess.run([
            sys.executable, 'manage.py', 'shell', '-c',
            'from django.contrib.auth.models import User; '
            'u = User.objects.get(username="admin"); '
            'u.set_password("admin"); '
            'u.save(); '
            'print("Mot de passe défini")'
        ], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la création du superuser: {e}")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("🚀 Réinitialisation complète de la base de données Django")
    print("=" * 60)
    
    # 1. Supprimer les migrations
    remove_migrations()
    
    # 2. Supprimer la base de données
    remove_database()
    
    # 3. Créer de nouvelles migrations
    if not create_new_migrations():
        print("❌ Échec de la création des migrations")
        return
    
    # 4. Appliquer les migrations
    if not apply_migrations():
        print("❌ Échec de l'application des migrations")
        return
    
    # 5. Créer un superuser
    if not create_superuser():
        print("❌ Échec de la création du superuser")
        return
    
    print("\n🎉 Réinitialisation terminée avec succès !")
    print("\n📋 Prochaines étapes:")
    print("   1. Démarrer le serveur: python manage.py runserver")
    print("   2. Aller sur http://127.0.0.1:8000/admin/")
    print("   3. Se connecter avec admin/admin")
    print("   4. Importer vos articles depuis le CSV")

if __name__ == "__main__":
    main()
