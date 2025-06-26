#!/usr/bin/env python
"""
Script de peuplement des configurations KPIs par défaut
Exécuter avec : python manage.py shell < populate_kpi_config.py
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from kpis.models import KPIConfiguration

def populate_default_configurations():
    """Peuple la base avec les configurations par défaut"""
    
    configurations = [
        # Seuils d'alerte
        {
            'nom_parametre': 'stock_critique_seuil',
            'categorie': 'seuils',
            'valeur': 5.0,
            'description': 'Seuil en dessous duquel un article populaire est considéré en stock critique',
            'unite': 'unités',
            'valeur_min': 1.0,
            'valeur_max': 50.0,
        },
        {
            'nom_parametre': 'taux_conversion_objectif',
            'categorie': 'seuils',
            'valeur': 70.0,
            'description': 'Objectif de taux de conversion téléphonique pour les opérateurs',
            'unite': '%',
            'valeur_min': 50.0,
            'valeur_max': 95.0,
        },
        {
            'nom_parametre': 'delai_livraison_defaut',
            'categorie': 'seuils',
            'valeur': 3.0,
            'description': 'Délai de livraison par défaut utilisé si aucune donnée disponible',
            'unite': 'jours',
            'valeur_min': 1.0,
            'valeur_max': 10.0,
        },
        
        # Paramètres de calcul
        {
            'nom_parametre': 'periode_analyse_defaut',
            'categorie': 'calcul',
            'valeur': 30.0,
            'description': 'Période d\'analyse par défaut pour les KPIs',
            'unite': 'jours',
            'valeur_min': 7.0,
            'valeur_max': 90.0,
        },
        {
            'nom_parametre': 'article_populaire_seuil',
            'categorie': 'calcul',
            'valeur': 2.0,
            'description': 'Nombre de ventes minimum pour considérer un article comme populaire',
            'unite': 'ventes',
            'valeur_min': 1.0,
            'valeur_max': 10.0,
        },
        {
            'nom_parametre': 'client_fidele_seuil',
            'categorie': 'calcul',
            'valeur': 2.0,
            'description': 'Nombre de commandes minimum pour considérer un client comme fidèle',
            'unite': 'commandes',
            'valeur_min': 2.0,
            'valeur_max': 10.0,
        },
        
        # Préférences d'affichage
        {
            'nom_parametre': 'rafraichissement_auto',
            'categorie': 'affichage',
            'valeur': 5.0,
            'description': 'Intervalle de rafraîchissement automatique des données KPIs',
            'unite': 'minutes',
            'valeur_min': 0.0,
            'valeur_max': 60.0,
        },
        {
            'nom_parametre': 'afficher_tendances',
            'categorie': 'affichage',
            'valeur': 1.0,
            'description': 'Afficher les flèches de tendance sur les KPIs (1=oui, 0=non)',
            'unite': 'booléen',
            'valeur_min': 0.0,
            'valeur_max': 1.0,
        },
        {
            'nom_parametre': 'activer_animations',
            'categorie': 'affichage',
            'valeur': 1.0,
            'description': 'Activer les animations lors du chargement (1=oui, 0=non)',
            'unite': 'booléen',
            'valeur_min': 0.0,
            'valeur_max': 1.0,
        },
    ]
    
    created_count = 0
    updated_count = 0
    
    for config_data in configurations:
        config, created = KPIConfiguration.objects.get_or_create(
            nom_parametre=config_data['nom_parametre'],
            defaults=config_data
        )
        
        if created:
            created_count += 1
            print(f"✓ Créé: {config.nom_parametre} = {config.valeur} {config.unite}")
        else:
            # Mettre à jour si nécessaire (garde la valeur existante)
            updated_count += 1
            print(f"- Existe déjà: {config.nom_parametre} = {config.valeur} {config.unite}")
    
    print(f"\n🎯 Résumé:")
    print(f"   • {created_count} configurations créées")
    print(f"   • {updated_count} configurations existantes")
    print(f"   • Total: {KPIConfiguration.objects.count()} configurations")

if __name__ == "__main__":
    print("🚀 Peuplement des configurations KPIs par défaut...")
    populate_default_configurations()
    print("✅ Terminé!")
