#!/usr/bin/env python
"""
Script de test pour vérifier les URLs des villes et les IDs
"""

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db.models import Count, Sum
from commande.models import Commande
from parametre.models import Ville, Region

def tester_urls_villes():
    """Test des URLs des villes"""
    print("=" * 80)
    print("TEST DES URLs DES VILLES")
    print("=" * 80)
    
    # 1. Vérifier les villes avec des commandes
    print("1. VILLES AVEC DES COMMANDES")
    print("-" * 40)
    
    villes_avec_commandes = Commande.objects.filter(
        etats__enum_etat__libelle__in=['Confirmée', 'À imprimer', 'Préparée', 'En cours de livraison'],
        etats__date_fin__isnull=True,
        ville__isnull=False
    ).values(
        'ville__id', 'ville__nom', 'ville__region__nom_region'
    ).annotate(
        nb_commandes=Count('id')
    ).order_by('ville__region__nom_region', 'ville__nom')
    
    print(f"{'ID':<5} {'Ville':<30} {'Région':<20} {'Commandes':<10}")
    print("-" * 70)
    
    for ville in villes_avec_commandes:
        print(f"{ville['ville__id']:<5} {ville['ville__nom']:<30} {ville['ville__region__nom_region']:<20} {ville['nb_commandes']:<10}")
    
    print()
    
    # 2. Vérifier les villes avec des commandes préparées
    print("2. VILLES AVEC DES COMMANDES PRÉPARÉES")
    print("-" * 40)
    
    villes_avec_preparees = Commande.objects.filter(
        etats__enum_etat__libelle='Préparée',
        etats__date_fin__isnull=True,
        ville__isnull=False
    ).values(
        'ville__id', 'ville__nom', 'ville__region__nom_region'
    ).annotate(
        nb_commandes_preparees=Count('id')
    ).order_by('ville__region__nom_region', 'ville__nom')
    
    print(f"{'ID':<5} {'Ville':<30} {'Région':<20} {'Préparées':<10}")
    print("-" * 70)
    
    for ville in villes_avec_preparees:
        print(f"{ville['ville__id']:<5} {ville['ville__nom']:<30} {ville['ville__region__nom_region']:<20} {ville['nb_commandes_preparees']:<10}")
    
    print()
    
    # 3. Test des URLs générées
    print("3. TEST DES URLs GÉNÉRÉES")
    print("-" * 40)
    
    from django.urls import reverse
    
    for ville in villes_avec_preparees:
        ville_id = ville['ville__id']
        ville_nom = ville['ville__nom']
        
        try:
            url_excel = reverse('Prepacommande:export_ville_consolidee_excel', kwargs={'ville_id': ville_id})
            url_csv = reverse('Prepacommande:export_ville_consolidee_csv', kwargs={'ville_id': ville_id})
            
            print(f"✅ Ville: {ville_nom} (ID: {ville_id})")
            print(f"   Excel: {url_excel}")
            print(f"   CSV: {url_csv}")
            print()
        except Exception as e:
            print(f"❌ Erreur pour {ville_nom} (ID: {ville_id}): {e}")
            print()
    
    # 4. Vérifier les caractères spéciaux dans les noms de villes
    print("4. VÉRIFICATION DES CARACTÈRES SPÉCIAUX")
    print("-" * 40)
    
    villes_speciales = Ville.objects.filter(nom__contains='/')
    if villes_speciales.exists():
        print("Villes avec des caractères spéciaux (/):")
        for ville in villes_speciales:
            print(f"   - {ville.nom} (ID: {ville.id})")
    else:
        print("Aucune ville avec des caractères spéciaux trouvée.")
    
    print()
    print("=" * 80)
    print("TEST TERMINÉ")
    print("=" * 80)

if __name__ == "__main__":
    try:
        tester_urls_villes()
    except Exception as e:
        print(f"Erreur lors du test : {e}")
        import traceback
        traceback.print_exc() 