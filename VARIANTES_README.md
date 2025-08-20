# Système de Variantes d'Articles avec Génération Automatique de Références

## Vue d'ensemble

Ce système permet de créer des variantes d'articles avec génération automatique de références, similaire à la génération de références d'articles. Chaque variante peut avoir une couleur, une pointure et une quantité, tous optionnels.

## Fonctionnalités

### 1. Modal de Création de Variantes
- **Couleur** : Optionnel, permet de spécifier la couleur de la variante
- **Pointure** : Optionnel, permet de spécifier la pointure de la variante  
- **Quantité** : Quantité disponible en stock (par défaut 0)
- **Référence automatique** : Générée en temps réel selon les sélections

### 2. Génération Automatique de Références

#### Format de Référence Article
```
{CATEGORIE}-{GENRE}-YZ-{MODELE}
```
Exemple : `CHAUSSURES-HOMME-YZ-1001`

#### Format de Référence Variante
```
{CATEGORIE}-{GENRE}-YZ-{MODELE}-{COULEUR}-{POINTURE}
```
Exemples :
- `CHAUSSURES-HOMME-YZ-1001-ROUGE-42`
- `CHAUSSURES-HOMME-YZ-1001-ROUGE` (sans pointure)
- `CHAUSSURES-HOMME-YZ-1001-42` (sans couleur)

### 3. Validation et Contrôles
- Au moins une couleur ou une pointure doit être spécifiée
- Vérification d'unicité des combinaisons couleur/pointure
- Validation avant soumission du formulaire
- Messages d'erreur et de succès en temps réel

## Utilisation

### 1. Ouvrir le Modal
Cliquer sur le bouton "Ajouter une variante" dans la section des variantes du formulaire de création d'article.

### 2. Remplir les Champs
- **Couleur** : Sélectionner une couleur ou laisser vide
- **Pointure** : Sélectionner une pointure ou laisser vide
- **Quantité** : Saisir la quantité disponible

### 3. Aperçu de la Référence
La référence de la variante s'affiche automatiquement en temps réel selon les sélections :
- Change automatiquement quand on modifie la catégorie, genre ou modèle
- S'adapte aux sélections de couleur et pointure
- Masquée si aucune couleur ni pointure n'est sélectionnée

### 4. Ajouter la Variante
Cliquer sur "Ajouter" pour créer la variante. Elle apparaîtra dans la liste des variantes avec :
- Combinaison couleur/pointure
- Quantité
- Référence générée
- Bouton de suppression

### 5. Gestion des Variantes
- **Supprimer** : Cliquer sur l'icône poubelle
- **Modifier** : Supprimer et recréer la variante
- **Validation** : Au moins une variante requise avant soumission

## Structure Technique

### Fichiers Modifiés
- `templates/article/creer.html` : Template avec modal et affichage des variantes
- `static/js/variantes-modal.js` : Gestion JavaScript des variantes
- `static/css/variantes-modal.css` : Styles CSS pour le modal
- `article/views.py` : Logique de création des variantes en backend

### Classes JavaScript
- **VariantesManager** : Gestion principale des variantes
- **Méthodes principales** :
  - `openVarianteModal()` : Ouvrir le modal
  - `addVariante()` : Ajouter une variante
  - `removeVariante()` : Supprimer une variante
  - `genererReferenceVariante()` : Générer la référence
  - `updateReferencePreview()` : Mettre à jour l'aperçu

### Modèle de Données
Les variantes sont stockées dans le modèle `VarianteArticle` avec :
- `article` : Référence vers l'article parent
- `couleur` : Couleur de la variante (optionnel)
- `pointure` : Pointure de la variante (optionnel)
- `qte_disponible` : Quantité en stock
- `reference_variante` : Référence générée automatiquement

## Exemples d'Utilisation

### Exemple 1 : Variante avec Couleur et Pointure
```
Article : Chaussures de Sport Homme
Catégorie : CHAUSSURES
Genre : HOMME
Modèle : 1001

Variante :
- Couleur : Rouge
- Pointure : 42
- Quantité : 25

Référence générée : CHAUSSURES-HOMME-YZ-1001-ROUGE-42
```

### Exemple 2 : Variante avec Couleur Seule
```
Article : Sac à Dos
Catégorie : PACK_SAC
Genre : FEMME
Modèle : 2001

Variante :
- Couleur : Noir
- Pointure : (vide)
- Quantité : 10

Référence générée : PACK_SAC-FEMME-YZ-2001-NOIR
```

### Exemple 3 : Variante avec Pointure Seule
```
Article : Chaussures de Ville
Catégorie : CHAUSSURES
Genre : FEMME
Modèle : 3001

Variante :
- Couleur : (vide)
- Pointure : 38
- Quantité : 15

Référence générée : CHAUSSURES-FEMME-YZ-3001-38
```

## Avantages

1. **Flexibilité** : Couleur et pointure optionnelles
2. **Automatisation** : Génération automatique des références
3. **Validation** : Contrôles en temps réel
4. **Interface intuitive** : Modal simple et clair
5. **Gestion d'erreurs** : Messages informatifs
6. **Responsive** : Compatible mobile et desktop

## Maintenance

### Ajouter de Nouvelles Couleurs/Pointures
Les couleurs et pointures sont récupérées depuis la base de données via les modèles `Couleur` et `Pointure`. Pour en ajouter de nouvelles, utiliser l'interface d'administration Django.

### Modifier le Format de Référence
Modifier la méthode `genererReferenceVariante()` dans `variantes-modal.js` pour changer le format des références.

### Personnaliser les Styles
Modifier le fichier `variantes-modal.css` pour adapter l'apparence du modal et des variantes.
