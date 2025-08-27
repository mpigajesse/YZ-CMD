#!/usr/bin/env python
"""
Script d'import automatique des articles CSV - YZ-CMD
Usage: python import_articles.py
"""

import os
import sys
import django
from datetime import datetime

def setup_django():
    """Configuration et initialisation de Django"""
    try:
        # Configuration Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de Django : {e}")
        return False

def import_articles():
    """Import automatique des articles depuis le CSV"""
    
    # Nom du fichier CSV (à adapter selon vos besoins)
    csv_filename = 'EXMPLE JOURNEE YOOZAK_EIGSI  - GESTIONNAIRE ARTICLE.csv'
    
    print("🚀 SCRIPT D'IMPORT DES ARTICLES CSV - YZ-CMD")
    print("=" * 60)
    print(f"⏰ Début de l'import : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Vérifier que le fichier existe
    if not os.path.exists(csv_filename):
        print(f"❌ Fichier CSV non trouvé : {csv_filename}")
        print("\n📁 Fichiers CSV disponibles dans le répertoire :")
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
        if csv_files:
            for i, file in enumerate(csv_files, 1):
                size_kb = os.path.getsize(file) / 1024
                print(f"   {i}. {file} ({size_kb:.1f} KB)")
        else:
            print("   Aucun fichier CSV trouvé")
        return False
    
    # Afficher les informations du fichier
    file_size = os.path.getsize(csv_filename)
    file_size_kb = file_size / 1024
    print(f"✅ Fichier trouvé : {csv_filename}")
    print(f"📊 Taille : {file_size_kb:.1f} KB")
    print(f"📅 Dernière modification : {datetime.fromtimestamp(os.path.getmtime(csv_filename)).strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        print("\n🔄 Début de l'import...")
        print("-" * 40)
        
        # Importer la commande Django
        from django.core.management import call_command
        
        # Appeler la commande Django
        call_command('import_articles_csv', csv_filename)
        
        print("-" * 40)
        print("✅ Import terminé avec succès !")
        print(f"⏰ Fin de l'import : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'import : {e}")
        print("\n🔧 Suggestions de dépannage :")
        print("   - Vérifiez que le fichier CSV est valide")
        print("   - Assurez-vous que Django est correctement configuré")
        print("   - Vérifiez les permissions du fichier")
        return False

def main():
    """Fonction principale"""
    print("🔧 Initialisation de Django...")
    
    if not setup_django():
        print("💥 Impossible d'initialiser Django. Arrêt du script.")
        sys.exit(1)
    
    print("✅ Django initialisé avec succès")
    
    # Lancer l'import
    success = import_articles()
    
    # Affichage du résultat final
    print("\n" + "=" * 60)
    if success:
        print("🎉 IMPORT RÉUSSI ! Tous les articles ont été importés.")
        print("📋 Vous pouvez maintenant utiliser l'interface web pour vérifier les articles.")
    else:
        print("💥 IMPORT ÉCHOUÉ ! Vérifiez les erreurs ci-dessus.")
    
    print("=" * 60)
    
    # Pause pour voir les résultats (optionnel)
    try:
        input("\nAppuyez sur Entrée pour fermer le script...")
    except KeyboardInterrupt:
        print("\n\n👋 Script interrompu par l'utilisateur")
    
    return success

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Script interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Erreur inattendue : {e}")
        sys.exit(1) 