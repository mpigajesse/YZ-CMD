from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.core.exceptions import ValidationError
from article.models import Article, VarianteArticle, Categorie, Genre, Pointure, Couleur


class Command(BaseCommand):
    help = 'Corrige les contraintes de base de données et résout les problèmes de cohérence'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-all',
            action='store_true',
            help='Corrige tous les problèmes détectés'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait corrigé sans effectuer les corrections'
        )

    def handle(self, *args, **options):
        fix_all = options['fix_all']
        dry_run = options['dry_run']

        self.stdout.write('🔍 Vérification des contraintes de base de données...')

        # Vérifier et corriger les problèmes
        problems = self.detecter_problemes()
        
        if not problems:
            self.stdout.write(
                self.style.SUCCESS('✅ Aucun problème détecté !')
            )
            return

        self.stdout.write(f'⚠️  {len(problems)} problème(s) détecté(s) :')
        for i, problem in enumerate(problems, 1):
            self.stdout.write(f'   {i}. {problem["description"]}')

        if not fix_all:
            self.stdout.write(
                self.style.WARNING(
                    '\nPour corriger automatiquement, utilisez --fix-all'
                )
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.INFO('🔍 Mode dry-run - Aucune correction effectuée')
            )
            return

        # Corriger les problèmes
        self.stdout.write('\n🔧 Correction des problèmes...')
        self.corriger_problemes(problems)

        self.stdout.write(
            self.style.SUCCESS('✅ Correction terminée !')
        )

    def detecter_problemes(self):
        """Détecte tous les problèmes de contraintes"""
        problems = []

        # 1. Vérifier les articles avec des références manquantes
        try:
            articles_sans_categorie = Article.objects.filter(categorie__isnull=True)
            if articles_sans_categorie.exists():
                problems.append({
                    'type': 'articles_sans_categorie',
                    'description': f'{articles_sans_categorie.count()} article(s) sans catégorie',
                    'queryset': articles_sans_categorie
                })
        except Exception as e:
            problems.append({
                'type': 'erreur_categorie',
                'description': f'Erreur lors de la vérification des catégories: {e}',
                'queryset': None
            })

        # 2. Vérifier les variantes avec des références manquantes
        try:
            variantes_sans_article = VarianteArticle.objects.filter(article__isnull=True)
            if variantes_sans_article.exists():
                problems.append({
                    'type': 'variantes_sans_article',
                    'description': f'{variantes_sans_article.count()} variante(s) sans article',
                    'queryset': variantes_sans_article
                })
        except Exception as e:
            problems.append({
                'type': 'erreur_variantes',
                'description': f'Erreur lors de la vérification des variantes: {e}',
                'queryset': None
            })

        # 3. Vérifier les contraintes de clés étrangères
        try:
            with connection.cursor() as cursor:
                # Vérifier les contraintes de clés étrangères
                cursor.execute("""
                    SELECT 
                        TABLE_NAME,
                        COLUMN_NAME,
                        CONSTRAINT_NAME,
                        REFERENCED_TABLE_NAME,
                        REFERENCED_COLUMN_NAME
                    FROM 
                        INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE 
                        REFERENCED_TABLE_SCHEMA = DATABASE()
                        AND REFERENCED_TABLE_NAME IS NOT NULL
                """)
                
                foreign_keys = cursor.fetchall()
                for fk in foreign_keys:
                    table, column, constraint, ref_table, ref_column = fk
                    
                    # Vérifier si la table référencée existe
                    cursor.execute(f"SHOW TABLES LIKE '{ref_table}'")
                    if not cursor.fetchone():
                        problems.append({
                            'type': 'table_referencee_manquante',
                            'description': f'Table référencée manquante: {ref_table} (référencée par {table}.{column})',
                            'queryset': None
                        })
        except Exception as e:
            problems.append({
                'type': 'erreur_contraintes',
                'description': f'Erreur lors de la vérification des contraintes: {e}',
                'queryset': None
            })

        # 4. Vérifier les données orphelines
        try:
            # Articles sans variantes
            articles_sans_variantes = Article.objects.filter(variantes__isnull=True)
            if articles_sans_variantes.exists():
                problems.append({
                    'type': 'articles_sans_variantes',
                    'description': f'{articles_sans_variantes.count()} article(s) sans variantes',
                    'queryset': articles_sans_variantes
                })
        except Exception as e:
            problems.append({
                'type': 'erreur_variantes_articles',
                'description': f'Erreur lors de la vérification des variantes d\'articles: {e}',
                'queryset': None
            })

        return problems

    def corriger_problemes(self, problems):
        """Corrige tous les problèmes détectés"""
        with transaction.atomic():
            for problem in problems:
                try:
                    if problem['type'] == 'articles_sans_categorie':
                        self.corriger_articles_sans_categorie(problem['queryset'])
                    elif problem['type'] == 'variantes_sans_article':
                        self.corriger_variantes_sans_article(problem['queryset'])
                    elif problem['type'] == 'articles_sans_variantes':
                        self.corriger_articles_sans_variantes(problem['queryset'])
                    elif problem['type'] == 'table_referencee_manquante':
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  {problem["description"]} - Correction manuelle requise')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  {problem["description"]} - Type de problème non géré')
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Erreur lors de la correction de {problem["type"]}: {e}')
                    )

    def corriger_articles_sans_categorie(self, queryset):
        """Corrige les articles sans catégorie"""
        self.stdout.write(f'   🔧 Correction des articles sans catégorie...')
        
        # Créer une catégorie par défaut si elle n'existe pas
        categorie_defaut, created = Categorie.objects.get_or_create(
            nom='AUTRE',
            defaults={'description': 'Catégorie par défaut pour les articles non classés'}
        )
        
        if created:
            self.stdout.write(f'      - Catégorie par défaut "AUTRE" créée')
        
        # Assigner la catégorie par défaut aux articles
        count = queryset.update(categorie=categorie_defaut)
        self.stdout.write(f'      - {count} article(s) corrigé(s)')

    def corriger_variantes_sans_article(self, queryset):
        """Corrige les variantes sans article"""
        self.stdout.write(f'   🔧 Correction des variantes sans article...')
        
        # Supprimer les variantes orphelines
        count = queryset.count()
        queryset.delete()
        self.stdout.write(f'      - {count} variante(s) orpheline(s) supprimée(s)')

    def corriger_articles_sans_variantes(self, queryset):
        """Corrige les articles sans variantes"""
        self.stdout.write(f'   🔧 Correction des articles sans variantes...')
        
        # Créer des variantes par défaut pour les articles
        for article in queryset:
            try:
                # Créer une variante avec des valeurs par défaut
                VarianteArticle.objects.create(
                    article=article,
                    couleur=Couleur.objects.first() or self.creer_couleur_defaut(),
                    pointure=Pointure.objects.first() or self.creer_pointure_defaut(),
                    qte_disponible=0,
                    prix_unitaire=article.prix_unitaire,
                    prix_achat=article.prix_achat or 0,
                    actif=article.actif
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'      ❌ Erreur lors de la création de variante pour {article.nom}: {e}')
                )
        
        self.stdout.write(f'      - Variantes par défaut créées pour {queryset.count()} article(s)')

    def creer_couleur_defaut(self):
        """Crée une couleur par défaut"""
        couleur, created = Couleur.objects.get_or_create(
            nom='Non spécifiée',
            defaults={'description': 'Couleur par défaut'}
        )
        if created:
            self.stdout.write(f'      - Couleur par défaut "Non spécifiée" créée')
        return couleur

    def creer_pointure_defaut(self):
        """Crée une pointure par défaut"""
        pointure, created = Pointure.objects.get_or_create(
            pointure='Non spécifiée',
            defaults={'description': 'Pointure par défaut', 'ordre': 999}
        )
        if created:
            self.stdout.write(f'      - Pointure par défaut "Non spécifiée" créée')
        return pointure

    def afficher_statistiques(self):
        """Affiche les statistiques de la base"""
        self.stdout.write('\n📊 Statistiques de la base :')
        self.stdout.write(f'   - Articles : {Article.objects.count()}')
        self.stdout.write(f'   - Variantes : {VarianteArticle.objects.count()}')
        self.stdout.write(f'   - Catégories : {Categorie.objects.count()}')
        self.stdout.write(f'   - Couleurs : {Couleur.objects.count()}')
        self.stdout.write(f'   - Pointures : {Pointure.objects.count()}')
        self.stdout.write(f'   - Genres : {Genre.objects.count()}')
