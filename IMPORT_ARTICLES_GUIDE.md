# Guide d'Import des Articles depuis CSV

## Vue d'ensemble

Le script d'import `import_articles_csv.py` a été amélioré pour extraire automatiquement le numéro de modèle depuis la colonne "REF ARTICLE" du fichier CSV.

## Fonctionnalités

### ✅ Extraction automatique du modèle
- **Pattern détecté** : `YZ` suivi de chiffres
- **Exemples** :
  - `SDL FEM YZ478` → Modèle : 478
  - `CHAUSS FEMYZ900` → Modèle : 900  
  - `SAB FEM YZ24` → Modèle : 24
  - `BOT FEM YZ3010` → Modèle : 3010

### ✅ Gestion des couleurs améliorée
- **Formats supportés** :
  - Couleurs séparées par tirets : `NOIR-MARRON-BEIGE`
  - Couleurs avec retours à la ligne dans le CSV
  - Couleurs vides ou `--` → Couleur par défaut "Standard"

### ✅ Gestion des prix upsell
- Support des 4 niveaux de prix upsell
- Détection automatique si l'article est un upsell
- Prix liquidation utilisé comme prix d'achat

### ✅ Gestion des pointures
- **Formats supportés** :
  - Plage avec `---` : `37---41` → 37, 38, 39, 40, 41
  - Plage avec `-` : `37-40` → 37, 38, 39, 40
  - Pointure unique : `39` → 39

## Utilisation

### 1. Test en mode dry-run (recommandé)
```bash
python manage.py import_articles_csv "EXMPLE JOURNEE YOOZAK_EIGSI  - GESTIONNAIRE ARTICLE.csv" --dry-run
```

### 2. Import réel
```bash
python manage.py import_articles_csv "EXMPLE JOURNEE YOOZAK_EIGSI  - GESTIONNAIRE ARTICLE.csv" --update-existing
```

### 3. Test avec le script helper
```bash
python test_import_articles.py
```

## Colonnes CSV traitées

| Colonne CSV | Champ modèle | Description |
|-------------|--------------|-------------|
| `REF ARTICLE` | `reference` + `modele` | Référence + extraction YZ + numéro |
| `CATEGORIE` | `categorie` | Mappage vers catégories système |
| `GENRE` | `genre` | HOMME, FEMME, FILLE, GARCON |
| `PRIX UNITAIRE` | `prix_unitaire` | Prix principal |
| `PRIX LIQ 1` | `prix_achat` | Prix d'achat/liquidation |
| `PRIX UPSEL 2-4` | `prix_upsell_1-4` | Prix dégressifs |
| `POINTURE` | Variantes | Génération des variantes |
| `COULEUR` | Variantes | Génération des variantes |
| `PHASE` | `phase` | EN_COURS, LIQUIDATION, etc. |

## Mappages automatiques

### Catégories
```python
'SANDALE' → 'SANDALES'
'SABOT' → 'SABOT'  
'CHAUSSURE' → 'CHAUSSURES'
'ESPADRILLE' → 'ESPARILLE'
'BASKET' → 'BASKET'
'SAC' → 'PACK_SAC'
# etc.
```

### Phases
```python
'EN COUR' → 'EN_COURS'
'EN TEST' → 'EN_TEST'
'EN LIQUIDATION' → 'LIQUIDATION'
'PROMO' → 'PROMO'
```

## Génération des variantes

Pour chaque article, le script génère automatiquement toutes les combinaisons :
- **Couleurs** × **Pointures** = **Variantes**
- Exemple : 3 couleurs × 5 pointures = 15 variantes par article

## Gestion des doublons

### Modèles
- Vérifie l'unicité du champ `modele` 
- En cas de conflit, ne met pas à jour le modèle existant

### Articles
- Par défaut : ignore les articles existants
- Avec `--update-existing` : met à jour les articles existants

## Logs et debugging

### Informations affichées
- Progression de l'import (tous les 10 articles)
- Modèles extraits avec succès
- Erreurs de parsing des prix
- Articles ignorés/créés/mis à jour
- Résumé final avec statistiques

### En cas d'erreur
- Messages d'erreur détaillés avec numéro de ligne
- Affichage des 5 premières erreurs
- Import partiel possible (continue malgré les erreurs)

## Exemple de sortie

```
Modèle extrait: SDL FEM YZ478 -> 478
Modèle extrait: CHAUSS FEMYZ900 -> 900
Articles traités: 10
Articles traités: 20
...

=====================================
RÉSUMÉ DE L'IMPORTATION
=====================================
Articles créés: 45
Articles mis à jour: 0
Articles ignorés: 0
Variantes créées: 1250
```

## Fichiers de test

- `test_extraction_modele.py` : Teste l'extraction des modèles
- `test_import_articles.py` : Test complet de l'import
- Script principal : `article/management/commands/import_articles_csv.py`

## Notes importantes

1. **Backup recommandé** avant import en production
2. **Test en dry-run** obligatoire avant import réel  
3. **Vérification des doublons** de modèles dans le CSV
4. **Encodage UTF-8** requis pour le fichier CSV
5. **Images** : non gérées par ce script (à ajouter manuellement)

## Dépannage

### Erreur d'encodage
- Vérifier l'encodage UTF-8 du fichier CSV
- Éviter les caractères spéciaux dans les noms

### Modèles en doublon
- Vérifier les références dans le CSV
- Utiliser `--update-existing` avec précaution

### Variantes non créées
- Vérifier le format des colonnes POINTURE et COULEUR  
- S'assurer qu'elles ne sont pas vides