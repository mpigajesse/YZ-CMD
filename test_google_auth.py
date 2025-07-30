#!/usr/bin/env python
"""
Script de test pour diagnostiquer l'authentification Google Sheets
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import gspread
from google.oauth2.service_account import Credentials
from synchronisation.models import GoogleSheetConfig

def test_google_authentication():
    """Test de l'authentification Google"""
    print("🔍 Test d'authentification Google Sheets...")
    
    try:
        # Chemin vers le fichier credentials
        credentials_path = 'credentials.json'
        
        if not os.path.exists(credentials_path):
            print(f"❌ Fichier credentials.json non trouvé dans : {os.path.abspath(credentials_path)}")
            return False
        
        print(f"✅ Fichier credentials.json trouvé")
        
        # Tester l'authentification
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
        client = gspread.authorize(creds)
        
        print("✅ Authentification Google réussie")
        
        # Tester avec une configuration existante
        configs = GoogleSheetConfig.objects.filter(is_active=True)
        if configs.exists():
            config = configs.first()
            print(f"🧪 Test avec la configuration : {config.sheet_name}")
            print(f"📄 URL : {config.sheet_url}")
            
            try:
                # Extraire l'ID de la feuille depuis l'URL
                if '/spreadsheets/d/' in config.sheet_url:
                    sheet_id = config.sheet_url.split('/spreadsheets/d/')[1].split('/')[0]
                    print(f"🆔 ID de la feuille : {sheet_id}")
                    
                    # Ouvrir la feuille
                    spreadsheet = client.open_by_key(sheet_id)
                    print(f"✅ Feuille ouverte avec succès : {spreadsheet.title}")
                    
                    # Lister les onglets
                    worksheets = spreadsheet.worksheets()
                    print(f"📊 Onglets disponibles : {[ws.title for ws in worksheets]}")
                    
                    # Tester la lecture du premier onglet
                    if worksheets:
                        worksheet = worksheets[0]
                        print(f"📖 Test de lecture de l'onglet : {worksheet.title}")
                        
                        # Lire les premières lignes
                        values = worksheet.get_all_values()
                        print(f"📏 Nombre de lignes : {len(values)}")
                        if values:
                            print(f"🔤 En-têtes : {values[0] if values else 'Aucune donnée'}")
                            print(f"📋 Première ligne de données : {values[1] if len(values) > 1 else 'Pas de données'}")
                        
                        print("✅ Test de lecture réussi")
                    
                else:
                    print(f"❌ Format d'URL non reconnu : {config.sheet_url}")
                    
            except Exception as e:
                print(f"❌ Erreur lors de l'accès à la feuille : {str(e)}")
                print(f"🔍 Type d'erreur : {type(e).__name__}")
                return False
        else:
            print("⚠️  Aucune configuration active trouvée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'authentification : {str(e)}")
        print(f"🔍 Type d'erreur : {type(e).__name__}")
        return False

def test_sync_logic():
    """Test de la logique de synchronisation"""
    print("\n🔍 Test de la logique de synchronisation...")
    
    try:
        from synchronisation.google_sheet_sync import GoogleSheetSync
        
        configs = GoogleSheetConfig.objects.filter(is_active=True)
        if not configs.exists():
            print("⚠️  Aucune configuration active pour tester")
            return
        
        config = configs.first()
        print(f"🧪 Test avec la configuration : {config.sheet_name}")
        
        # Créer une instance de synchronisation
        syncer = GoogleSheetSync(config, triggered_by="test_script")
        
        # Tester l'authentification
        print("🔐 Test d'authentification...")
        client = syncer.authenticate()
        if client:
            print("✅ Authentification réussie")
        else:
            print("❌ Échec de l'authentification")
            return
        
        # Tester l'ouverture de la feuille
        print("📄 Test d'ouverture de la feuille...")
        sheet = syncer.get_sheet(client)
        if sheet:
            print("✅ Feuille ouverte avec succès")
            
            # Tester la lecture des données
            print("📖 Test de lecture des données...")
            values = sheet.get_all_values()
            print(f"📏 Nombre de lignes lues : {len(values)}")
            
            if values:
                headers = values[0]
                print(f"🔤 En-têtes détectés : {headers}")
                
                # Simuler le traitement de quelques lignes
                print("🔄 Simulation du traitement...")
                for i, row in enumerate(values[1:3]):  # 2 premières lignes
                    print(f"  Ligne {i+1}: {dict(zip(headers, row))}")
            
        else:
            print("❌ Impossible d'ouvrir la feuille")
            return
        
        print("✅ Tests de la logique de synchronisation terminés")
        
    except Exception as e:
        print(f"❌ Erreur dans la logique de synchronisation : {str(e)}")
        print(f"🔍 Type d'erreur : {type(e).__name__}")
        import traceback
        print(f"🔧 Traceback : {traceback.format_exc()}")

if __name__ == "__main__":
    print("🚀 Démarrage des tests de diagnostic Google Sheets")
    print("=" * 60)
    
    # Test 1: Authentification
    auth_success = test_google_authentication()
    
    # Test 2: Logique de synchronisation (seulement si auth OK)
    if auth_success:
        test_sync_logic()
    
    print("\n" + "=" * 60)
    print("🏁 Tests de diagnostic terminés") 