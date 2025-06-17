from django.db import migrations


def populate_etats_commande(apps, schema_editor):
    """Peuple la table EnumEtatCmd avec tous les états nécessaires"""
    EnumEtatCmd = apps.get_model('commande', 'EnumEtatCmd')
    
    # États de commande principaux
    etats_commande = [
        {'libelle': 'Non affectée', 'ordre': 10, 'couleur': '#6B7280'},
        {'libelle': 'Affectée', 'ordre': 20, 'couleur': '#3B82F6'},
        {'libelle': 'En cours de confirmation', 'ordre': 30, 'couleur': '#F59E0B'},
        {'libelle': 'Confirmée', 'ordre': 40, 'couleur': '#10B981'},
        {'libelle': 'Erronée', 'ordre': 50, 'couleur': '#EF4444'},
        {'libelle': 'Doublon', 'ordre': 60, 'couleur': '#F97316'},
    ]
    
    # États de paiement
    etats_paiement = [
        {'libelle': 'Non payé', 'ordre': 100, 'couleur': '#DC2626'},
        {'libelle': 'Partiellement payé', 'ordre': 110, 'couleur': '#F59E0B'},
        {'libelle': 'Payé', 'ordre': 120, 'couleur': '#059669'},
    ]
    
    # États de livraison
    etats_livraison = [
        {'libelle': 'En préparation', 'ordre': 200, 'couleur': '#7C3AED'},
        {'libelle': 'En livraison', 'ordre': 210, 'couleur': '#2563EB'},
        {'libelle': 'Livrée', 'ordre': 220, 'couleur': '#16A34A'},
        {'libelle': 'Retournée', 'ordre': 230, 'couleur': '#DC2626'},
    ]
    
    # États supplémentaires qui peuvent venir de la synchronisation Google Sheets
    etats_supplementaires = [
        {'libelle': 'En attente', 'ordre': 5, 'couleur': '#9CA3AF'},
        {'libelle': 'Annulée', 'ordre': 70, 'couleur': '#EF4444'},
        {'libelle': 'Reportée', 'ordre': 35, 'couleur': '#F59E0B'},
        {'libelle': 'Hors zone', 'ordre': 80, 'couleur': '#6B7280'},
        {'libelle': 'Injoignable', 'ordre': 55, 'couleur': '#F97316'},
        {'libelle': 'Pas de réponse', 'ordre': 56, 'couleur': '#F97316'},
        {'libelle': 'Numéro incorrect', 'ordre': 57, 'couleur': '#EF4444'},
        {'libelle': 'Échoué', 'ordre': 58, 'couleur': '#EF4444'},
        {'libelle': 'Expédiée', 'ordre': 205, 'couleur': '#3B82F6'},
    ]
    
    # Combiner tous les états
    tous_les_etats = etats_commande + etats_paiement + etats_livraison + etats_supplementaires
    
    # Créer les états qui n'existent pas déjà
    for etat_data in tous_les_etats:
        EnumEtatCmd.objects.get_or_create(
            libelle=etat_data['libelle'],
            defaults={
                'ordre': etat_data['ordre'],
                'couleur': etat_data['couleur']
            }
        )


def reverse_populate_etats_commande(apps, schema_editor):
    """Fonction de rollback - ne fait rien pour préserver les données"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('commande', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            populate_etats_commande,
            reverse_populate_etats_commande,
        ),
    ] 