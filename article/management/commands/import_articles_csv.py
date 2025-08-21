import csv
import os
import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from article.models import Article, Categorie, Genre, Pointure, Couleur, VarianteArticle
from parametre.models import Operateur


class Command(BaseCommand):
    help = 'Importe les articles depuis un fichier CSV avec leurs variantes selon la structure YOOZAK'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Chemin vers le fichier CSV à importer'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait importé sans effectuer l\'importation'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Met à jour les articles existants au lieu de les ignorer'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        update_existing = options['update_existing']

        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'Le fichier {csv_file} n\'existe pas.')
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING('Mode DRY-RUN activé - Aucune donnée ne sera importée')
            )

        # Mapping des phases du CSV vers les phases du modèle
        phase_mapping = {
            'EN COUR': 'EN_COURS',
            'EN TEST': 'EN_TEST',
            'EN LIQUIDATION': 'LIQUIDATION',
            'PROMO': 'PROMO'
        }

        # Mapping des catégories du CSV vers les catégories du modèle
        categorie_mapping = {
            'SANDALE': 'SANDALES',
            'SABOT': 'SABOT',
            'CHAUSSURE': 'CHAUSSURES',
            'ESPADRILLE': 'ESPARILLE',
            'BASKET': 'BASKET',
            'MULES': 'MULES',
            'PACK': 'PACK_SAC',
            'BOTTE': 'BOTTE',
            'ESCARPINS': 'ESCARPINS',
            'SAC': 'PACK_SAC'  # Les sacs sont dans la catégorie PACK_SAC
        }

        # Mapping des genres du CSV vers les genres du modèle
        genre_mapping = {
            'FEMME': 'FEMME',
            'HOMME': 'HOMME',
            'FILLE': 'FILLE',
            'GARCON': 'GARCON'
        }

        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                articles_created = 0
                articles_updated = 0
                articles_skipped = 0
                variantes_created = 0
                errors = []

                for row_num, row in enumerate(reader, start=2):  # Commencer à 2 car la ligne 1 est l'en-tête
                    try:
                        # Vérifier que les données essentielles sont présentes
                        if not row.get('REF ARTICLE'):
                            self.stdout.write(
                                self.style.WARNING(f'Ligne {row_num}: Référence manquante, ignorée')
                            )
                            articles_skipped += 1
                            continue

                        # Nettoyer et valider les données
                        reference = row['REF ARTICLE'].strip()
                        nom = reference  # Le nom est égal à la référence pour l'instant
                        
                        if not reference:
                            articles_skipped += 1
                            continue

                        # Traiter la catégorie
                        categorie_csv = row.get('CATEGORIE', '').strip()
                        if categorie_csv in categorie_mapping:
                            categorie_nom = categorie_mapping[categorie_csv]
                        else:
                            categorie_nom = 'CHAUSSURES'  # Valeur par défaut

                        # Créer ou récupérer l'objet Categorie
                        try:
                            categorie_obj = Categorie.objects.get(nom=categorie_nom)
                        except Categorie.DoesNotExist:
                            # Créer la catégorie si elle n'existe pas
                            categorie_obj = Categorie.objects.create(
                                nom=categorie_nom,
                                description=f'Catégorie {categorie_nom}',
                                actif=True
                            )

                        # Traiter le genre
                        genre_csv = row.get('GENRE', '').strip()
                        if genre_csv in genre_mapping:
                            genre_nom = genre_mapping[genre_csv]
                        else:
                            genre_nom = 'FEMME'  # Valeur par défaut

                        # Créer ou récupérer l'objet Genre
                        try:
                            genre_obj = Genre.objects.get(nom=genre_nom)
                        except Genre.DoesNotExist:
                            # Créer le genre s'il n'existe pas
                            genre_obj = Genre.objects.create(
                                nom=genre_nom,
                                description=f'Genre {genre_nom}',
                                actif=True
                            )

                        # Traiter la phase
                        phase_csv = row.get('PHASE', '').strip()
                        if phase_csv in phase_mapping:
                            phase = phase_mapping[phase_csv]
                        else:
                            phase = 'EN_COURS'  # Valeur par défaut

                        # Traiter le prix unitaire
                        prix_unitaire_str = row.get('PRIX UNITAIRE', '0').strip()
                        if prix_unitaire_str and prix_unitaire_str != '0':
                            # Nettoyer le prix (enlever "DH" et convertir en Decimal)
                            prix_unitaire_str = prix_unitaire_str.replace('DH', '').replace(',', '.').strip()
                            try:
                                prix_unitaire = Decimal(prix_unitaire_str)
                            except (ValueError, TypeError):
                                prix_unitaire = Decimal('0.00')
                        else:
                            prix_unitaire = Decimal('0.00')

                        # Traiter le prix de liquidation (prix d'achat)
                        prix_liquidation = self._parse_price(row.get('PRIX LIQ 1', ''))

                        # Traiter les prix upsell
                        prix_upsell_2 = self._parse_price(row.get('PRIX UPSEL 2', ''))
                        prix_upsell_3 = self._parse_price(row.get('PRIX UPSEL 3', ''))
                        prix_upsell_4 = self._parse_price(row.get('PRIX UPSEL 4', ''))

                        # Déterminer si c'est un article upsell
                        is_upsell = prix_upsell_2 is not None or prix_upsell_3 is not None or prix_upsell_4 is not None

                        # Extraire le numéro de modèle de la référence (ex: YZ478 -> 478)
                        modele = self._extract_modele(reference)

                        # Traiter les pointures
                        pointures_str = row.get('POINTURE', '').strip()
                        pointures = self._parse_pointures(pointures_str)

                        # Traiter les couleurs
                        couleurs_str = row.get('COULEUR', '').strip()
                        couleurs = self._parse_couleurs(couleurs_str)

                        # Vérifier si l'article existe déjà
                        article_existant = None
                        if reference:
                            article_existant = Article.objects.filter(reference=reference).first()
                        else:
                            # Si pas de référence, chercher par nom
                            article_existant = Article.objects.filter(nom=nom).first()

                        if article_existant and not update_existing:
                            self.stdout.write(
                                self.style.WARNING(f'Article existant ignoré: {nom} - {reference}')
                            )
                            articles_skipped += 1
                            continue

                        # Créer ou mettre à jour l'article
                        if dry_run:
                            if article_existant:
                                self.stdout.write(f'[DRY-RUN] Article à mettre à jour: {nom} - {reference}')
                            else:
                                self.stdout.write(f'[DRY-RUN] Article à créer: {nom} - {reference}')
                            
                            # Afficher les variantes qui seraient créées
                            for couleur in couleurs:
                                for pointure in pointures:
                                    self.stdout.write(f'  [DRY-RUN] Variante: {couleur} - {pointure}')
                            
                            articles_created += 1
                            variantes_created += len(couleurs) * len(pointures)
                            continue

                        # Créer ou mettre à jour l'article
                        if article_existant:
                            # Mise à jour
                            article_existant.nom = nom
                            article_existant.prix_unitaire = prix_unitaire
                            article_existant.prix_actuel = prix_unitaire
                            article_existant.categorie = categorie_obj
                            article_existant.genre = genre_obj
                            article_existant.phase = phase
                            article_existant.prix_achat = prix_liquidation if prix_liquidation else Decimal('0.00')
                            article_existant.isUpsell = is_upsell
                            article_existant.prix_upsell_2 = prix_upsell_2
                            article_existant.prix_upsell_3 = prix_upsell_3
                            article_existant.prix_upsell_4 = prix_upsell_4
                            article_existant.date_modification = timezone.now()
                            article_existant.save()
                            articles_updated += 1
                            
                            # Supprimer les anciennes variantes pour les recréer
                            VarianteArticle.objects.filter(article=article_existant).delete()
                            
                        else:
                            # Création
                            article = Article.objects.create(
                                nom=nom,
                                reference=reference if reference else None,
                                modele=modele,
                                prix_unitaire=prix_unitaire,
                                prix_achat=prix_liquidation if prix_liquidation else Decimal('0.00'),
                                prix_actuel=prix_unitaire,
                                categorie=categorie_obj,
                                genre=genre_obj,
                                phase=phase,
                                isUpsell=is_upsell,
                                prix_upsell_2=prix_upsell_2,
                                prix_upsell_3=prix_upsell_3,
                                prix_upsell_4=prix_upsell_4
                            )
                            articles_created += 1

                        # Créer les variantes pour toutes les combinaisons couleur/pointure
                        article_to_use = article_existant if article_existant else article
                        variantes_created_for_article = 0
                        
                        for couleur in couleurs:
                            for pointure in pointures:
                                try:
                                    # Créer ou récupérer la couleur
                                    couleur_obj, created = Couleur.objects.get_or_create(
                                        nom=couleur,
                                        defaults={'actif': True}
                                    )
                                    
                                    # Créer ou récupérer la pointure
                                    pointure_obj, created = Pointure.objects.get_or_create(
                                        pointure=pointure,
                                        defaults={'actif': True, 'ordre': int(pointure) if pointure.isdigit() else 0}
                                    )
                                    
                                    # Créer la variante
                                    variante = VarianteArticle.objects.create(
                                        article=article_to_use,
                                        couleur=couleur_obj,
                                        pointure=pointure_obj,
                                        qte_disponible=0,  # Valeur par défaut
                                        actif=True
                                    )
                                    
                                    variantes_created_for_article += 1
                                    
                                except Exception as e:
                                    self.stdout.write(
                                        self.style.ERROR(f'Erreur lors de la création de la variante {couleur}-{pointure}: {str(e)}')
                                    )
                        
                        variantes_created += variantes_created_for_article
                        
                        # Afficher le progrès
                        if (articles_created + articles_updated) % 10 == 0:
                            self.stdout.write(f'Articles traités: {articles_created + articles_updated + articles_skipped}')

                    except Exception as e:
                        error_msg = f'Ligne {row_num}: Erreur lors du traitement - {str(e)}'
                        self.stdout.write(self.style.ERROR(error_msg))
                        errors.append(error_msg)

                # Résumé final
                self.stdout.write('\n' + '='*50)
                self.stdout.write('RÉSUMÉ DE L\'IMPORTATION')
                self.stdout.write('='*50)
                
                if dry_run:
                    self.stdout.write(f'Articles qui seraient créés: {articles_created}')
                    self.stdout.write(f'Articles qui seraient mis à jour: {articles_updated}')
                    self.stdout.write(f'Articles ignorés: {articles_skipped}')
                    self.stdout.write(f'Variantes qui seraient créées: {variantes_created}')
                else:
                    self.stdout.write(f'Articles créés: {articles_created}')
                    self.stdout.write(f'Articles mis à jour: {articles_updated}')
                    self.stdout.write(f'Articles ignorés: {articles_skipped}')
                    self.stdout.write(f'Variantes créées: {variantes_created}')

                if errors:
                    self.stdout.write(f'\nErreurs rencontrées: {len(errors)}')
                    for error in errors[:5]:  # Afficher les 5 premières erreurs
                        self.stdout.write(f'  - {error}')
                    if len(errors) > 5:
                        self.stdout.write(f'  ... et {len(errors) - 5} autres erreurs')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erreur lors de la lecture du fichier CSV: {str(e)}')
            )

    def _parse_price(self, price_str):
        """Parse un prix depuis le CSV et le convertit en Decimal"""
        if not price_str or price_str.strip() == '':
            return None
        
        try:
            # Nettoyer le prix (enlever "DH" et convertir la virgule en point)
            clean_price = price_str.replace('DH', '').replace(',', '.').strip()
            return Decimal(clean_price)
        except (ValueError, TypeError):
            return None

    def _extract_modele(self, reference):
        """Extrait le numéro de modèle de la référence (ex: YZ478 -> 478)"""
        if not reference:
            return None
        
        # Chercher le pattern YZ suivi de chiffres
        match = re.search(r'YZ(\d+)', reference.upper())
        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                return None
        return None

    def _parse_pointures(self, pointures_str):
        """Parse les pointures depuis le CSV"""
        if not pointures_str or pointures_str.strip() == '':
            return []
        
        pointures = []
        # Parser les pointures (ex: "37---41" ou "37-41" ou "37---40")
        if '---' in pointures_str:
            parts = pointures_str.split('---')
        elif '-' in pointures_str:
            parts = pointures_str.split('-')
        else:
            parts = [pointures_str]
        
        if len(parts) >= 2:
            try:
                start = int(parts[0])
                end = int(parts[1])
                pointures = [str(i) for i in range(start, end + 1)]
            except (ValueError, IndexError):
                pointures = [pointures_str]
        else:
            pointures = [pointures_str]
        
        return pointures

    def _parse_couleurs(self, couleurs_str):
        """Parse les couleurs depuis le CSV"""
        if not couleurs_str or couleurs_str.strip() == '':
            return []
        
        couleurs = []
        # Parser les couleurs (séparées par des tirets ou des virgules)
        if '-' in couleurs_str:
            couleurs = [c.strip() for c in couleurs_str.split('-') if c.strip()]
        elif ',' in couleurs_str:
            couleurs = [c.strip() for c in couleurs_str.split(',') if c.strip()]
        else:
            couleurs = [couleurs_str]
        
        return couleurs
