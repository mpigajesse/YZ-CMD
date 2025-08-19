import os
from django.core.management.base import BaseCommand
from django.db import transaction
from django.conf import settings
from article.models import Article, Categorie, Genre, Pointure, Couleur, VarianteArticle, MouvementStock, Promotion
from commande.models import Commande, Panier, EtatCommande, Operation, EnumEtatCmd
from client.models import Client
from parametre.models import Operateur, Ville, Region
from kpis.models import KPIConfiguration


class Command(BaseCommand):
    help = 'Vide la base de données selon différentes options'

    def add_arguments(self, parser):
        parser.add_argument(
            '--option',
            type=str,
            choices=['articles', 'commandes', 'clients', 'operateurs', 'tout', 'soft', 'hard'],
            default='tout',
            help='Option de nettoyage (défaut: tout)'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirme l\'opération sans demander de confirmation'
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Crée une sauvegarde avant de vider (si possible)'
        )

    def handle(self, *args, **options):
        option = options['option']
        confirm = options['confirm']
        backup = options['backup']

        self.stdout.write(
            self.style.WARNING(
                '⚠️  ATTENTION : Cette opération va supprimer des données de la base !'
            )
        )

        if not confirm:
            self.stdout.write(
                self.style.ERROR(
                    'Pour confirmer, utilisez --confirm ou répondez "oui" à la question suivante'
                )
            )
            user_input = input('Êtes-vous sûr de vouloir continuer ? (oui/non): ')
            if user_input.lower() not in ['oui', 'yes', 'o', 'y']:
                self.stdout.write(self.style.SUCCESS('Opération annulée.'))
                return

        # Créer une sauvegarde si demandée
        if backup:
            self.creer_sauvegarde()

        # Exécuter le nettoyage selon l'option
        if option == 'tout':
            self.vider_tout()
        elif option == 'articles':
            self.vider_articles()
        elif option == 'commandes':
            self.vider_commandes()
        elif option == 'clients':
            self.vider_clients()
        elif option == 'operateurs':
            self.vider_operateurs()
        elif option == 'soft':
            self.soft_reset()
        elif option == 'hard':
            self.hard_reset()

        self.stdout.write(
            self.style.SUCCESS('✅ Nettoyage terminé avec succès !')
        )

    def creer_sauvegarde(self):
        """Crée une sauvegarde de la base de données si possible"""
        try:
            from django.core.management import call_command
            from datetime import datetime
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f'backup_{timestamp}.json'
            
            self.stdout.write(f'📦 Création de la sauvegarde : {backup_file}')
            
            # Créer une sauvegarde des données principales
            call_command('dumpdata', 
                        'article', 'commande', 'client', 'parametre',
                        '--indent=2',
                        f'--output={backup_file}')
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Sauvegarde créée : {backup_file}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Impossible de créer la sauvegarde : {e}')
            )

    def vider_tout(self):
        """Vide complètement la base de données"""
        self.stdout.write('🧹 Nettoyage complet de la base de données...')
        
        with transaction.atomic():
            # Supprimer dans l'ordre pour respecter les contraintes
            
            # 1. Supprimer les mouvements de stock
            count = MouvementStock.objects.all().delete()[0]
            self.stdout.write(f'   - {count} mouvements de stock supprimés')
            
            # 2. Supprimer les variantes d'articles
            count = VarianteArticle.objects.all().delete()[0]
            self.stdout.write(f'   - {count} variantes d\'articles supprimées')
            
            # 3. Supprimer les promotions
            count = Promotion.objects.all().delete()[0]
            self.stdout.write(f'   - {count} promotions supprimées')
            
            # 4. Supprimer les articles
            count = Article.objects.all().delete()[0]
            self.stdout.write(f'   - {count} articles supprimés')
            
            # 5. Supprimer les opérations
            count = Operation.objects.all().delete()[0]
            self.stdout.write(f'   - {count} opérations supprimées')
            
            # 6. Supprimer les états de commande
            count = EtatCommande.objects.all().delete()[0]
            self.stdout.write(f'   - {count} états de commande supprimés')
            
            # 7. Supprimer les paniers
            count = Panier.objects.all().delete()[0]
            self.stdout.write(f'   - {count} paniers supprimés')
            
            # 8. Supprimer les commandes
            count = Commande.objects.all().delete()[0]
            self.stdout.write(f'   - {count} commandes supprimées')
            
            # 9. Supprimer les clients
            count = Client.objects.all().delete()[0]
            self.stdout.write(f'   - {count} clients supprimés')
            
            # 10. Supprimer les opérateurs
            count = Operateur.objects.all().delete()[0]
            self.stdout.write(f'   - {count} opérateurs supprimés')
            
            # 11. Supprimer les villes
            count = Ville.objects.all().delete()[0]
            self.stdout.write(f'   - {count} villes supprimées')
            
            # 12. Supprimer les régions
            count = Region.objects.all().delete()[0]
            self.stdout.write(f'   - {count} régions supprimées')
            
            # 13. Supprimer les catégories
            count = Categorie.objects.all().delete()[0]
            self.stdout.write(f'   - {count} catégories supprimées')
            
            # 14. Supprimer les genres
            count = Genre.objects.all().delete()[0]
            self.stdout.write(f'   - {count} genres supprimés')
            
            # 15. Supprimer les pointures
            count = Pointure.objects.all().delete()[0]
            self.stdout.write(f'   - {count} pointures supprimées')
            
            # 16. Supprimer les couleurs
            count = Couleur.objects.all().delete()[0]
            self.stdout.write(f'   - {count} couleurs supprimées')
            
            # 17. Supprimer les états de commande énumérés
            count = EnumEtatCmd.objects.all().delete()[0]
            self.stdout.write(f'   - {count} états de commande énumérés supprimés')
            
            # 18. Supprimer les configurations KPI
            count = KPIConfiguration.objects.all().delete()[0]
            self.stdout.write(f'   - {count} configurations KPI supprimées')

    def vider_articles(self):
        """Vide uniquement les articles et leurs variantes"""
        self.stdout.write('🧹 Nettoyage des articles...')
        
        with transaction.atomic():
            # Supprimer les mouvements de stock
            count = MouvementStock.objects.all().delete()[0]
            self.stdout.write(f'   - {count} mouvements de stock supprimés')
            
            # Supprimer les variantes
            count = VarianteArticle.objects.all().delete()[0]
            self.stdout.write(f'   - {count} variantes d\'articles supprimées')
            
            # Supprimer les promotions
            count = Promotion.objects.all().delete()[0]
            self.stdout.write(f'   - {count} promotions supprimées')
            
            # Supprimer les articles
            count = Article.objects.all().delete()[0]
            self.stdout.write(f'   - {count} articles supprimés')

    def vider_commandes(self):
        """Vide uniquement les commandes et leurs données associées"""
        self.stdout.write('🧹 Nettoyage des commandes...')
        
        with transaction.atomic():
            # Supprimer les opérations
            count = Operation.objects.all().delete()[0]
            self.stdout.write(f'   - {count} opérations supprimées')
            
            # Supprimer les états de commande
            count = EtatCommande.objects.all().delete()[0]
            self.stdout.write(f'   - {count} états de commande supprimés')
            
            # Supprimer les paniers
            count = Panier.objects.all().delete()[0]
            self.stdout.write(f'   - {count} paniers supprimés')
            
            # Supprimer les commandes
            count = Commande.objects.all().delete()[0]
            self.stdout.write(f'   - {count} commandes supprimées')

    def vider_clients(self):
        """Vide uniquement les clients"""
        self.stdout.write('🧹 Nettoyage des clients...')
        
        with transaction.atomic():
            # Supprimer les clients (les commandes seront supprimées en cascade)
            count = Client.objects.all().delete()[0]
            self.stdout.write(f'   - {count} clients supprimés')

    def vider_operateurs(self):
        """Vide uniquement les opérateurs"""
        self.stdout.write('🧹 Nettoyage des opérateurs...')
        
        with transaction.atomic():
            # Supprimer les opérateurs
            count = Operateur.objects.all().delete()[0]
            self.stdout.write(f'   - {count} opérateurs supprimés')

    def soft_reset(self):
        """Reset soft : désactive les éléments au lieu de les supprimer"""
        self.stdout.write('🧹 Reset soft (désactivation)...')
        
        with transaction.atomic():
            # Désactiver les articles
            count = Article.objects.filter(actif=True).update(actif=False)
            self.stdout.write(f'   - {count} articles désactivés')
            
            # Désactiver les variantes
            count = VarianteArticle.objects.filter(actif=True).update(actif=False)
            self.stdout.write(f'   - {count} variantes désactivées')
            
            # Désactiver les catégories
            count = Categorie.objects.filter(actif=True).update(actif=False)
            self.stdout.write(f'   - {count} catégories désactivées')
            
            # Désactiver les genres
            count = Genre.objects.filter(actif=True).update(actif=False)
            self.stdout.write(f'   - {count} genres désactivés')
            
            # Désactiver les pointures
            count = Pointure.objects.filter(actif=True).update(actif=False)
            self.stdout.write(f'   - {count} pointures désactivées')
            
            # Désactiver les couleurs
            count = Couleur.objects.filter(actif=True).update(actif=False)
            self.stdout.write(f'   - {count} couleurs désactivées')
            
            # Désactiver les opérateurs
            count = Operateur.objects.filter(actif=True).update(actif=False)
            self.stdout.write(f'   - {count} opérateurs désactivés')
            
            # Désactiver les clients
            count = Client.objects.filter(is_active=True).update(is_active=False)
            self.stdout.write(f'   - {count} clients désactivés')

    def hard_reset(self):
        """Reset hard : supprime tout et recrée les données de base"""
        self.stdout.write('🧹 Reset hard (suppression complète + recréation)...')
        
        # D'abord tout supprimer
        self.vider_tout()
        
        # Puis recréer les données de base
        self.creer_donnees_base()

    def creer_donnees_base(self):
        """Crée les données de base nécessaires au fonctionnement"""
        self.stdout.write('🔧 Création des données de base...')
        
        with transaction.atomic():
            # Créer les catégories de base
            categories = [
                'SANDALES', 'SABOT', 'CHAUSSURES', 'ESPARILLE', 
                'BASKET', 'MULES', 'PACK_SAC', 'BOTTE', 'ESCARPINS'
            ]
            for cat in categories:
                Categorie.objects.get_or_create(nom=cat)
            self.stdout.write(f'   - {len(categories)} catégories créées')
            
            # Créer les genres de base
            genres = ['HOMME', 'FEMME', 'FILLE', 'GARCON']
            for gen in genres:
                Genre.objects.get_or_create(nom=gen)
            self.stdout.write(f'   - {len(genres)} genres créés')
            
            # Créer les pointures de base
            pointures = ['35', '36', '37', '38', '39', '40', '41', '42', '43', '44', '45']
            for i, point in enumerate(pointures):
                Pointure.objects.get_or_create(
                    pointure=point,
                    defaults={'ordre': i}
                )
            self.stdout.write(f'   - {len(pointures)} pointures créées')
            
            # Créer les couleurs de base
            couleurs = ['Noir', 'Blanc', 'Beige', 'Marron', 'Bleu', 'Rouge', 'Vert']
            for couleur in couleurs:
                Couleur.objects.get_or_create(nom=couleur)
            self.stdout.write(f'   - {len(couleurs)} couleurs créées')
            
            # Créer les états de commande de base
            etats = [
                ('Nouvelle', 1, '#3B82F6'),
                ('Confirmée', 2, '#10B981'),
                ('En préparation', 3, '#F59E0B'),
                ('Prête', 4, '#8B5CF6'),
                ('Expédiée', 5, '#06B6D4'),
                ('Livrée', 6, '#059669'),
                ('Annulée', 7, '#EF4444'),
            ]
            for libelle, ordre, couleur in etats:
                EnumEtatCmd.objects.get_or_create(
                    libelle=libelle,
                    defaults={'ordre': ordre, 'couleur': couleur}
                )
            self.stdout.write(f'   - {len(etats)} états de commande créés')
            
            # Créer une région et une ville par défaut
            region, _ = Region.objects.get_or_create(nom_region='Casablanca-Settat')
            ville, _ = Ville.objects.get_or_create(
                nom='Casablanca',
                defaults={
                    'frais_livraison': 30.0,
                    'frequence_livraison': 'Quotidienne',
                    'region': region
                }
            )
            self.stdout.write('   - Région et ville par défaut créées')

    def afficher_statistiques(self):
        """Affiche les statistiques actuelles de la base"""
        self.stdout.write('\n📊 Statistiques actuelles de la base :')
        self.stdout.write(f'   - Articles : {Article.objects.count()}')
        self.stdout.write(f'   - Variantes : {VarianteArticle.objects.count()}')
        self.stdout.write(f'   - Commandes : {Commande.objects.count()}')
        self.stdout.write(f'   - Clients : {Client.objects.count()}')
        self.stdout.write(f'   - Opérateurs : {Operateur.objects.count()}')
        self.stdout.write(f'   - Catégories : {Categorie.objects.count()}')
        self.stdout.write(f'   - Genres : {Genre.objects.count()}')
        self.stdout.write(f'   - Pointures : {Pointure.objects.count()}')
        self.stdout.write(f'   - Couleurs : {Couleur.objects.count()}')
