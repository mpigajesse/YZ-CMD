# Documentation des Modèles - Projet YZ-CMD

## Vue d'ensemble
Ce document présente la structure complète de la base de données du projet YZ-CMD, un système de gestion de commandes avec interfaces séparées pour administrateurs, opérateurs de confirmation et opérateurs logistiques.

---

## 1. Application `parametre`

### 1.1 Modèle `Region`
**Description :** Gestion des régions géographiques

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | AutoField | PK, Auto-increment | Clé primaire automatique |
| `nom_region` | CharField(100) | Unique, Required | Nom de la région |

**Meta :**
- `verbose_name` : "Région"
- `verbose_name_plural` : "Régions"
- `ordering` : ['nom_region']

**Relations :**
- `villes` ← `Ville` (One-to-Many)

---

### 1.2 Modèle `Ville`
**Description :** Gestion des villes avec informations de livraison

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | AutoField | PK, Auto-increment | Clé primaire automatique |
| `nom` | CharField(100) | Required | Nom de la ville |
| `frais_livraison` | FloatField | Required | Coût de livraison |
| `frequence_livraison` | CharField(50) | Required | Fréquence de livraison |
| `region` | ForeignKey(Region) | CASCADE, Required | Région de rattachement |

**Meta :**
- `verbose_name` : "Ville"
- `verbose_name_plural` : "Villes"
- `ordering` : ['nom']
- `unique_together` : ['nom', 'region'] (Une ville unique par région)

**Relations :**
- `region` → `Region` (Many-to-One)
- `commandes` ← `Commande` (One-to-Many)

---

### 1.3 Modèle `Operateur`
**Description :** Profils des opérateurs du système

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | AutoField | PK, Auto-increment | Clé primaire automatique |
| `user` | OneToOneField(User) | CASCADE, Required | Utilisateur Django associé |
| `nom` | CharField(100) | Required | Nom de famille |
| `prenom` | CharField(100) | Required | Prénom |
| `mail` | EmailField | Required | Adresse email |
| `type_operateur` | CharField(20) | Choices, Default='CONFIRMATION' | Type d'opérateur |
| `photo` | ImageField | Optional | Photo de profil |
| `adresse` | TextField | Optional | Adresse complète |
| `telephone` | CharField(20) | Optional | Numéro de téléphone |
| `date_creation` | DateTimeField | Auto-now-add | Date de création |
| `date_modification` | DateTimeField | Auto-now | Date de modification |
| `actif` | BooleanField | Default=True | Statut actif/inactif |

**Choix `type_operateur` :**
- `CONFIRMATION` : Opérateur de Confirmation
- `LOGISTIQUE` : Opérateur Logistique
- `ADMIN` : Administrateur

**Propriétés :**
- `nom_complet` : Retourne "prénom nom"
- `is_confirmation` : True si type_operateur == 'CONFIRMATION'
- `is_logistique` : True si type_operateur == 'LOGISTIQUE'
- `is_admin` : True si type_operateur == 'ADMIN'

**Meta :**
- `verbose_name` : "Opérateur"
- `verbose_name_plural` : "Opérateurs"
- `ordering` : ['nom', 'prenom']

**Relations :**
- `user` → `User` (One-to-One)
- `operations` ← `Operation` (One-to-Many)
- `etats_modifies` ← `EtatCommande` (One-to-Many)

---

## 2. Application `client`

### 2.1 Modèle `Client`
**Description :** Gestion des clients

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | AutoField | PK, Auto-increment | Clé primaire automatique |
| `numero_tel` | CharField(20) | Unique, Required | Numéro de téléphone |
| `nom` | CharField(100) | Optional | Nom de famille |
| `prenom` | CharField(100) | Optional | Prénom |
| `email` | EmailField | Optional | Adresse email |
| `adresse` | TextField | Optional | Adresse complète |
| `date_creation` | DateTimeField | Auto-now-add | Date de création |
| `actif` | BooleanField | Default=True | Statut actif/inactif |

**Meta :**
- `verbose_name` : "Client"
- `verbose_name_plural` : "Clients"
- `ordering` : ['numero_tel']

**Relations :**
- `commandes` ← `Commande` (One-to-Many)

**Méthode `__str__` :**
- Si nom et prénom : "prénom nom - numéro_tel"
- Sinon : "Client numéro_tel"

---

## 3. Application `article`

### 3.1 Modèle `Article`
**Description :** Gestion du catalogue d'articles

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | AutoField | PK, Auto-increment | Clé primaire automatique |
| `nom` | CharField(200) | Required | Nom de l'article |
| `couleur` | CharField(50) | Required | Couleur |
| `pointure` | CharField(10) | Required | Pointure/Taille |
| `prix_unitaire` | FloatField | Required, >0 | Prix unitaire |
| `categorie` | CharField(100) | Required | Catégorie |
| `qte_disponible` | IntegerField | Required, ≥0 | Quantité disponible |
| `description` | TextField | Optional | Description détaillée |
| `image` | ImageField | Optional | Image de l'article |
| `date_creation` | DateTimeField | Auto-now-add | Date de création |
| `date_modification` | DateTimeField | Auto-now | Date de modification |
| `actif` | BooleanField | Default=True | Statut actif/inactif |

**Propriétés :**
- `est_disponible` : True si qte_disponible > 0 et actif == True

**Meta :**
- `verbose_name` : "Article"
- `verbose_name_plural` : "Articles"
- `ordering` : ['nom', 'couleur', 'pointure']
- `unique_together` : ['nom', 'couleur', 'pointure'] (Combinaison unique)

**Contraintes :**
- `prix_unitaire_positif` : prix_unitaire > 0
- `qte_disponible_positif` : qte_disponible ≥ 0

**Relations :**
- `paniers` ← `Panier` (One-to-Many)

---

## 4. Application `commande`

### 4.1 Modèle `EnumEtatCmd`
**Description :** États possibles des commandes

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | AutoField | PK, Auto-increment | Clé primaire automatique |
| `libelle` | CharField(100) | Unique, Required | Libellé de l'état |
| `ordre` | IntegerField | Default=0 | Ordre d'affichage |
| `couleur` | CharField(7) | Default='#6B7280' | Code couleur hexadécimal |

**Meta :**
- `verbose_name` : "État de commande"
- `verbose_name_plural` : "États de commande"
- `ordering` : ['ordre', 'libelle']

**Relations :**
- `etatcommande_set` ← `EtatCommande` (One-to-Many)

---

### 4.2 Modèle `Commande`
**Description :** Commandes principales (États gérés dans EtatCommande)

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | AutoField | PK, Auto-increment | Clé primaire automatique |
| `num_cmd` | CharField(50) | Unique, Required | Numéro de commande |
| `id_yz` | CharField(50) | Optional | Identifiant YZ |
| `date_cmd` | DateField | Default=today | Date de commande |
| `total_cmd` | FloatField | Required, ≥0 | Montant total |
| `adresse` | TextField | Required | Adresse de livraison |
| `motif_annulation` | TextField | Optional | Motif d'annulation |
| `etat_paiement` | CharField(20) | Choices, Default='En attente' | État du paiement |
| `is_upsell` | BooleanField | Default=False | Commande upsell |
| `date_creation` | DateTimeField | Auto-now-add | Date de création |
| `date_modification` | DateTimeField | Auto-now | Date de modification |
| `client` | ForeignKey(Client) | CASCADE, Required | Client |
| `ville` | ForeignKey(Ville) | CASCADE, Required | Ville de livraison |

**Choix `etat_paiement` :**
- `En attente` : En attente
- `Payé` : Payé
- `Échoué` : Échoué

**Propriétés :**
- `etat_actuel` : Retourne l'état actuel de la commande (EtatCommande sans date_fin)
- `historique_etats` : Retourne l'historique complet des états

**Meta :**
- `verbose_name` : "Commande"
- `verbose_name_plural` : "Commandes"
- `ordering` : ['-date_cmd', '-date_creation']

**Contraintes :**
- `total_cmd_positif` : total_cmd ≥ 0

**Relations :**
- `client` → `Client` (Many-to-One)
- `ville` → `Ville` (Many-to-One)
- `paniers` ← `Panier` (One-to-Many)
- `etats` ← `EtatCommande` (One-to-Many)
- `operations` ← `Operation` (One-to-Many)

**⚠️ Important :** Les états de commande ne sont PAS stockés dans cette table mais dans `EtatCommande` pour un historique complet.

---

### 4.3 Modèle `Panier`
**Description :** Articles dans une commande

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | AutoField | PK, Auto-increment | Clé primaire automatique |
| `commande` | ForeignKey(Commande) | CASCADE, Required | Commande |
| `article` | ForeignKey(Article) | CASCADE, Required | Article |
| `quantite` | IntegerField | Required, >0 | Quantité commandée |
| `sous_total` | FloatField | Required, ≥0 | Sous-total |

**Meta :**
- `verbose_name` : "Panier"
- `verbose_name_plural` : "Paniers"
- `unique_together` : [['commande', 'article']] (Un article par commande)

**Contraintes :**
- `quantite_positive` : quantite > 0
- `sous_total_positif` : sous_total ≥ 0

**Relations :**
- `commande` → `Commande` (Many-to-One)
- `article` → `Article` (Many-to-One)

---

### 4.4 Modèle `EtatCommande`
**Description :** Historique des états des commandes (Table principale pour les modifications d'état)

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | AutoField | PK, Auto-increment | Clé primaire automatique |
| `commande` | ForeignKey(Commande) | CASCADE, Required | Commande |
| `enum_etat` | ForeignKey(EnumEtatCmd) | CASCADE, Required | État |
| `date_debut` | DateTimeField | Auto-now-add | Date de début |
| `date_fin` | DateTimeField | Optional | Date de fin |
| `commentaire` | TextField | Optional | Commentaire |
| `operateur` | ForeignKey(Operateur) | CASCADE, Optional | Opérateur ayant modifié l'état |

**Méthodes :**
- `terminer_etat(operateur=None)` : Termine cet état en définissant la date_fin
- `duree` (property) : Retourne la durée de cet état

**Meta :**
- `verbose_name` : "État de commande"
- `verbose_name_plural` : "États de commande"
- `ordering` : ['-date_debut']

**Contraintes :**
- `date_debut_avant_date_fin` : date_debut ≤ date_fin (si date_fin existe)

**Relations :**
- `commande` → `Commande` (Many-to-One)
- `enum_etat` → `EnumEtatCmd` (Many-to-One)
- `operateur` → `Operateur` (Many-to-One)

**⚠️ Important :** Cette table est le cœur du système de suivi des commandes. Toutes les modifications d'état sont enregistrées ici.

---

### 4.5 Modèle `Operation`
**Description :** Opérations effectuées sur les commandes

| Champ | Type | Contraintes | Description |
|-------|------|-------------|-------------|
| `id` | AutoField | PK, Auto-increment | Clé primaire automatique |
| `type_operation` | CharField(20) | Choices, Required | Type d'opération |
| `date_operation` | DateTimeField | Auto-now-add | Date de l'opération |
| `conclusion` | TextField | Required | Conclusion/Résultat |
| `commande` | ForeignKey(Commande) | CASCADE, Required | Commande |
| `operateur` | ForeignKey(Operateur) | CASCADE, Required | Opérateur |

**Choix `type_operation` :**
- `CONFIRMATION` : Confirmation
- `ANNULATION` : Annulation
- `PREPARATION` : Préparation
- `EXPEDITION` : Expédition
- `LIVRAISON` : Livraison
- `RETOUR` : Retour
- `MODIFICATION` : Modification
- `COMMENTAIRE` : Commentaire

**Meta :**
- `verbose_name` : "Opération"
- `verbose_name_plural` : "Opérations"
- `ordering` : ['-date_operation']

**Relations :**
- `commande` → `Commande` (Many-to-One)
- `operateur` → `Operateur` (Many-to-One)

---

## 5. Diagramme des Relations

```
User (Django) ←→ Operateur
                     ↓
Client → Commande ← Ville ← Region
           ↓
        Panier → Article
           ↓
     EtatCommande ← EnumEtatCmd
           ↓        ↑
       Operation    Operateur
```

---

## 6. Contraintes et Validations

### Contraintes de Base de Données
- **Unicité** : Region.nom_region, Ville(nom+region), Client.numero_tel, Article(nom+couleur+pointure), Commande.num_cmd, EnumEtatCmd.libelle
- **Valeurs positives** : Article.prix_unitaire > 0, Article.qte_disponible ≥ 0, Commande.total_cmd ≥ 0, Panier.quantite > 0, Panier.sous_total ≥ 0
- **Dates cohérentes** : EtatCommande.date_debut ≤ date_fin

### Validations Métier
- Un article est disponible si qte_disponible > 0 ET actif = True
- Un opérateur a un type unique (CONFIRMATION, LOGISTIQUE, ADMIN)
- Une commande peut avoir plusieurs états dans le temps
- L'état actuel d'une commande est celui sans date_fin dans EtatCommande
- Toutes les modifications d'état sont tracées dans EtatCommande avec l'opérateur responsable

---

## 7. Signaux Django

### Signal `post_save` sur User
**Fichier :** `parametre/signals.py`
**Fonction :** Création automatique du profil Operateur selon les groupes de l'utilisateur
**Logique :**
- Si utilisateur dans groupe "Administrateurs" → type_operateur = 'ADMIN'
- Si utilisateur dans groupe "Operateurs_Confirmation" → type_operateur = 'CONFIRMATION'  
- Si utilisateur dans groupe "Operateurs_Logistique" → type_operateur = 'LOGISTIQUE'
- Synchronisation des données User ↔ Operateur

---

## 8. Interface d'Administration

### Fonctionnalités Admin
- **Filtres avancés** par type, statut, dates
- **Recherche** sur tous les champs pertinents
- **Édition en ligne** pour les champs fréquemment modifiés
- **Fieldsets organisés** pour une meilleure UX
- **Relations inline** pour les modèles liés
- **Champs en lecture seule** pour les données système

### Permissions
- Accès différencié selon le type d'opérateur
- Interface spécialisée pour chaque rôle
- Sidebar personnalisée avec couleurs thématiques

---

## 9. Données Importées

### Régions et Villes
- **11 régions** : CASABLANCA, SALE, MARRAKECH, AGADIR, TETOUAN, OUJDA, SAFI, MEKNÈS, BENI MELLAL, FÈS, GUELMIM
- **416 villes** avec tarifs de livraison et fréquences
- **Tarifs** : de 20DH (grandes villes) à 50DH (zones éloignées)

### Articles
- **Chaussures femme** principalement (SAB FEM YZ83, SAB FEM YZ 410)
- **Couleurs** : NOIR, BEIGE, MARRON, BLEU MARINE, BLEU CIEL, CAMEL
- **Pointures** : 37 à 41
- **Prix** : de 200DH à 700DH selon le modèle et la pointure

---

*Documentation générée par COD$uite Team - Version 2.0*
*Projet YZ-CMD - Système de Gestion de Commandes* 