# 📦 Importation des Articles depuis CSV - YOOZAK

Ce document explique comment utiliser le script d'importation des articles depuis le fichier CSV YOOZAK.

## 🎯 Objectif

Le script `import_articles_csv` permet d'importer automatiquement les articles et leurs variantes depuis le fichier CSV `EXMPLE JOURNEE YOOZAK_EIGSI - GESTIONNAIRE ARTICLE.csv` vers la base de données Django.

## 📋 Structure du CSV

Le fichier CSV contient les colonnes suivantes :

| Colonne CSV | Champ Modèle | Description | Exemple |
|-------------|--------------|-------------|---------|
| `REF ARTICLE` | `reference` | Référence unique de l'article | `SDL FEM YZ478` |
| `CATEGORIE` | `categorie` | Catégorie de l'article | `SANDALE`, `CHAUSSURE`, `SABOT` |
| `GENRE` | `genre` | Genre cible | `FEMME`, `HOMME`, `FILLE`, `GARCON` |
| `PRIX UNITAIRE` | `prix_unitaire` | Prix de vente | `219,00DH` |
| `POINTURE` | - | Gamme de pointures | `37---41`, `37-40` |
| `COULEUR` | - | Couleurs disponibles | `BEIGE`, `NOIR-MARRON` |
| `PHASE` | `phase` | Phase de l'article | `EN COUR`, `EN TEST`, `EN LIQUIDATION` |
| `PRIX LIQ 1` | `prix_achat` | Prix d'achat/liquidation | `134,00DH` |
| `PRIX UPSEL 2` | `prix_upsell_2` | Prix upsell quantité 2 | `388,00DH` |
| `PRIX UPSEL 3` | `prix_upsell_3` | Prix upsell quantité 3 | `522,00DH` |
| `PRIX UPSEL 4` | `prix_upsell_4` | Prix upsell quantité 4 | `656,00DH` |

## 🏗️ Structure des Modèles

### Article Principal
- **Informations de base** : nom, référence, modèle, prix, catégorie, genre, phase
- **Prix** : prix unitaire, prix d'achat, prix actuel
- **Upsell** : indicateur et prix pour différentes quantités

### Variantes
- **Combinaisons** : article + couleur + pointure
- **Stock** : quantité disponible par variante
- **Activation** : possibilité d'activer/désactiver des variantes

## 🚀 Utilisation

### 1. Test en Mode DRY-RUN

```bash
# Voir ce qui serait importé sans modifier la base
python manage.py import_articles_csv "EXMPLE JOURNEE YOOZAK_EIGSI  - GESTIONNAIRE ARTICLE.csv" --dry-run
```

### 2. Importation Réelle

```bash
# Importation complète
python manage.py import_articles_csv "EXMPLE JOURNEE YOOZAK_EIGSI  - GESTIONNAIRE ARTICLE.csv"
```

### 3. Mise à Jour des Articles Existants

```bash
# Mettre à jour les articles existants
python manage.py import_articles_csv "EXMPLE JOURNEE YOOZAK_EIGSI  - GESTIONNAIRE ARTICLE.csv" --update-existing
```

## 🔧 Fonctionnalités

### Mapping Automatique
- **Catégories** : SANDALE → SANDALES, SAC → PACK_SAC
- **Phases** : EN COUR → EN_COURS, EN LIQUIDATION → LIQUIDATION
- **Genres** : FEMME → FEMME, HOMME → HOMME

### Extraction Intelligente
- **Modèle** : Extraction automatique du numéro YZ (ex: YZ478 → 478)
- **Pointures** : Parsing des gammes (ex: 37---41 → [37, 38, 39, 40, 41])
- **Couleurs** : Séparation automatique des couleurs multiples

### Gestion des Prix
- **Prix unitaire** : Conversion automatique DH → Decimal
- **Prix upsell** : Détection automatique des articles upsell
- **Prix d'achat** : Utilisation du prix de liquidation

## 📊 Exemple d'Importation

### Article Source (CSV)
```
REF ARTICLE: SDL FEM YZ478
CATEGORIE: SANDALE
GENRE: FEMME
PRIX UNITAIRE: 219,00DH
POINTURE: 37---41
COULEUR: BEIGE
PHASE: EN LIQUIDATION
PRIX LIQ 1: 134,00DH
PRIX UPSEL 2: 388,00DH
PRIX UPSEL 3: 522,00DH
PRIX UPSEL 4: 656,00DH
```

### Article Créé (Base de Données)
```python
Article.objects.create(
    nom='SDL FEM YZ478',
    reference='SDL FEM YZ478',
    modele=478,
    prix_unitaire=219.00,
    prix_achat=134.00,
    prix_actuel=219.00,
    categorie=categorie_sandales,
    genre=genre_femme,
    phase='LIQUIDATION',
    isUpsell=True,
    prix_upsell_2=388.00,
    prix_upsell_3=522.00,
    prix_upsell_4=656.00
)
```

### Variantes Créées
- **Variante 1** : BEIGE - 37
- **Variante 2** : BEIGE - 38
- **Variante 3** : BEIGE - 39
- **Variante 4** : BEIGE - 40
- **Variante 5** : BEIGE - 41

## ⚠️ Points d'Attention

### Contraintes
- **Prix unitaire** : Doit être > 0 (contrainte de base de données)
- **Référence** : Doit être unique
- **Modèle** : Doit être unique

### Gestion des Erreurs
- **Lignes invalides** : Ignorées avec log d'erreur
- **Données manquantes** : Valeurs par défaut appliquées
- **Doublons** : Gestion selon l'option `--update-existing`

### Performance
- **Transactions** : Utilisation de transactions Django pour la cohérence
- **Bulk Create** : Création en lot des variantes
- **Progression** : Affichage du progrès tous les 10 articles

## 🧪 Tests

### Script de Test
```bash
# Exécuter les tests
python test_import_articles.py
```

### Tests Inclus
- **Création d'article** : Test de création d'un article complet
- **Importation CSV** : Test en mode DRY-RUN et réel
- **Validation des données** : Vérification des contraintes

## 📈 Résultats Attendus

### Articles
- **Total** : ~327 articles (selon le CSV)
- **Catégories** : 9 catégories principales
- **Genres** : 4 genres (FEMME, HOMME, FILLE, GARCON)
- **Phases** : 4 phases (EN_COURS, EN_TEST, LIQUIDATION, PROMO)

### Variantes
- **Total** : ~1000+ variantes (combinaisons couleur/pointure)
- **Pointures** : Gammes 24-45 selon les articles
- **Couleurs** : 20+ couleurs différentes

## 🔄 Mise à Jour

### Re-importation
```bash
# Mettre à jour tous les articles
python manage.py import_articles_csv "fichier.csv" --update-existing
```

### Nettoyage
- **Variantes** : Supprimées et recréées lors de la mise à jour
- **Articles** : Mise à jour des champs modifiables
- **Historique** : Conservation des dates de création

## 📝 Logs et Suivi

### Informations Affichées
- **Progrès** : Nombre d'articles traités
- **Erreurs** : Détail des erreurs par ligne
- **Résumé** : Statistiques finales d'importation

### Fichiers de Log
- **Console** : Affichage en temps réel
- **Base de données** : Traçabilité via timestamps

## 🚨 Dépannage

### Erreurs Communes
1. **Fichier CSV introuvable** : Vérifier le chemin et l'encodage
2. **Erreurs de contrainte** : Vérifier les données du CSV
3. **Problèmes de mémoire** : Traiter par lots pour de gros fichiers

### Solutions
- **Mode DRY-RUN** : Tester avant importation
- **Validation CSV** : Vérifier la structure des données
- **Logs détaillés** : Analyser les erreurs ligne par ligne

---

**Note** : Ce script est conçu spécifiquement pour la structure YOOZAK et peut nécessiter des adaptations pour d'autres formats CSV.
