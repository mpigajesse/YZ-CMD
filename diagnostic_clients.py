#!/usr/bin/env python
"""
Script de diagnostic pour vérifier l'exactitude des statistiques des clients
et détecter d'éventuels problèmes de synchronisation
"""

import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from client.models import Client
from commande.models import Commande
from synchronisation.models import SyncLog, GoogleSheetConfig
from django.db.models import Count, Q
from django.utils import timezone

def diagnostic_clients():
    """Effectue un diagnostic complet des clients"""
    print("🔍 DIAGNOSTIC DES CLIENTS - YZ-CMD")
    print("=" * 50)
    
    # 1. Statistiques générales
    total_clients = Client.objects.count()
    print(f"📊 STATISTIQUES GÉNÉRALES:")
    print(f"   • Total clients en base: {total_clients}")
    
    # 2. Vérifier les doublons potentiels
    print(f"\n🔍 VÉRIFICATION DES DOUBLONS:")
    
    # Doublons par numéro de téléphone
    doublons_tel = Client.objects.values('numero_tel').annotate(
        count=Count('id')
    ).filter(count__gt=1).order_by('-count')
    
    if doublons_tel:
        print(f"   ⚠️  {len(doublons_tel)} numéros de téléphone en double détectés:")
        for doublon in doublons_tel[:5]:  # Top 5
            clients_dupliques = Client.objects.filter(numero_tel=doublon['numero_tel'])
            print(f"      - {doublon['numero_tel']}: {doublon['count']} clients")
            for client in clients_dupliques:
                print(f"        → ID {client.id}: {client.get_full_name()}")
    else:
        print(f"   ✅ Aucun doublon de numéro de téléphone détecté")
    
    # Doublons par nom complet
    doublons_nom = Client.objects.values('nom', 'prenom').annotate(
        count=Count('id')
    ).filter(count__gt=1).order_by('-count')
    
    if doublons_nom:
        print(f"   ⚠️  {len(doublons_nom)} noms complets en double détectés:")
        for doublon in doublons_nom[:5]:  # Top 5
            print(f"      - {doublon['nom']} {doublon['prenom']}: {doublon['count']} clients")
    else:
        print(f"   ✅ Aucun doublon de nom complet détecté")
    
    # 3. Clients avec/sans commandes
    print(f"\n📋 RÉPARTITION PAR COMMANDES:")
    clients_avec_commandes = Client.objects.filter(commandes__isnull=False).distinct().count()
    clients_sans_commandes = Client.objects.filter(commandes__isnull=True).count()
    
    print(f"   • Clients avec commandes: {clients_avec_commandes}")
    print(f"   • Clients sans commandes: {clients_sans_commandes}")
    print(f"   • Ratio avec commandes: {(clients_avec_commandes/total_clients*100):.1f}%")
    
    # 4. Vérification avec les logs de synchronisation
    print(f"\n🔄 HISTORIQUE DE SYNCHRONISATION:")
    derniere_sync = SyncLog.objects.filter(status__in=['success', 'partial']).first()
    
    if derniere_sync:
        print(f"   • Dernière synchronisation: {derniere_sync.sync_date.strftime('%d/%m/%Y %H:%M')}")
        print(f"   • Statut: {derniere_sync.get_status_display()}")
        print(f"   • Nouvelles commandes créées: {derniere_sync.new_orders_created}")
        print(f"   • Commandes mises à jour: {derniere_sync.existing_orders_updated}")
        print(f"   • Doublons évités: {derniere_sync.duplicate_orders_found}")
        
        # Vérifier si le nombre de clients a augmenté depuis la dernière sync
        clients_crees_depuis = Client.objects.filter(
            date_creation__gte=derniere_sync.sync_date
        ).count()
        print(f"   • Clients créés depuis: {clients_crees_depuis}")
    else:
        print(f"   ⚠️  Aucune synchronisation trouvée")
    
    # 5. Top clients par nombre de commandes
    print(f"\n👥 TOP 10 CLIENTS PAR NOMBRE DE COMMANDES:")
    top_clients = Client.objects.annotate(
        nb_commandes=Count('commandes')
    ).filter(nb_commandes__gt=0).order_by('-nb_commandes')[:10]
    
    for i, client in enumerate(top_clients, 1):
        print(f"   {i:2}. {client.get_full_name()} ({client.numero_tel}): {client.nb_commandes} commandes")
    
    # 6. Clients récents
    print(f"\n📅 CLIENTS RÉCENTS (dernières 24h):")
    hier = timezone.now() - timezone.timedelta(days=1)
    clients_recents = Client.objects.filter(date_creation__gte=hier).count()
    print(f"   • Nouveaux clients: {clients_recents}")
    
    # 7. Intégrité des données
    print(f"\n🔧 INTÉGRITÉ DES DONNÉES:")
    
    # Clients sans numéro de téléphone
    clients_sans_tel = Client.objects.filter(
        Q(numero_tel__isnull=True) | Q(numero_tel__exact='')
    ).count()
    print(f"   • Clients sans téléphone: {clients_sans_tel}")
    
    # Clients sans nom
    clients_sans_nom = Client.objects.filter(
        Q(nom__isnull=True) | Q(nom__exact='') | 
        Q(prenom__isnull=True) | Q(prenom__exact='')
    ).count()
    print(f"   • Clients sans nom/prénom: {clients_sans_nom}")
    
    # 8. Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    
    if doublons_tel:
        print(f"   ⚠️  Fusionner les clients avec des numéros de téléphone identiques")
    
    if clients_sans_commandes > total_clients * 0.8:
        print(f"   ⚠️  Trop de clients sans commandes ({clients_sans_commandes})")
        print(f"      → Vérifier la synchronisation des commandes")
    
    if clients_sans_tel > 0:
        print(f"   ⚠️  {clients_sans_tel} clients sans numéro de téléphone")
        print(f"      → Nettoyer ou compléter ces données")
    
    if total_clients == 0:
        print(f"   ❌ Aucun client en base - problème de synchronisation")
    elif total_clients < 1000:
        print(f"   ⚠️  Nombre de clients faible ({total_clients}) - vérifier la synchronisation")
    else:
        print(f"   ✅ Nombre de clients cohérent ({total_clients})")
    
    print(f"\n" + "=" * 50)
    print(f"✅ Diagnostic terminé !")
    return {
        'total_clients': total_clients,
        'doublons_tel': len(doublons_tel),
        'doublons_nom': len(doublons_nom),
        'clients_avec_commandes': clients_avec_commandes,
        'clients_sans_commandes': clients_sans_commandes,
        'clients_sans_tel': clients_sans_tel,
        'clients_sans_nom': clients_sans_nom,
    }

if __name__ == "__main__":
    diagnostic_clients() 