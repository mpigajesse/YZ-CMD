from django.core.management.base import BaseCommand
from commande.models import EnumEtatCmd


class Command(BaseCommand):
    help = 'Peuple la base de données avec tous les états de commande nécessaires pour la synchronisation'

    def handle(self, *args, **options):
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
            {'libelle': 'À imprimer', 'ordre': 195, 'couleur': '#F59E0B'},
            {'libelle': 'En préparation', 'ordre': 200, 'couleur': '#7C3AED'},
            {'libelle': 'Préparée', 'ordre': 202, 'couleur': '#10B981'},
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
        
        created_count = 0
        updated_count = 0
        
        for etat_data in tous_les_etats:
            etat, created = EnumEtatCmd.objects.get_or_create(
                libelle=etat_data['libelle'],
                defaults={
                    'ordre': etat_data['ordre'],
                    'couleur': etat_data['couleur']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ État créé: {etat.libelle}')
                )
            else:
                # Mettre à jour l'ordre et la couleur si nécessaire
                if etat.ordre != etat_data['ordre'] or etat.couleur != etat_data['couleur']:
                    etat.ordre = etat_data['ordre']
                    etat.couleur = etat_data['couleur']
                    etat.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'🔄 État mis à jour: {etat.libelle}')
                    )
                else:
                    self.stdout.write(
                        self.style.HTTP_INFO(f'ℹ️  État existant: {etat.libelle}')
                    )
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(
            self.style.SUCCESS(
                f'✨ Terminé! {created_count} états créés, {updated_count} états mis à jour'
            )
        )
        self.stdout.write(
            self.style.HTTP_INFO(
                f'📊 Total des états dans la base: {EnumEtatCmd.objects.count()}'
            )
        ) 