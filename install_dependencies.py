#!/usr/bin/env python
"""
Script d'installation des dépendances manquantes
"""

import subprocess
import sys

def install_package(package):
    """Installe un package via pip"""
    try:
        print(f"📦 Installation de {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation de {package}: {e}")
        return False

def main():
    """Fonction principale"""
    print("🔧 Installation des dépendances manquantes...")
    
    # Liste des packages à installer
    packages = [
        'django-crispy-forms',
        'django-widget-tweaks',
        'django-filter',
        'djangorestframework',
        'django-cors-headers',
        'django-extensions',
        'django-tailwind',
        'django-browser-reload',
        'whitenoise'
    ]
    
    success_count = 0
    total_count = len(packages)
    
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n📊 Résumé: {success_count}/{total_count} packages installés avec succès")
    
    if success_count == total_count:
        print("🎉 Toutes les dépendances sont installées !")
        print("Vous pouvez maintenant tester les contraintes avec: python test_constraints.py")
    else:
        print("⚠️  Certaines dépendances n'ont pas pu être installées")
        print("Vérifiez les erreurs ci-dessus et réessayez")

if __name__ == "__main__":
    main()
