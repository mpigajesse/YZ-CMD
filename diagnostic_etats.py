#!/usr/bin/env python
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'YZ_CMD.settings')
django.setup()

from commande.models import EtatCommande, EnumEtatCmd, Commande
from django.db.models import Count

print("=== DIAGNOSTIC DES ÉTATS DE COMMANDES ===")
print()

# 1. Vérifier tous les états définis
print("1. États définis dans EnumEtatCmd:")
for etat in EnumEtatCmd.objects.all().order_by('ordre'):
    print(f"   - {etat.libelle} (ID: {etat.id}, Couleur: {etat.couleur})")
print()

# 2. Compter les commandes par état actuel
print("2. Commandes par état actuel (date_fin=NULL):")
etats_actifs = EtatCommande.objects.filter(date_fin__isnull=True).values('enum_etat__libelle').annotate(count=Count('id')).order_by('-count')
total_avec_etat = 0
for etat in etats_actifs:
    count = etat["count"]
    total_avec_etat += count
    print(f"   - {etat['enum_etat__libelle']}: {count} commandes")
print()

# 3. Vérifier spécifiquement les commandes affectées
print("3. Vérification des commandes 'Affectées':")
affectees_exact = EtatCommande.objects.filter(
    date_fin__isnull=True,
    enum_etat__libelle__exact='Affectée'
)
print(f"   - Avec exact='Affectée': {affectees_exact.count()}")

affectees_icontains = EtatCommande.objects.filter(
    date_fin__isnull=True,
    enum_etat__libelle__icontains='Affectée'
)
print(f"   - Avec icontains='Affectée': {affectees_icontains.count()}")

# Lister les états qui contiennent "Affectée"
etats_avec_affectee = EnumEtatCmd.objects.filter(libelle__icontains='Affectée')
print(f"   - États contenant 'Affectée':")
for etat in etats_avec_affectee:
    count = EtatCommande.objects.filter(date_fin__isnull=True, enum_etat=etat).count()
    print(f"     * '{etat.libelle}': {count} commandes")
print()

# 4. Vérifier les doublons d'états actifs
print("4. Vérification des doublons d'états actifs:")
doublons = EtatCommande.objects.filter(date_fin__isnull=True).values('commande_id').annotate(count=Count('id')).filter(count__gt=1)
if doublons.exists():
    print(f"   ATTENTION: {doublons.count()} commandes ont plusieurs états actifs!")
    for doublon in doublons[:5]:
        commande_id = doublon["commande_id"]
        count = doublon["count"]
        print(f"   - Commande ID {commande_id}: {count} états actifs")
        # Détailler les états de cette commande
        etats_commande = EtatCommande.objects.filter(commande_id=commande_id, date_fin__isnull=True)
        for etat in etats_commande:
            print(f"     * {etat.enum_etat.libelle} (créé le {etat.date_debut})")
else:
    print("   Aucun doublon d'état actif détecté.")
print()

# 5. Statistiques générales
total_commandes = Commande.objects.count()
commandes_sans_etat = total_commandes - total_avec_etat
print("5. Statistiques générales:")
print(f"   - Total commandes: {total_commandes}")
print(f"   - Commandes avec état actif: {total_avec_etat}")
print(f"   - Commandes sans état: {commandes_sans_etat}")
print()

print("=== FIN DU DIAGNOSTIC ===") 