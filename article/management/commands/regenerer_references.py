from django.core.management.base import BaseCommand
from django.db import transaction
from article.models import Article, VarianteArticle


class Command(BaseCommand):
    help = 'Régénère automatiquement les références des articles et des variantes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans l\'exécuter'
        )
        parser.add_argument(
            '--articles-only',
            action='store_true',
            help='Régénère uniquement les références des articles'
        )
        parser.add_argument(
            '--variantes-only',
            action='store_true',
            help='Régénère uniquement les références des variantes'
        )
        parser.add_argument(
            '--force-all',
            action='store_true',
            help='Force la régénération même si une référence existe déjà'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        articles_only = options['articles_only']
        variantes_only = options['variantes_only']
        force_all = options['force_all']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('Mode DRY-RUN activé - Aucune donnée ne sera modifiée')
            )

        articles_updated = 0
        variantes_updated = 0

        # Régénérer les références des articles
        if not variantes_only:
            self.stdout.write('Régénération des références des articles...')
            
            # Récupérer les articles éligibles
            articles_queryset = Article.objects.filter(
                categorie__isnull=False,
                genre__isnull=False,
                modele__isnull=False
            )
            
            if not force_all:
                articles_queryset = articles_queryset.filter(reference__isnull=True)

            for article in articles_queryset:
                reference_auto = article.generer_reference_automatique()
                if reference_auto:
                    if dry_run:
                        if article.reference:
                            self.stdout.write(f'[DRY-RUN] Article {article.nom}: {article.reference} -> {reference_auto}')
                        else:
                            self.stdout.write(f'[DRY-RUN] Article {article.nom}: Aucune référence -> {reference_auto}')
                    else:
                        ancienne_ref = article.reference
                        article.reference = reference_auto
                        article.save()
                        
                        if ancienne_ref:
                            self.stdout.write(f'Article {article.nom}: {ancienne_ref} -> {reference_auto}')
                        else:
                            self.stdout.write(f'Article {article.nom}: Référence générée -> {reference_auto}')
                    
                    articles_updated += 1

        # Régénérer les références des variantes
        if not articles_only:
            self.stdout.write('Régénération des références des variantes...')
            
            # Récupérer les variantes éligibles
            variantes_queryset = VarianteArticle.objects.filter(
                article__reference__isnull=False,
                couleur__isnull=False,
                pointure__isnull=False
            )
            
            if not force_all:
                variantes_queryset = variantes_queryset.filter(reference_variante__isnull=True)

            for variante in variantes_queryset:
                reference_variante_auto = variante.generer_reference_variante_automatique()
                if reference_variante_auto:
                    if dry_run:
                        if variante.reference_variante:
                            self.stdout.write(f'[DRY-RUN] Variante {variante}: {variante.reference_variante} -> {reference_variante_auto}')
                        else:
                            self.stdout.write(f'[DRY-RUN] Variante {variante}: Aucune référence -> {reference_variante_auto}')
                    else:
                        ancienne_ref = variante.reference_variante
                        variante.reference_variante = reference_variante_auto
                        variante.save()
                        
                        if ancienne_ref:
                            self.stdout.write(f'Variante {variante}: {ancienne_ref} -> {reference_variante_auto}')
                        else:
                            self.stdout.write(f'Variante {variante}: Référence générée -> {reference_variante_auto}')
                    
                    variantes_updated += 1

        # Résumé final
        self.stdout.write('\n' + '='*50)
        self.stdout.write('RÉSUMÉ DE LA RÉGÉNÉRATION')
        self.stdout.write('='*50)
        
        if dry_run:
            self.stdout.write(f'Articles qui seraient mis à jour: {articles_updated}')
            self.stdout.write(f'Variantes qui seraient mises à jour: {variantes_updated}')
        else:
            self.stdout.write(f'Articles mis à jour: {articles_updated}')
            self.stdout.write(f'Variantes mises à jour: {variantes_updated}')

        if articles_updated == 0 and variantes_updated == 0:
            self.stdout.write(
                self.style.WARNING('Aucune référence à régénérer trouvée.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Régénération terminée avec succès!')
            )