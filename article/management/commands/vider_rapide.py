from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Vide rapidement toute la base de données'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirme l\'opération sans demander de confirmation'
        )

    def handle(self, *args, **options):
        confirm = options['confirm']

        self.stdout.write(
            self.style.WARNING(
                '⚠️  ATTENTION : Cette opération va supprimer TOUTES les données de la base !'
            )
        )

        if not confirm:
            self.stdout.write(
                self.style.ERROR(
                    'Pour confirmer, utilisez --confirm ou répondez "oui" à la question suivante'
                )
            )
            user_input = input('Êtes-vous sûr de vouloir vider TOUTE la base ? (oui/non): ')
            if user_input.lower() not in ['oui', 'yes', 'o', 'y']:
                self.stdout.write(self.style.SUCCESS('Opération annulée.'))
                return

        self.stdout.write('🧹 Vidage rapide de la base de données...')

        try:
            with connection.cursor() as cursor:
                # Désactiver temporairement les contraintes de clés étrangères
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
                
                # Récupérer toutes les tables
                cursor.execute("SHOW TABLES;")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Vider chaque table
                for table in tables:
                    if table != 'django_migrations':  # Ne pas vider les migrations
                        cursor.execute(f"TRUNCATE TABLE {table};")
                        self.stdout.write(f"   - Table {table} vidée")
                
                # Réactiver les contraintes
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
                
            self.stdout.write(
                self.style.SUCCESS('✅ Base de données vidée avec succès !')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Erreur lors du vidage : {e}')
            )
            self.stdout.write(
                self.style.WARNING('Essayez le script vider_base_donnees.py avec l\'option --hard')
            )
