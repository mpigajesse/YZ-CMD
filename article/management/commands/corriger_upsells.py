from django.core.management.base import BaseCommand
from django.utils import timezone
from article.models import Article

class Command(BaseCommand):
    help = 'Corrige automatiquement les upsells qui devraient être désactivés (articles en promotion, liquidation, ou test)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche les changements qui seraient effectués sans les appliquer',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affiche des informations détaillées sur les articles traités',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== MODE DRY-RUN ACTIVÉ - AUCUN CHANGEMENT NE SERA APPLIQUÉ ==='))
        
        # Récupérer tous les articles avec upsell actif
        articles_avec_upsell = Article.objects.filter(isUpsell=True, actif=True)
        
        if not articles_avec_upsell.exists():
            self.stdout.write(self.style.SUCCESS('✅ Aucun article avec upsell actif trouvé.'))
            return
        
        self.stdout.write(f'🔍 Analyse de {articles_avec_upsell.count()} article(s) avec upsell actif...')
        
        articles_a_corriger = []
        
        for article in articles_avec_upsell:
            should_disable = article.should_disable_upsell()
            
            if should_disable:
                reason = []
                if article.phase in ['LIQUIDATION', 'EN_TEST']:
                    reason.append(f"phase {article.phase}")
                if article.has_promo_active:
                    reason.append("en promotion active")
                
                articles_a_corriger.append({
                    'article': article,
                    'reasons': reason
                })
                
                if verbose:
                    reasons_str = " et ".join(reason)
                    self.stdout.write(f'  ⚠️  {article.nom} - {article.couleur} - {article.pointure} (ID: {article.id}) - Raisons: {reasons_str}')
        
        if not articles_a_corriger:
            self.stdout.write(self.style.SUCCESS('✅ Tous les upsells sont correctement configurés.'))
            return
        
        self.stdout.write(f'\n📊 Résumé des articles à corriger: {len(articles_a_corriger)}')
        
        # Statistiques par raison
        stats = {
            'liquidation': 0,
            'test': 0,
            'promotion': 0
        }
        
        for item in articles_a_corriger:
            reasons = item['reasons']
            for reason in reasons:
                if 'LIQUIDATION' in reason:
                    stats['liquidation'] += 1
                elif 'EN_TEST' in reason:
                    stats['test'] += 1
                elif 'promotion' in reason:
                    stats['promotion'] += 1
        
        self.stdout.write(f'  - Articles en liquidation: {stats["liquidation"]}')
        self.stdout.write(f'  - Articles en test: {stats["test"]}')
        self.stdout.write(f'  - Articles en promotion: {stats["promotion"]}')
        
        if not dry_run:
            self.stdout.write(f'\n🔧 Application des corrections...')
            
            corrected_count = 0
            for item in articles_a_corriger:
                article = item['article']
                try:
                    article.isUpsell = False
                    article.save(update_fields=['isUpsell'])
                    corrected_count += 1
                    
                    if verbose:
                        reasons_str = " et ".join(item['reasons'])
                        self.stdout.write(f'  ✅ {article.nom} - Upsell désactivé (Raisons: {reasons_str})')
                        
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Erreur lors de la correction de {article.nom}: {str(e)}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Correction terminée: {corrected_count} article(s) mis à jour.')
            )
        else:
            self.stdout.write(f'\n💡 Pour appliquer les corrections, exécutez la commande sans --dry-run') 