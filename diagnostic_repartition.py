#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from commande.models import Commande, EtatCommande, EnumEtatCmd
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

def diagnostiquer_repartition():
    print("=== DIAGNOSTIC DU SYSTÈME DE RÉPARTITION AUTOMATIQUE ===\n")
    
    # 1. Vérifier tous les états disponibles
    print("=== ÉTATS DISPONIBLES ===")
    etats = EnumEtatCmd.objects.all().order_by('ordre')
    for etat in etats:
        print(f"  - {etat.libelle} (ordre: {etat.ordre})")
    
    # 2. Répartition des commandes par état actuel
    print("\n=== RÉPARTITION DES COMMANDES PAR ÉTAT ACTUEL ===")
    etats_actifs = EtatCommande.objects.filter(
        date_fin__isnull=True
    ).values('enum_etat__libelle').annotate(
        nb_commandes=Count('commande', distinct=True)
    ).order_by('enum_etat__libelle')
    
    for etat in etats_actifs:
        print(f"  - {etat['enum_etat__libelle']}: {etat['nb_commandes']} commandes")
    
    # 3. Vérifier les commandes récentes
    print("\n=== COMMANDES RÉCENTES (derniers 7 jours) ===")
    date_limite = timezone.now() - timedelta(days=7)
    commandes_recentes = Commande.objects.filter(
        date_creation__gte=date_limite
    ).select_related('ville', 'ville__region')
    
    print(f"Total commandes récentes: {commandes_recentes.count()}")
    
    # Analyser les 10 premières commandes récentes
    print("\nDétail des 10 premières commandes récentes:")
    for commande in commandes_recentes[:10]:
        etat_actuel = commande.etat_actuel
        if commande.ville and commande.ville.region:
            ville_info = f"{commande.ville.nom} ({commande.ville.region.nom_region})"
        else:
            ville_info = "Pas de ville/région"
        
        etat_libelle = etat_actuel.enum_etat.libelle if etat_actuel else "Pas d'état"
        print(f"  - Commande {commande.num_cmd}: {etat_libelle} - {ville_info}")
    
    # 4. Vérifier les commandes qui devraient être dans l'état "Confirmée"
    print("\n=== ANALYSE DES COMMANDES POUR RÉPARTITION ===")
    
    # Commandes qui pourraient être confirmées mais ne le sont pas
    commandes_avec_ville = Commande.objects.filter(
        ville__isnull=False,
        ville__region__isnull=False
    ).select_related('ville', 'ville__region')
    
    print(f"Commandes avec ville et région: {commandes_avec_ville.count()}")
    
    # Vérifier leurs états
    etats_commandes_avec_ville = commandes_avec_ville.filter(
        etats__date_fin__isnull=True
    ).values('etats__enum_etat__libelle').annotate(
        nb=Count('id', distinct=True)
    )
    
    print("États des commandes avec ville/région:")
    for etat in etats_commandes_avec_ville:
        print(f"  - {etat['etats__enum_etat__libelle']}: {etat['nb']} commandes")
    
    # 5. Vérifier le processus de confirmation
    print("\n=== VÉRIFICATION DU PROCESSUS DE CONFIRMATION ===")
    
    # Commandes qui ont déjà été confirmées (historique)
    commandes_confirmees_historique = EtatCommande.objects.filter(
        enum_etat__libelle='Confirmée'
    ).count()
    print(f"Total historique de commandes confirmées: {commandes_confirmees_historique}")
    
    # Commandes qui sont passées de "Confirmée" à un autre état
    transitions_confirmee = EtatCommande.objects.filter(
        enum_etat__libelle='Confirmée',
        date_fin__isnull=False
    ).count()
    print(f"Commandes qui ont quitté l'état 'Confirmée': {transitions_confirmee}")

if __name__ == "__main__":
    diagnostiquer_repartition() 