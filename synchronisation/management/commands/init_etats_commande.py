from django.core.management.base import BaseCommand
from commande.models import EnumEtatCmd


class Command(BaseCommand):
    help = 'Initialise les états de commande de base nécessaires pour la synchronisation'

    def handle(self, *args, **options):
        """Crée les états de commande de base s'ils n'existent pas"""
        
        # États de base nécessaires pour la synchronisation
        etats_base = [
            {'libelle': 'Non affectée', 'ordre': 1, 'couleur': '#EF4444'},
            {'libelle': 'Affectée', 'ordre': 2, 'couleur': '#F59E0B'},
            {'libelle': 'Erronée', 'ordre': 3, 'couleur': '#DC2626'},
            {'libelle': 'Doublon', 'ordre': 4, 'couleur': '#7C2D12'},
            {'libelle': 'En cours de confirmation', 'ordre': 5, 'couleur': '#3B82F6'},
            {'libelle': 'Confirmée', 'ordre': 6, 'couleur': '#10B981'},
            {'libelle': 'Annulée', 'ordre': 7, 'couleur': '#6B7280'},
            {'libelle': 'En attente', 'ordre': 8, 'couleur': '#F59E0B'},
            {'libelle': 'Reportée', 'ordre': 9, 'couleur': '#8B5CF6'},
            {'libelle': 'Hors zone', 'ordre': 10, 'couleur': '#EF4444'},
            {'libelle': 'Injoignable', 'ordre': 11, 'couleur': '#6B7280'},
            {'libelle': 'Pas de réponse', 'ordre': 12, 'couleur': '#6B7280'},
            {'libelle': 'Numéro incorrect', 'ordre': 13, 'couleur': '#DC2626'},
            {'libelle': 'Échoué', 'ordre': 14, 'couleur': '#DC2626'},
            {'libelle': 'Expédiée', 'ordre': 15, 'couleur': '#3B82F6'},
            {'libelle': 'En préparation', 'ordre': 16, 'couleur': '#F59E0B'},
            {'libelle': 'En livraison', 'ordre': 17, 'couleur': '#8B5CF6'},
            {'libelle': 'Livrée', 'ordre': 18, 'couleur': '#10B981'},
            {'libelle': 'Retournée', 'ordre': 19, 'couleur': '#EF4444'},
            {'libelle': 'Non payé', 'ordre': 20, 'couleur': '#DC2626'},
            {'libelle': 'Partiellement payé', 'ordre': 21, 'couleur': '#F59E0B'},
            {'libelle': 'Payé', 'ordre': 22, 'couleur': '#10B981'},
        ]
        
        created_count = 0
        updated_count = 0
        
        for etat_data in etats_base:
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
                    self.style.SUCCESS(f"✅ État créé: {etat.libelle}")
                )
            else:
                # Mettre à jour l'ordre et la couleur si nécessaire
                if etat.ordre != etat_data['ordre'] or etat.couleur != etat_data['couleur']:
                    etat.ordre = etat_data['ordre']
                    etat.couleur = etat_data['couleur']
                    etat.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f"🔄 État mis à jour: {etat.libelle}")
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ État existant: {etat.libelle}")
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Initialisation terminée:\n"
                f"   - {created_count} nouveaux états créés\n"
                f"   - {updated_count} états mis à jour\n"
                f"   - {len(etats_base)} états au total"
            )
        )
