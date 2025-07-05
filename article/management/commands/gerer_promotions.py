from django.core.management.base import BaseCommand
from django.utils import timezone
from article.models import Promotion

class Command(BaseCommand):
    help = 'Gère automatiquement les promotions selon leur date et statut'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les actions qui seraient effectuées sans les exécuter',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche des informations détaillées',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        now = timezone.now()
        
        # Statistiques
        stats = {
            'activated': 0,
            'deactivated': 0,
            'articles_updated': 0,
            'no_change': 0
        }
        
        # Récupérer toutes les promotions
        all_promotions = Promotion.objects.all()
        
        self.stdout.write(self.style.SUCCESS(f'Début de la gestion automatique des promotions...'))
        self.stdout.write(f'Promotions trouvées: {all_promotions.count()}')
        
        for promotion in all_promotions:
            if verbose:
                self.stdout.write(f'Traitement de la promotion: {promotion.nom}')
                self.stdout.write(f'  - Période: {promotion.date_debut} à {promotion.date_fin}')
                self.stdout.write(f'  - Statut actuel: {"Actif" if promotion.active else "Inactif"}')
                self.stdout.write(f'  - Articles associés: {promotion.articles.count()}')
            
            if not dry_run:
                result = promotion.verifier_et_appliquer_automatiquement()
            else:
                # Simulation pour dry-run
                if (promotion.date_debut <= now <= promotion.date_fin and not promotion.active):
                    result = "activated"
                elif (now > promotion.date_fin and promotion.active):
                    result = "deactivated"
                else:
                    result = "no_change"
            
            if result == "activated":
                stats['activated'] += 1
                stats['articles_updated'] += promotion.articles.count()
                action_msg = f'✅ Promotion activée: {promotion.nom}'
            elif result == "deactivated":
                stats['deactivated'] += 1
                stats['articles_updated'] += promotion.articles.count()
                action_msg = f'❌ Promotion désactivée: {promotion.nom}'
            else:
                stats['no_change'] += 1
                action_msg = f'➖ Aucun changement: {promotion.nom}'
            
            if verbose:
                self.stdout.write(f'  - {action_msg}')
        
        # Résumé
        self.stdout.write(self.style.SUCCESS('\n=== RÉSUMÉ ==='))
        if dry_run:
            self.stdout.write(self.style.WARNING('Mode simulation (dry-run) - Aucune modification effectuée'))
        
        self.stdout.write(f'Promotions activées: {stats["activated"]}')
        self.stdout.write(f'Promotions désactivées: {stats["deactivated"]}')
        self.stdout.write(f'Articles mis à jour: {stats["articles_updated"]}')
        self.stdout.write(f'Promotions inchangées: {stats["no_change"]}')
        
        if stats['activated'] > 0 or stats['deactivated'] > 0:
            self.stdout.write(self.style.SUCCESS(f'Gestion automatique terminée avec succès!'))
        else:
            self.stdout.write(self.style.SUCCESS('Aucune promotion à traiter automatiquement.')) 