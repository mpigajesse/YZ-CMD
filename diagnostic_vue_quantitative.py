#!/usr/bin/env python
"""
Script de diagnostic avancé pour l'API Vue Quantitative
Teste spécifiquement les différentes périodes qui causent des erreurs
"""

import os
import sys
import django
from datetime import datetime, timedelta
import traceback

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.utils import timezone
from kpis.views import vue_quantitative_data
import json

def test_period_calculation():
    """Test direct des calculs de période dans la vue"""
    print("\n" + "="*60)
    print("🔍 DIAGNOSTIC DES CALCULS DE PÉRIODE")
    print("="*60)
    
    today = timezone.now().date()
    print(f"📅 Date actuelle: {today}")
    
    # Test chaque type de période
    periods_to_test = {
        'aujourd_hui': 'Aujourd\'hui',
        'ce_mois': 'Ce mois',
        'cette_annee': 'Cette année',
        'custom:2025-06-01:2025-07-01': 'Période personnalisée'
    }
    
    for period_code, period_name in periods_to_test.items():
        print(f"\n📊 Test: {period_name} ({period_code})")
        print("-" * 40)
        
        try:
            # Reproduire la logique de calcul de la vue
            if period_code == 'aujourd_hui':
                date_debut = today
                date_fin = today
                jours = 1
                print(f"   ✅ Du {date_debut} au {date_fin} ({jours} jour)")
                
            elif period_code == 'ce_mois':
                date_debut = today.replace(day=1)
                date_fin = today
                jours = (date_fin - date_debut).days + 1
                print(f"   ✅ Du {date_debut} au {date_fin} ({jours} jours)")
                
            elif period_code == 'cette_annee':
                date_debut = today.replace(month=1, day=1)
                date_fin = today
                jours = (date_fin - date_debut).days + 1
                print(f"   ✅ Du {date_debut} au {date_fin} ({jours} jours)")
                
            elif period_code.startswith('custom:'):
                parts = period_code.split(':')
                if len(parts) == 3:
                    from datetime import datetime
                    date_debut = datetime.strptime(parts[1], '%Y-%m-%d').date()
                    date_fin = datetime.strptime(parts[2], '%Y-%m-%d').date()
                    jours = (date_fin - date_debut).days + 1
                    print(f"   ✅ Du {date_debut} au {date_fin} ({jours} jours)")
                else:
                    print(f"   ❌ Format invalide: {parts}")
                    
        except Exception as e:
            print(f"   ❌ Erreur calcul: {str(e)}")
            print(f"      Traceback: {traceback.format_exc()}")

def test_database_access():
    """Test d'accès aux données de commandes"""
    print("\n" + "="*60)
    print("🗄️ DIAGNOSTIC D'ACCÈS BASE DE DONNÉES")
    print("="*60)
    
    try:
        from commande.models import Commande
        from django.db.models import Count
        
        # Test basique
        total = Commande.objects.count()
        print(f"📊 Total commandes en base: {total}")
        
        if total == 0:
            print("⚠️  Aucune commande en base - cela peut expliquer les erreurs")
            return False
            
        # Test avec filtres de date
        today = timezone.now().date()
        
        # Aujourd'hui
        today_count = Commande.objects.filter(date_cmd=today).count()
        print(f"📅 Commandes aujourd'hui: {today_count}")
        
        # Ce mois
        debut_mois = today.replace(day=1)
        month_count = Commande.objects.filter(
            date_cmd__gte=debut_mois,
            date_cmd__lte=today
        ).count()
        print(f"📅 Commandes ce mois: {month_count}")
        
        # Cette année
        debut_annee = today.replace(month=1, day=1)
        year_count = Commande.objects.filter(
            date_cmd__gte=debut_annee,
            date_cmd__lte=today
        ).count()
        print(f"📅 Commandes cette année: {year_count}")
        
        # Test des états
        print("\n🏷️ Test des états de commandes:")
        etats_actifs = Commande.objects.filter(
            etats__date_fin__isnull=True
        ).select_related('etats__enum_etat').values(
            'etats__enum_etat__libelle'
        ).annotate(count=Count('id'))
        
        for etat in etats_actifs:
            print(f"   - {etat['etats__enum_etat__libelle']}: {etat['count']}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur base de données: {str(e)}")
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def test_api_with_periods():
    """Test complet de l'API avec toutes les périodes"""
    print("\n" + "="*60)
    print("🌐 DIAGNOSTIC COMPLET API")
    print("="*60)
    
    factory = RequestFactory()
    
    # Créer un utilisateur de test
    try:
        user = User.objects.first()
        if not user:
            user = User.objects.create_user('test_user', 'test@test.com', 'password123')
    except Exception as e:
        print(f"❌ Erreur création utilisateur: {str(e)}")
        return
    
    periods = [
        ('', 'Par défaut'),
        ('aujourd_hui', 'Aujourd\'hui'),
        ('ce_mois', 'Ce mois'),
        ('cette_annee', 'Cette année'),
        ('custom:2025-06-01:2025-07-01', 'Période personnalisée'),
        ('7j', 'Ancien format - 7 jours'),
        ('30j', 'Ancien format - 30 jours'),
        ('invalid_period', 'Période invalide (test)')
    ]
    
    for period_code, period_name in periods:
        print(f"\n🔍 Test API: {period_name}")
        print("-" * 40)
        
        try:
            # Créer la requête
            url = '/kpis/api/vue-quantitative/'
            if period_code:
                url += f'?period={period_code}'
            
            request = factory.get(url)
            request.user = user
            
            # Appeler la vue
            response = vue_quantitative_data(request)
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    content = response.content.decode('utf-8')
                    data = json.loads(content)
                    
                    if data.get('success'):
                        total = data['data']['total_commandes']
                        etats_count = len(data['data']['etats_commandes'])
                        print(f"   ✅ Succès - {total} commandes, {etats_count} états")
                        
                        # Afficher quelques détails
                        stats = data['data']['stats_supplementaires']
                        print(f"      En cours: {stats.get('commandes_en_cours', 0)}")
                        print(f"      Problématiques: {stats.get('commandes_problematiques', 0)}")
                        print(f"      Complétées: {stats.get('commandes_completees', 0)}")
                    else:
                        print(f"   ❌ Erreur API: {data.get('message', 'Pas de message')}")
                        if 'error' in data:
                            print(f"      Code: {data['error']}")
                            
                except json.JSONDecodeError as e:
                    print(f"   ❌ Erreur JSON: {str(e)}")
                    print(f"      Contenu: {response.content[:100]}...")
                    
            else:
                print(f"   ❌ Erreur HTTP: {response.status_code}")
                print(f"      Contenu: {response.content[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            print(f"      Traceback: {traceback.format_exc()}")

def check_view_imports():
    """Vérifier que tous les imports nécessaires sont présents"""
    print("\n" + "="*60)
    print("📦 DIAGNOSTIC DES IMPORTS")
    print("="*60)
    
    try:
        from commande.models import Commande, EtatCommande
        print("✅ Modèles Commande et EtatCommande importés")
        
        from django.utils import timezone
        print("✅ Django timezone importé")
        
        from django.http import JsonResponse
        print("✅ JsonResponse importé")
        
        from datetime import datetime, timedelta
        print("✅ datetime et timedelta importés")
        
        from django.db.models import Count, Q
        print("✅ Count et Q importés")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {str(e)}")
        return False

if __name__ == '__main__':
    print("🚀 DÉMARRAGE DU DIAGNOSTIC COMPLET")
    print(f"📅 Date/Heure: {datetime.now()}")
    
    # Exécuter tous les tests de diagnostic
    success = True
    
    success &= check_view_imports()
    success &= test_database_access()
    
    test_period_calculation()
    test_api_with_periods()
    
    print("\n" + "="*60)
    if success:
        print("✅ DIAGNOSTIC TERMINÉ - Vérifiez les résultats ci-dessus")
    else:
        print("❌ DIAGNOSTIC TERMINÉ - Des erreurs ont été détectées")
    print("="*60)
