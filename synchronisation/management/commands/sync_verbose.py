from django.core.management.base import BaseCommand, CommandError
from synchronisation.models import GoogleSheetConfig
from synchronisation.google_sheet_sync import GoogleSheetSync


class Command(BaseCommand):
    help = 'Synchronise les données Google Sheets en mode verbose (avec affichage détaillé)'

    def add_arguments(self, parser):
        parser.add_argument(
            'config_id',
            type=int,
            help='ID de la configuration Google Sheets à synchroniser'
        )
        parser.add_argument(
            '--user',
            type=str,
            default='admin',
            help='Nom de l\'utilisateur qui déclenche la synchronisation (défaut: admin)'
        )

    def handle(self, *args, **options):
        config_id = options['config_id']
        triggered_by = options['user']

        try:
            # Récupérer la configuration
            config = GoogleSheetConfig.objects.get(pk=config_id, is_active=True)
            
            self.stdout.write(
                self.style.SUCCESS(f'🔄 Démarrage de la synchronisation pour "{config.sheet_name}" en mode verbose...')
            )
            
            # Créer une instance de synchronisation en mode verbose
            syncer = GoogleSheetSync(config, triggered_by=triggered_by, verbose=True)
            success = syncer.sync()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Synchronisation réussie !\n'
                        f'   • Nouvelles commandes créées: {syncer.new_orders_created}\n'
                        f'   • Commandes mises à jour: {syncer.existing_orders_updated}\n'
                        f'   • Commandes inchangées: {syncer.existing_orders_skipped}\n'
                        f'   • Doublons évités: {syncer.duplicate_orders_found}\n'
                        f'   • Résumé: {syncer.execution_details.get("sync_summary", "N/A")}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f'❌ Synchronisation échouée !\n'
                        f'   • Erreurs: {len(syncer.errors)}\n'
                        f'   • Détails: {"; ".join(syncer.errors) if syncer.errors else "Aucun détail disponible"}'
                    )
                )
                
        except GoogleSheetConfig.DoesNotExist:
            raise CommandError(f'Configuration avec ID {config_id} non trouvée ou inactive.')
        except Exception as e:
            raise CommandError(f'Erreur lors de la synchronisation: {str(e)}') 