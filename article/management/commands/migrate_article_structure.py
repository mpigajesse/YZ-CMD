from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.core.management import call_command
from article.models import Article, VarianteArticle, Categorie, Genre, Pointure, Couleur


class Command(BaseCommand):
    help = 'Migre la structure des articles vers le nouveau modèle avec variantes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la migration même si des erreurs sont détectées'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait migré sans effectuer la migration'
        )

    def handle(self, *args, **options):
        force = options['force']
        dry_run = options['dry_run']

        self.stdout.write('🔄 Migration de la structure des articles...')

        if dry_run:
            self.stdout.write(
                self.style.INFO('🔍 Mode dry-run - Aucune migration effectuée')
            )

        # 1. Vérifier la structure actuelle
        self.verifier_structure()

        # 2. Créer les données de base si nécessaire
        if not dry_run:
            self.creer_donnees_base()

        # 3. Migrer les articles existants
        if not dry_run:
            self.migrer_articles_existants()

        # 4. Nettoyer les contraintes obsolètes
        if not dry_run:
            self.nettoyer_contraintes()

        self.stdout.write(
            self.style.SUCCESS('✅ Migration terminée !')
        )

    def verifier_structure(self):
        """Vérifie la structure actuelle de la base"""
        self.stdout.write('🔍 Vérification de la structure...')

        # Vérifier les tables
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = [
                'article_article',
                'article_categorie', 
                'article_genre',
                'article_pointure',
                'article_couleur',
                'article_variantearticle'
            ]
            
            for table in required_tables:
                if table in tables:
                    self.stdout.write(f'   ✅ Table {table} existe')
                else:
                    self.stdout.write(
                        self.style.WARNING(f'   ⚠️  Table {table} manquante')
                    )

        # Vérifier les modèles
        try:
            self.stdout.write(f'   📊 Articles: {Article.objects.count()}')
            self.stdout.write(f'   📊 Variantes: {VarianteArticle.objects.count()}')
            self.stdout.write(f'   📊 Catégories: {Categorie.objects.count()}')
            self.stdout.write(f'   📊 Genres: {Genre.objects.count()}')
            self.stdout.write(f'   📊 Pointures: {Pointure.objects.count()}')
            self.stdout.write(f'   📊 Couleurs: {Couleur.objects.count()}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Erreur lors de la vérification: {e}')
            )

    def creer_donnees_base(self):
        """Crée les données de base nécessaires"""
        self.stdout.write('🔧 Création des données de base...')

        with transaction.atomic():
            # Créer les catégories de base
            categories = [
                'SANDALES', 'SABOT', 'CHAUSSURES', 'ESPARILLE', 
                'BASKET', 'MULES', 'PACK_SAC', 'BOTTE', 'ESCARPINS'
            ]
            for cat in categories:
                categorie, created = Categorie.objects.get_or_create(nom=cat)
                if created:
                    self.stdout.write(f'   - Catégorie "{cat}" créée')
                else:
                    self.stdout.write(f'   - Catégorie "{cat}" existe déjà')

            # Créer les genres de base
            genres = ['HOMME', 'FEMME', 'FILLE', 'GARCON']
            for gen in genres:
                genre, created = Genre.objects.get_or_create(nom=gen)
                if created:
                    self.stdout.write(f'   - Genre "{gen}" créé')
                else:
                    self.stdout.write(f'   - Genre "{gen}" existe déjà')

            # Créer les pointures de base
            pointures = ['35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45']
            for i, point in enumerate(pointures):
                pointure, created = Pointure.objects.get_or_create(
                    pointure=point,
                    defaults={'ordre': i}
                )
                if created:
                    self.stdout.write(f'   - Pointure "{point}" créée')
                else:
                    self.stdout.write(f'   - Pointure "{point}" existe déjà')

            # Créer les couleurs de base
            couleurs = ['Noir', 'Blanc', 'Beige', 'Marron', 'Bleu', 'Rouge', 'Vert']
            for couleur in couleurs:
                couleur_obj, created = Couleur.objects.get_or_create(nom=couleur)
                if created:
                    self.stdout.write(f'   - Couleur "{couleur}" créée')
                else:
                    self.stdout.write(f'   - Couleur "{couleur}" existe déjà')

    def migrer_articles_existants(self):
        """Migre les articles existants vers la nouvelle structure"""
        self.stdout.write('🔄 Migration des articles existants...')

        # Récupérer tous les articles
        articles = Article.objects.all()
        
        if not articles.exists():
            self.stdout.write('   - Aucun article à migrer')
            return

        with transaction.atomic():
            for article in articles:
                try:
                    # Vérifier si l'article a déjà des variantes
                    if article.variantes.exists():
                        self.stdout.write(f'   - Article "{article.nom}" a déjà des variantes')
                        continue

                    # Créer une variante par défaut
                    # Utiliser les premières couleurs et pointures disponibles
                    couleur = Couleur.objects.filter(actif=True).first()
                    pointure = Pointure.objects.filter(actif=True).first()

                    if couleur and pointure:
                        VarianteArticle.objects.create(
                            article=article,
                            couleur=couleur,
                            pointure=pointure,
                            qte_disponible=0,  # Quantité par défaut
                            prix_unitaire=article.prix_unitaire,
                            prix_achat=article.prix_achat or 0,
                            actif=article.actif
                        )
                        self.stdout.write(f'   - Variante créée pour "{article.nom}"')
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'   ⚠️  Impossible de créer une variante pour "{article.nom}" - couleurs/pointures manquantes')
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Erreur lors de la migration de "{article.nom}": {e}')
                    )

    def nettoyer_contraintes(self):
        """Nettoie les contraintes obsolètes"""
        self.stdout.write('🧹 Nettoyage des contraintes obsolètes...')

        try:
            with connection.cursor() as cursor:
                # Vérifier les contraintes existantes
                cursor.execute("""
                    SELECT 
                        CONSTRAINT_NAME,
                        TABLE_NAME,
                        COLUMN_NAME
                    FROM 
                        INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
                    WHERE 
                        TABLE_SCHEMA = DATABASE()
                        AND TABLE_NAME = 'article_article'
                """)
                
                constraints = cursor.fetchall()
                
                for constraint in constraints:
                    constraint_name, table, column = constraint
                    
                    # Supprimer les contraintes obsolètes
                    if 'unique_together' in constraint_name.lower():
                        try:
                            cursor.execute(f"ALTER TABLE {table} DROP INDEX {constraint_name}")
                            self.stdout.write(f'   - Contrainte {constraint_name} supprimée')
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f'   ⚠️  Impossible de supprimer {constraint_name}: {e}')
                            )

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'   ⚠️  Erreur lors du nettoyage des contraintes: {e}')
            )

    def afficher_statistiques_finales(self):
        """Affiche les statistiques finales"""
        self.stdout.write('\n📊 Statistiques finales :')
        try:
            self.stdout.write(f'   - Articles : {Article.objects.count()}')
            self.stdout.write(f'   - Variantes : {VarianteArticle.objects.count()}')
            self.stdout.write(f'   - Catégories : {Categorie.objects.count()}')
            self.stdout.write(f'   - Genres : {Genre.objects.count()}')
            self.stdout.write(f'   - Pointures : {Pointure.objects.count()}')
            self.stdout.write(f'   - Couleurs : {Couleur.objects.count()}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Erreur lors de l\'affichage des statistiques: {e}')
            )
