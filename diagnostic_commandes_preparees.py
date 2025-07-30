#!/usr/bin/env python
"""
Script de diagnostic pour vérifier les indicateurs des commandes préparées
dans les templates HTML de l'interface de préparation.
"""

import os
import sys
import django
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db.models import Count, Sum
from commande.models import Commande
from parametre.models import Region, Ville

def diagnostic_commandes_preparees():
    """Diagnostic complet des commandes préparées"""
    print("=" * 80)
    print("DIAGNOSTIC DES COMMANDES PRÉPARÉES")
    print("=" * 80)
    print(f"Date et heure : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Statistiques globales
    print("1. STATISTIQUES GLOBALES")
    print("-" * 40)
    
    # Total des commandes préparées
    total_preparees = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_fin__isnull=True
    ).count()
    
    # Total des commandes en traitement
    total_en_traitement = Commande.objects.filter(
        etats__enum_etat__libelle__in=['Confirmée', 'À imprimer', 'Préparée', 'En cours de livraison'],
        etats__date_fin__isnull=True
    ).count()
    
    print(f"Total commandes préparées : {total_preparees}")
    print(f"Total commandes en traitement : {total_en_traitement}")
    print(f"Pourcentage préparées : {(total_preparees/total_en_traitement*100):.1f}%" if total_en_traitement > 0 else "0%")
    print()
    
    # 2. Statistiques par région
    print("2. STATISTIQUES PAR RÉGION")
    print("-" * 40)
    
    # Commandes préparées par région
    preparees_par_region = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_fin__isnull=True,
        ville__isnull=False,
        ville__region__isnull=False
    ).values('ville__region__nom_region').annotate(
        nb_commandes_preparees=Count('id')
    ).order_by('ville__region__nom_region')
    
    # Commandes en traitement par région
    en_traitement_par_region = Commande.objects.filter(
        etats__enum_etat__libelle__in=['Confirmée', 'À imprimer', 'Préparée', 'En cours de livraison'],
        etats__date_fin__isnull=True,
        ville__isnull=False,
        ville__region__isnull=False
    ).values('ville__region__nom_region').annotate(
        nb_commandes=Count('id')
    ).order_by('ville__region__nom_region')
    
    # Créer des dictionnaires pour comparaison
    preparees_dict = {stat['ville__region__nom_region']: stat['nb_commandes_preparees'] for stat in preparees_par_region}
    traitement_dict = {stat['ville__region__nom_region']: stat['nb_commandes'] for stat in en_traitement_par_region}
    
    print(f"{'Région':<25} {'En traitement':<15} {'Préparées':<12} {'%':<8} {'Indicateur'}")
    print("-" * 80)
    
    for region in sorted(set(list(preparees_dict.keys()) + list(traitement_dict.keys()))):
        en_traitement = traitement_dict.get(region, 0)
        preparees = preparees_dict.get(region, 0)
        pourcentage = (preparees/en_traitement*100) if en_traitement > 0 else 0
        indicateur = "✅ OUI" if preparees > 0 else "❌ NON"
        
        print(f"{region:<25} {en_traitement:<15} {preparees:<12} {pourcentage:<8.1f}% {indicateur}")
    
    print()
    
    # 3. Statistiques par ville
    print("3. STATISTIQUES PAR VILLE")
    print("-" * 40)
    
    # Commandes préparées par ville
    preparees_par_ville = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_fin__isnull=True,
        ville__isnull=False,
        ville__region__isnull=False
    ).values('ville__nom', 'ville__region__nom_region').annotate(
        nb_commandes_preparees=Count('id')
    ).order_by('ville__region__nom_region', 'ville__nom')
    
    # Commandes en traitement par ville
    en_traitement_par_ville = Commande.objects.filter(
        etats__enum_etat__libelle__in=['Confirmée', 'À imprimer', 'Préparée', 'En cours de livraison'],
        etats__date_fin__isnull=True,
        ville__isnull=False,
        ville__region__isnull=False
    ).values('ville__nom', 'ville__region__nom_region').annotate(
        nb_commandes=Count('id')
    ).order_by('ville__region__nom_region', 'ville__nom')
    
    # Créer des dictionnaires pour comparaison
    preparees_ville_dict = {(stat['ville__nom'], stat['ville__region__nom_region']): stat['nb_commandes_preparees'] for stat in preparees_par_ville}
    traitement_ville_dict = {(stat['ville__nom'], stat['ville__region__nom_region']): stat['nb_commandes'] for stat in en_traitement_par_ville}
    
    print(f"{'Ville':<20} {'Région':<20} {'En traitement':<15} {'Préparées':<12} {'Indicateur'}")
    print("-" * 85)
    
    # Afficher seulement les villes avec des commandes préparées
    villes_avec_preparees = [key for key, value in preparees_ville_dict.items() if value > 0]
    
    if villes_avec_preparees:
        for ville, region in sorted(villes_avec_preparees):
            en_traitement = traitement_ville_dict.get((ville, region), 0)
            preparees = preparees_ville_dict.get((ville, region), 0)
            indicateur = "✅ OUI" if preparees > 0 else "❌ NON"
            
            print(f"{ville:<20} {region:<20} {en_traitement:<15} {preparees:<12} {indicateur}")
    else:
        print("Aucune ville avec des commandes préparées trouvée.")
    
    print()
    
    # 4. Vérification des données pour les templates
    print("4. VÉRIFICATION DES DONNÉES POUR LES TEMPLATES")
    print("-" * 40)
    
    # Simuler les données comme dans les vues
    print("Données pour repartition.html et repartition_automatique.html :")
    print("preparees_par_region = {")
    for region, count in preparees_dict.items():
        if count > 0:
            print(f"    '{region}': {count},")
    print("}")
    
    print("\npreparees_par_ville = {")
    for (ville, region), count in preparees_ville_dict.items():
        if count > 0:
            print(f"    ('{ville}', '{region}'): {count},")
    print("}")
    
    print()
    
    # 5. Test des filtres template
    print("5. TEST DES FILTRES TEMPLATE")
    print("-" * 40)
    
    # Simuler le filtre get_item
    def get_item(dictionary, key):
        try:
            return dictionary.get(key, 0)
        except (AttributeError, TypeError):
            return 0
    
    print("Test du filtre get_item pour les régions :")
    for region in sorted(preparees_dict.keys()):
        if preparees_dict[region] > 0:
            resultat = get_item(preparees_dict, region)
            print(f"    get_item(preparees_par_region, '{region}') = {resultat}")
    
    print("\nTest du filtre get_item pour les villes :")
    for (ville, region) in sorted(preparees_ville_dict.keys()):
        if preparees_ville_dict[(ville, region)] > 0:
            ville_key = f"{ville},{region}"
            resultat = get_item(preparees_ville_dict, (ville, region))
            print(f"    get_item(preparees_par_ville, ('{ville}', '{region}')) = {resultat}")
    
    print()
    
    # 6. Résumé des indicateurs
    print("6. RÉSUMÉ DES INDICATEURS")
    print("-" * 40)
    
    regions_avec_indicateurs = len([r for r, c in preparees_dict.items() if c > 0])
    villes_avec_indicateurs = len([v for v, c in preparees_ville_dict.items() if c > 0])
    
    print(f"Régions avec indicateurs : {regions_avec_indicateurs}")
    print(f"Villes avec indicateurs : {villes_avec_indicateurs}")
    print(f"Total indicateurs à afficher : {regions_avec_indicateurs + villes_avec_indicateurs}")
    
    if total_preparees > 0:
        print(f"\n✅ Les indicateurs devraient être visibles dans les templates")
        print(f"   - {regions_avec_indicateurs} régions avec des commandes préparées")
        print(f"   - {villes_avec_indicateurs} villes avec des commandes préparées")
    else:
        print(f"\n❌ Aucun indicateur ne devrait être visible (pas de commandes préparées)")
    
    print()
    print("=" * 80)
    print("DIAGNOSTIC TERMINÉ")
    print("=" * 80)

if __name__ == "__main__":
    try:
        diagnostic_commandes_preparees()
    except Exception as e:
        print(f"Erreur lors du diagnostic : {e}")
        import traceback
        traceback.print_exc() 