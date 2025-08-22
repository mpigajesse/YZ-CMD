import csv
import os
import re
from decimal import Decimal, InvalidOperation
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
        parser.add_argument(
            '--verbose-colors',
            action='store_true',
            help='Affiche la normalisation des couleurs pendant l\'importation'
        )
        parser.add_argument(
            '--regenerate-references',
            action='store_true',
            help='Force la régénération des références même si elles existent déjà'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        dry_run = options['dry_run']
        update_existing = options['update_existing']
        verbose_colors = options['verbose_colors']
        regenerate_references = options['regenerate_references']

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

                        # Traiter le prix unitaire (parser robuste)
                        parsed_pu = self._parse_price(row.get('PRIX UNITAIRE', ''))
                        prix_unitaire = parsed_pu if parsed_pu is not None else Decimal('0.00')

                        # Traiter le prix de liquidation (prix d'achat)
                        prix_liquidation = self._parse_price(row.get('PRIX LIQ 1', ''))

                        # Traiter les prix upsell
                        prix_upsell_1 = self._parse_price(row.get('PRIX UPSEL 1', '')) # Au cas où il y en aurait un
                        prix_upsell_2 = self._parse_price(row.get('PRIX UPSEL 2', ''))
                        prix_upsell_3 = self._parse_price(row.get('PRIX UPSEL 3', ''))
                        prix_upsell_4 = self._parse_price(row.get('PRIX UPSEL 4', ''))

                        # Déterminer si c'est un article upsell
                        is_upsell = (prix_upsell_1 is not None or 
                                   prix_upsell_2 is not None or 
                                   prix_upsell_3 is not None or 
                                   prix_upsell_4 is not None)

                        # Extraire le numéro de modèle de la référence (ex: YZ478 -> 478)
                        modele = self._extract_modele(reference)

                        # Traiter les pointures
                        pointures_str = row.get('POINTURE', '').strip()
                        pointures = self._parse_pointures(pointures_str)

                        # Traiter les couleurs
                        couleurs_str = row.get('COULEUR', '').strip()
                        couleurs = self._parse_couleurs(couleurs_str)
                        
                        # Afficher les couleurs normalisées pour le suivi (si option activée)
                        if verbose_colors and couleurs_str and couleurs_str != '':
                            self.stdout.write(f'Couleurs CSV: "{couleurs_str}" -> Normalisées: {couleurs}')

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
                            article_existant.prix_upsell_1 = prix_upsell_1
                            article_existant.prix_upsell_2 = prix_upsell_2
                            article_existant.prix_upsell_3 = prix_upsell_3
                            article_existant.prix_upsell_4 = prix_upsell_4
                            # Mettre à jour modele uniquement si non conflictuel
                            if modele is not None:
                                # Si un autre article a déjà ce modele, ne pas l'écraser
                                if not Article.objects.filter(modele=modele).exclude(pk=article_existant.pk).exists():
                                    article_existant.modele = modele
                            article_existant.date_modification = timezone.now()
                            article_existant.save()
                            
                            # Générer automatiquement la référence si elle n'est pas définie ou si régénération forcée
                            if (not article_existant.reference or regenerate_references) and article_existant.categorie and article_existant.genre and article_existant.modele:
                                reference_auto = article_existant.generer_reference_automatique()
                                if reference_auto:
                                    ancienne_ref = article_existant.reference
                                    article_existant.reference = reference_auto
                                    article_existant.save()
                                    if ancienne_ref and regenerate_references:
                                        self.stdout.write(f'Référence régénérée: {ancienne_ref} -> {reference_auto}')
                                    else:
                                        self.stdout.write(f'Référence générée automatiquement (mise à jour): {reference_auto}')
                            
                            articles_updated += 1
                            
                            # Supprimer les anciennes variantes pour les recréer
                            VarianteArticle.objects.filter(article=article_existant).delete()
                            
                        else:
                            # Création
                            # Éviter les collisions sur le champ unique `modele`
                            if modele is not None and Article.objects.filter(modele=modele).exists():
                                modele_to_use = None
                            else:
                                modele_to_use = modele
                            article = Article.objects.create(
                                nom=nom,
                                reference=reference if reference else None,
                                modele=modele_to_use,
                                prix_unitaire=prix_unitaire,
                                prix_achat=prix_liquidation if prix_liquidation else Decimal('0.00'),
                                prix_actuel=prix_unitaire,
                                categorie=categorie_obj,
                                genre=genre_obj,
                                phase=phase,
                                isUpsell=is_upsell,
                                prix_upsell_1=prix_upsell_1,
                                prix_upsell_2=prix_upsell_2,
                                prix_upsell_3=prix_upsell_3,
                                prix_upsell_4=prix_upsell_4
                            )
                            
                            # Générer automatiquement la référence si elle n'est pas définie ou si régénération forcée
                            if (not article.reference or regenerate_references) and article.categorie and article.genre and article.modele:
                                reference_auto = article.generer_reference_automatique()
                                if reference_auto:
                                    ancienne_ref = article.reference
                                    article.reference = reference_auto
                                    article.save()
                                    if ancienne_ref and regenerate_references:
                                        self.stdout.write(f'Référence régénérée: {ancienne_ref} -> {reference_auto}')
                                    else:
                                        self.stdout.write(f'Référence générée automatiquement: {reference_auto}')
                            
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
                                    
                                    # Générer automatiquement la référence de la variante
                                    reference_variante_auto = variante.generer_reference_variante_automatique()
                                    if reference_variante_auto:
                                        variante.reference_variante = reference_variante_auto
                                        variante.save()
                                        if verbose_colors:
                                            self.stdout.write(f'Référence variante générée: {reference_variante_auto}')
                                    
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
        """Parse un prix depuis le CSV et le convertit en Decimal (robuste)."""
        if price_str is None:
            return None
        s = str(price_str)
        # Normaliser et nettoyer des artefacts courants
        s = s.replace('\xa0', ' ').replace('DH', '').replace('DHS', '').replace('MAD', '')
        s = s.strip()
        if s == '' or s == '0':
            return None
        # Extraire la première occurrence numérique (ex: 1.234,56 -> 1.234,56)
        match = re.search(r'[+-]?\d{1,3}(?:[\s\u00A0\.]\d{3})*(?:[\.,]\d+)?|[+-]?\d+(?:[\.,]\d+)?', s)
        if not match:
            return None
        num = match.group(0)
        # Retirer séparateurs de milliers (espace, NBSP, point) quand une virgule ou un point décimal est utilisé
        num = num.replace('\u00A0', ' ').replace(' ', '')
        # Si les deux séparateurs existent, on considère la dernière occurrence comme décimale
        if ',' in num and '.' in num:
            # Supposer format européen (1.234,56)
            num = num.replace('.', '').replace(',', '.')
        else:
            # Un seul séparateur -> remplacer virgule par point
            num = num.replace(',', '.')
        try:
            return Decimal(num)
        except (InvalidOperation, ValueError, TypeError):
            return None

    def _extract_modele(self, reference):
        """Extrait le numéro de modèle de la référence (ex: YZ478 -> 478, CHAUSS FEMYZ900 -> 900)"""
        if not reference:
            return None
        
        # Nettoyer la référence en retirant les espaces
        reference_clean = str(reference).replace(' ', '').upper()
        
        # Chercher le pattern YZ suivi de chiffres (même si collé à d'autres lettres)
        match = re.search(r'YZ(\d+)', reference_clean)
        if match:
            try:
                modele_num = int(match.group(1))
                self.stdout.write(f'Modèle extrait: {reference} -> {modele_num}')
                return modele_num
            except (ValueError, TypeError):
                self.stdout.write(f'Erreur extraction modèle: {reference}')
                return None
        
        # Si pas de pattern YZ trouvé
        self.stdout.write(f'Aucun modèle trouvé dans: {reference}')
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
        """Parse les couleurs depuis le CSV avec normalisation de la casse"""
        if not couleurs_str or couleurs_str.strip() == '' or couleurs_str.strip() == '--':
            return ['Standard']  # Couleur par défaut si aucune spécifiée
        
        # Mapping des couleurs communes pour normaliser la casse
        couleur_mapping = {
            'NOIR': 'Noir',
            'BLANC': 'Blanc',
            'ROUGE': 'Rouge',
            'BLEU': 'Bleu',
            'VERT': 'Vert',
            'JAUNE': 'Jaune',
            'ROSE': 'Rose',
            'VIOLET': 'Violet',
            'ORANGE': 'Orange',
            'GRIS': 'Gris',
            'MARRON': 'Marron',
            'BEIGE': 'Beige',
            'CAMEL': 'Camel',
            'BRONZE': 'Bronze',
            'DORE': 'Doré',
            'ARGENT': 'Argent',
            'GOLD': 'Doré',
            'SILVER': 'Argent',
            'NAVY': 'Bleu Marine',
            'NUDE': 'Nude',
            'KAKI': 'Kaki',
            'TURQUOISE': 'Turquoise',
            'FUCHSIA': 'Fuchsia',
            'LIME': 'Lime',
            'CORAIL': 'Corail',
            'SAUMON': 'Saumon',
            'BORDEAUX': 'Bordeaux',
            'PRUNE': 'Prune',
            'TAUPE': 'Taupe',
            'ECRU': 'Ecru',
            'IVOIRE': 'Ivoire',
            'CREME': 'Crème',
            'MULTICOLORE': 'Multicolore',
            'LEOPARD': 'Léopard',
            'ZEBRE': 'Zèbre',
            'PYTHON': 'Python',
            'CROCO': 'Croco',
            'METAL': 'Métallisé',
            'METALLISE': 'Métallisé',
            'BRILLANT': 'Brillant',
            'MAT': 'Mat',
            'SATINE': 'Satiné',
            'BLEU JEANS': 'Bleu Jeans',
            'BLEU JEAN': 'Bleu Jeans',
            'BLANC GRIS': 'Blanc Gris',
            'GRENAT': 'Grenat',
            'COGNAC': 'Cognac'
        }
        
        couleurs = []
        # Nettoyer la chaîne (retirer les retours à la ligne et espaces en trop)
        couleurs_clean = str(couleurs_str).replace('\n', ' ').replace('\r', ' ')
        couleurs_clean = re.sub(r'\s+', ' ', couleurs_clean).strip()
        
        # Parser les couleurs (séparées par des tirets, virgules, slashes ou pipes)
        separateurs = ['-', ',', '/', '|', ';']
        couleurs_brutes = [couleurs_clean]
        
        for sep in separateurs:
            if sep in couleurs_clean:
                couleurs_brutes = [c.strip() for c in couleurs_clean.split(sep) if c.strip() and c.strip() != '']
                break
        
        # Nettoyer chaque couleur et normaliser la casse
        couleurs_finales = []
        for couleur in couleurs_brutes:
            couleur_clean = couleur.strip().upper()
            if couleur_clean and couleur_clean != '--' and len(couleur_clean) > 0:
                # Vérifier si la couleur existe dans le mapping
                if couleur_clean in couleur_mapping:
                    couleur_normalisee = couleur_mapping[couleur_clean]
                else:
                    # Si pas dans le mapping, utiliser la forme title (première lettre majuscule)
                    couleur_normalisee = couleur.strip().title()
                    # Correction pour les mots composés
                    couleur_normalisee = couleur_normalisee.replace(' De ', ' de ')
                    couleur_normalisee = couleur_normalisee.replace(' Du ', ' du ')
                    couleur_normalisee = couleur_normalisee.replace(' Le ', ' le ')
                    couleur_normalisee = couleur_normalisee.replace(' La ', ' la ')
                
                couleurs_finales.append(couleur_normalisee)
        
        # Si aucune couleur valide trouvée, retourner une couleur par défaut
        if not couleurs_finales:
            couleurs_finales = ['Standard']
        
        # Supprimer les doublons tout en préservant l'ordre
        couleurs_uniques = []
        for couleur in couleurs_finales:
            if couleur not in couleurs_uniques:
                couleurs_uniques.append(couleur)
            
        return couleurs_uniques
