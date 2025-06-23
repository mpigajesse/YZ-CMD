# KPIs - Indicateurs de Performance YZ-CMD

## Vue d'ensemble

Ce document présente l'architecture et les spécifications des KPIs (Key Performance Indicators) pour le système YZ-CMD de **Yoozak**, entreprise marocaine spécialisée dans la vente de chaussures et sandales de qualité.

**Activité Yoozak :**
- 🏢 **Entreprise fièrement marocaine** 
- 👟 **Chaussures** pour hommes et femmes (style + confort)
- 🩴 **Sandales** et **Baskets** de haute qualité  
- 🐄 **Cuir véritable** de qualité supérieure
- 🌍 **Marché** : Maroc avec livraison nationale
- 🚚 **Livraison gratuite** + support 24/7 + paiement à la livraison
- 📱 **Vente e-commerce** avec suivi téléphonique intensif

Les KPIs sont organisés en composants modulaires adaptés à l'activité e-commerce chaussures avec forte composante téléphonique, gestion des stocks par pointures, et couverture géographique étendue Maroc.

## Organisation UX Optimale pour le Dashboard

### 🎯 Problématiques Identifiées
- Dashboard actuel avec seulement 4 cartes KPIs insuffisant pour ~20 indicateurs
- Manque de hiérarchisation visuelle de l'information
- Absence de filtres et d'interactivité utilisateur
- Pas de regroupement logique des métriques par domaine

### 📊 Solution Retenue: Dashboard à Onglets

#### Structure Générale
```
┌─────────────────────────────────────────────────────────┐
│ [Vue Générale] [Ventes] [Clients] [Opérations] [Produits] │
├─────────────────────────────────────────────────────────┤
│ Filtres: [📅 Période] [🌍 Région] [👤 Client Type]      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ┌─ KPIs Clés (3-4 métriques principales) ─────────────┐  │
│ │ [CA: 150K€] [Commandes: 1,245] [Clients: 890]     │  │
│ └─────────────────────────────────────────────────────┘  │
│                                                         │
│ ┌─ Graphiques Principaux ──────────────────────────────┐  │
│ │ [Evolution CA (ligne)]  [Top Produits (barres)]    │  │
│ │ [Geo CA (carte)]       [Performance (gauge)]       │  │
│ └─────────────────────────────────────────────────────┘  │
│                                                         │
│ ┌─ Métriques Secondaires ──────────────────────────────┐  │
│ │ [Délais] [Taux] [Ratios] [Alertes]                 │  │
│ └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

#### Contenu des Onglets

##### 🏠 Onglet "Vue Générale" (Page d'accueil)
- **Top 4 KPIs critiques** : CA du mois, Commandes du jour, Stock critique pointures, Taux conversion téléphonique
- **Graphique principal** : Evolution CA sur 12 mois
- **Alertes importantes** : Commandes en retard, stocks critiques par pointure populaire
- **Activité récente** : Dernières commandes, opérateurs actifs, appels du jour

##### 📊 Onglet "Ventes"
- CA par période, panier moyen, top modèles par CA/quantité
- Répartition géographique (régions/villes chargées dynamiquement)
- Performance par catégorie (Chaussures Homme, Chaussures Femme, Sandales, Baskets)
- Graphiques : Evolution temporelle, comparaisons période N vs N-1

##### 👥 Onglet "Clients" 
- Nouveaux clients par région
- Fréquence d'achat et fidélisation
- Analyse comportementale clients (tous traités de manière identique)
- Retours/échanges par pointure (crucial pour vente à distance)

##### ⚙️ Onglet "Opérations"
- Performance téléphonique (appels, conversions, suivi)
- Délais de traitement (confirmation → livraison)
- Performance des opérateurs (Confirmation vs Logistique)
- Gestion livraisons par zones tarifaires

##### 👟 Onglet "Chaussures & Stocks"
- Analyse stocks par pointures et couleurs 
- Rotation par catégorie (Homme, Femme, Sandales, Baskets)
- Analyse ABC des modèles et saisonnalité
- Alertes stocks critiques par pointure populaire

### 🎨 Principes UX Appliqués

#### 1. Hiérarchie Visuelle Clara
```css
/* Taille des métriques par importance */
.kpi-critical { font-size: 3rem; color: #1f2937; }    /* KPIs critiques */
.kpi-important { font-size: 2rem; color: #374151; }   /* KPIs importants */
.kpi-secondary { font-size: 1.5rem; color: #6b7280; } /* KPIs secondaires */
```

#### 2. Codes Couleurs Cohérents et Significatifs
- 🔵 **Bleu (#3b82f6)** : Ventes, CA, revenus financiers
- 🟢 **Vert (#10b981)** : Stocks disponibles, objectifs atteints, livraisons réussies
- 🟠 **Orange (#f59e0b)** : Stocks faibles, alertes pointures, attention requise
- 🔴 **Rouge (#ef4444)** : Ruptures de stock, retards livraison, urgences critiques
- 🟣 **Violet (#8b5cf6)** : Clients, fidélisation, segments professionnels
- 🟡 **Jaune (#eab308)** : Sabots médicaux, produits spécialisés, certifications
- 🔶 **Marron (#92400e)** : Chaussures cuir, produits premium

#### 3. Progressive Disclosure (Révélation Progressive)
- **Niveau 1** : Métriques principales visibles immédiatement
- **Niveau 2** : Détails accessibles au clic/hover avec tooltips
- **Niveau 3** : Drill-down vers analyses détaillées et historiques

#### 4. Design Responsive Optimisé
```css
/* Breakpoints adaptés */
Desktop (>1200px) : 4 colonnes de KPIs + sidebar
Tablet (768-1200px) : 2 colonnes + navigation tabs
Mobile (<768px) : 1 colonne + menu hamburger
```

#### 5. Interactions et Feedback Utilisateur
- **Hover Effects** : Zoom léger (scale 1.05) + ombres dynamiques
- **Loading States** : Spinners et skeletons pendant chargements
- **Animations** : Transitions fluides (300ms) entre états
- **Tooltips** : Informations contextuelles et explications calculs

### 🔧 Système de Filtres Intuitif

#### Interface des Filtres
```html
┌─ Barre de Filtres Sticky ─────────────────────────────┐
│ [📅 Période ▼] [🌍 Région ▼] [👤 Type Client ▼]    │
│ [🔍 Recherche] [📊 Comparer] [↻ Actualiser] [⚙️]    │
└───────────────────────────────────────────────────────┘
```

#### Logique de Persistance
- Filtres sauvegardés par utilisateur en session
- URL parameters pour partage de vues filtrées
- Bouton "Reset" pour revenir aux valeurs par défaut

### 📱 Adaptation Mobile-First

#### Navigation Mobile
- **Tab Bar** en bas d'écran pour navigation rapide
- **Swipe gestures** entre onglets
- **Cards empilables** avec scroll vertical infini
- **Touch-friendly** : boutons minimum 44px
- **Affichage optimisé stocks** : Vue compacte pointures disponibles

## Catégories de KPIs Spécialisés Chaussures

### 1. KPIs de Vente et Performance Commerciale 👟

#### 1.1 Chiffre d'Affaires (CA)
- **Description**: Montant total des ventes sur une période
- **Sources**: Table `Commande`
- **Filtres**: Période, région, client
- **Visualisation**: Graphique linéaire avec évolution temporelle
- **Fréquence de calcul**: Temps réel

#### 1.2 Nombre de Commandes
- **Description**: Volume total des commandes
- **Sources**: Table `Commande`
- **Filtres**: Période, statut, région
- **Visualisation**: Compteur avec indicateur de tendance
- **Fréquence de calcul**: Temps réel

#### 1.3 Panier Moyen
- **Description**: Montant moyen par commande
- **Calcul**: `CA Total / Nombre de Commandes`
- **Filtres**: Période, type de client
- **Visualisation**: Gauge avec objectif
- **Fréquence de calcul**: Quotidienne

#### 1.4 Top Modèles (CA et Quantité)
- **Description**: Modèles de chaussures les plus performants
- **Sources**: `Commande` + `Article`
- **Filtres**: Période, catégorie (Chaussures/Sandales/Baskets), pointure
- **Visualisation**: Tableau classé + graphique en barres avec répartition par pointures
- **Fréquence de calcul**: Quotidienne

#### 1.5 Répartition Géographique du CA (Maroc détaillé)
- **Description**: Performance par région et ville marocaine
- **Détail Maroc**: Régions et villes (chargées dynamiquement depuis la base)
- **Sources**: `Commande` + `Client` + `Ville` + `Region`
- **Filtres**: Période, niveau géographique (région/ville)
- **Visualisation**: Carte interactive Maroc + graphique en secteurs
- **Fréquence de calcul**: Quotidienne

#### 1.6 Performance par Catégorie de Chaussures
- **Description**: CA et volume par type réel Yoozak
- **Catégories**: Chaussures Homme, Chaussures Femme, Sandales, Baskets
- **Sources**: `Article.categorie` + `Commande`
- **Filtres**: Période, région, matériau
- **Visualisation**: Graphique en barres empilées + évolution temporelle
- **Fréquence de calcul**: Quotidienne

#### 1.7 Performance Téléphonique et Conversion
- **Description**: Efficacité du processus de vente téléphonique
- **Métriques**: Taux conversion appels, CA par opérateur confirmation
- **Sources**: `Operation` (types d'appels) + `Commande`
- **Filtres**: Période, opérateur, type d'appel
- **Visualisation**: Funnel conversion + performance individuelle
- **Fréquence de calcul**: Temps réel

### 2. KPIs Client 👥

#### 2.1 Nouveaux Clients par Région
- **Description**: Acquisition géographique (régions/villes BD)
- **Sources**: `Client` + `Ville` + `Region` (données dynamiques)
- **Filtres**: Période, région, canal d'acquisition
- **Visualisation**: Graphique linéaire + carte interactive Maroc
- **Fréquence de calcul**: Quotidienne

#### 2.2 Analyse Comportementale Clients
- **Description**: Patterns d'achat sans segmentation métier
- **Métriques**: Fréquence d'achat, panier moyen, fidélisation
- **Sources**: `Client` + historique `Commande`
- **Filtres**: Période, région, ancienneté client
- **Visualisation**: Matrice comportementale + cohortes
- **Fréquence de calcul**: Hebdomadaire

#### 2.3 Préférences Pointures par Région
- **Description**: Analyse géographique des tailles populaires
- **Métriques**: Pointures vendues par région, retours par taille
- **Sources**: `Commande` + `Article.pointure` + géolocalisation
- **Filtres**: Période, région, sexe (Homme/Femme)
- **Visualisation**: Heatmap géographique + distribution pointures
- **Fréquence de calcul**: Mensuelle

#### 2.4 Top Clients (Volume et CA)
- **Description**: Clients les plus actifs et rentables
- **Métriques**: CA total, fréquence commandes, ancienneté
- **Sources**: `Client` + `Commande` agrégés
- **Filtres**: Période, seuil CA/volume
- **Visualisation**: Tableau classé + profils détaillés
- **Fréquence de calcul**: Quotidienne

#### 2.5 Satisfaction et Retours Clients
- **Description**: Qualité perçue (crucial vente à distance chaussures)
- **Métriques**: Taux retour par motif, satisfaction pointures
- **Sources**: Données retours + `Operation` commentaires
- **Filtres**: Période, motif retour, pointure, modèle
- **Visualisation**: Dashboard satisfaction + alertes qualité
- **Fréquence de calcul**: Quotidienne

### 3. KPIs Opérationnels ⚙️

#### 3.1 Délais de Livraison par Zone Tarifaire Maroc
- **Description**: Temps livraison selon tarification Yoozak (20DH à 50DH)
- **Zones**: 
  - **Zone A** (20DH): Grandes villes (Casablanca, Rabat, Marrakech)
  - **Zone B** (30-35DH): Villes moyennes  
  - **Zone C** (40-50DH): Zones éloignées/rurales
- **Sources**: `Commande` + `Livraison` + `Ville.frais_livraison`
- **Filtres**: Période, zone tarifaire, type commande
- **Visualisation**: Carte délais Maroc + comparaison zones
- **Fréquence de calcul**: Temps réel

#### 3.2 Performance Livraison Gratuite
- **Description**: Efficacité de l'offre "livraison gratuite" Yoozak
- **Métriques**: Coût réel vs tarif normal, satisfaction client
- **Sources**: `Ville.frais_livraison` + coûts logistiques
- **Filtres**: Période, zone, montant commande
- **Visualisation**: Analyse coût-bénéfice + impact commercial
- **Fréquence de calcul**: Quotidienne

#### 3.3 Délai de Traitement Commandes Multi-Pointures
- **Description**: Complexité logistique chaussures (mix pointures/couleurs)
- **Sources**: `Panier` + `Article` + temps préparation
- **Filtres**: Période, nb articles différents, complexité commande
- **Visualisation**: Scatter plot complexité vs délai + optimisations
- **Fréquence de calcul**: Temps réel

#### 3.4 Efficacité Opérateurs par Catégorie
- **Description**: Performance selon spécialité produit (Homme, Femme, Sandales, Baskets)
- **Sources**: `OperatConfirme` + `OperatLogistic` + `Article.categorie`
- **Filtres**: Période, catégorie produit, opérateur
- **Visualisation**: Tableau performance + formation ciblée
- **Fréquence de calcul**: Quotidienne

#### 3.5 Gestion Stock-Livraison Synchronisée
- **Description**: Disponibilité pointures vs promesses livraison
- **Sources**: `Article.qte_disponible` + `Commande` + promesses délai
- **Filtres**: Pointure, région, stock critique
- **Visualisation**: Dashboard temps réel + alertes
- **Fréquence de calcul**: Temps réel

#### 3.6 Support Client 24/7 Performance
- **Description**: Efficacité service client continu Yoozak
- **Métriques**: Temps réponse, résolution problèmes tailles, satisfaction
- **Sources**: Tickets support + SAV + retours
- **Filtres**: Période, type problème, canal contact
- **Visualisation**: Dashboard support + amélioration continue
- **Fréquence de calcul**: Temps réel

### 4. KPIs Produits & Stocks 👟 (Spécialisés Chaussures)

#### 4.1 Analyse des Stocks par Pointures
- **Description**: Distribution et disponibilité par taille
- **Sources**: `Article.pointure` + `qte_disponible`
- **Filtres**: Période, modèle, catégorie
- **Visualisation**: Heatmap pointures + alertes ruptures populaires
- **Fréquence de calcul**: Temps réel

#### 4.2 Rotation des Stocks par Catégorie
- **Description**: Vitesse d'écoulement par catégorie (Chaussures Homme/Femme, Sandales, Baskets)
- **Sources**: `Article` + historique commandes
- **Filtres**: Période, catégorie, saison
- **Visualisation**: Graphique en barres + indicateurs saisonniers
- **Fréquence de calcul**: Hebdomadaire

#### 4.3 Analyse ABC des Modèles
- **Description**: Classification Pareto adaptée chaussures
- **Critères**: CA par modèle, rotation par pointure, marge
- **Sources**: `Article` + `Commande`
- **Filtres**: Période, catégorie
- **Visualisation**: Graphique Pareto + matrice ABC
- **Fréquence de calcul**: Mensuelle

#### 4.4 Performance par Gamme de Prix
- **Description**: Analyse des ventes par segment tarifaire
- **Métriques**: Volume et CA par tranche de prix, rotation par segment
- **Sources**: `Article.prix_unitaire` + `Commande`
- **Filtres**: Période, gamme de prix, catégorie
- **Visualisation**: Graphique par segments + analyse de profitabilité
- **Fréquence de calcul**: Quotidienne

#### 4.5 Saisonnalité des Ventes
- **Description**: Patterns saisonniers par type de chaussures
- **Sources**: Historique commandes + météo/saisons
- **Filtres**: Période, catégorie, région climatique
- **Visualisation**: Graphique saisonnier + prévisions
- **Fréquence de calcul**: Hebdomadaire

#### 4.6 Indicateurs Qualité et Retours
- **Description**: Taux de retour par modèle/pointure
- **Sources**: Données retours + motifs (taille, défaut, confort)
- **Filtres**: Période, modèle, motif retour
- **Visualisation**: Tableau de bord qualité + alertes
- **Fréquence de calcul**: Quotidienne

## Système de Filtres

### Filtres Temporels
- **Période prédéfinie**: Aujourd'hui, 7 jours, 30 jours, 3 mois, année
- **Période personnalisée**: Date de début + date de fin
- **Comparaison**: Période actuelle vs période précédente

### Filtres Géographiques Détaillés Maroc
- **Région**: Régions marocaines (chargées dynamiquement depuis la base)
- **Ville**: Villes marocaines avec cascade dépendante région
- **Zone tarifaire**: 20DH, 30DH, 35DH, 40DH, 50DH (selon `frais_livraison`)

### Filtres Métier Spécialisés Yoozak
- **Statut commande**: Nouveau, confirmé, expédié, livré
- **Type client**: Tous les clients traités de manière identique
- **Catégorie produit**: 
  - **Chaussures Homme** (style + confort)
  - **Chaussures Femme** (élégance + confort)
  - **Sandales** (respirabilité + style)
  - **Baskets** (sport + casual)
- **Pointure**: 37-41 (range principale Yoozak)
- **Couleur**: NOIR, BEIGE, MARRON, BLEU MARINE, BLEU CIEL, CAMEL
- **Matériau**: Cuir véritable vs autres
- **Zone livraison**: Selon tarifs 20DH à 50DH

### Filtres Avancés Spécialisés
- **Montant**: Seuils min/max (impact livraison gratuite)
- **Quantité**: Volume de commande
- **Délai livraison**: Par zone tarifaire (20DH à 50DH)
- **Pointure**: Sélection multiple (focus 37-41)
- **Qualité cuir**: Cuir véritable vs autres matériaux
- **Gamme de prix**: Segmentation par tranche tarifaire
- **Saisonnalité**: Périodes chaudes (sandales) vs froides (chaussures fermées)
- **Fréquence livraison**: Selon `frequence_livraison` par ville

## Technologies et Outils

### Backend
- **Django ORM**: Requêtes optimisées avec `select_related`, `prefetch_related`
- **Cache Redis**: Mise en cache des KPIs coûteux
- **Celery**: Calculs asynchrones pour les métriques complexes
- **PostgreSQL**: Requêtes analytiques avancées (window functions)

### Frontend
- **Chart.js / D3.js**: Visualisations interactives
- **Alpine.js**: Réactivité des filtres
- **Tailwind CSS**: Styling cohérent
- **WebSocket**: Mise à jour temps réel

### Performance
- **Vues matérialisées**: Pour les calculs lourds
- **Index optimisés**: Sur les colonnes de dates et foreign keys
- **Pagination**: Pour les gros datasets
- **Lazy loading**: Chargement progressif des graphiques

## Mise en Œuvre

### Phase 1: Foundation Yoozak (Semaine 1-2)
1. Structure composants KPIs spécialisés chaussures marocaines
2. Système filtres géographiques (régions et villes dynamiques, zones tarifaires)
3. KPIs vente essentiels + répartition géographique détaillée Maroc
4. Dashboard principal avec onglets adaptés métier Yoozak

### Phase 2: Extension Marché (Semaine 3-4)
1. KPIs clients comportementaux et fidélisation
2. Graphiques spécialisés (heatmap régions Maroc, analyse pointures)
3. Système cache Redis + optimisations géolocalisation
4. Intégration données météo/saisonnalité par région climatique

### Phase 3: Expertise Chaussures (Semaine 5-6)
1. KPIs avancés par gamme de prix et rotation stocks
2. Module satisfaction client (retours pointures, confort matériaux)
3. Analyses prédictives stocks par pointures et régions populaires
4. Système alertes spécialisées (ruptures par catégorie, zones à fort potentiel)

## Sécurité et Permissions

### Contrôle d'Accès
- **Admin**: Accès complet à tous les KPIs
- **Manager**: KPIs de leur région/équipe
- **Opérateur**: KPIs personnels uniquement
- **Client**: Accès restreint aux métriques publiques

### Audit Trail
- Log des consultations de KPIs
- Traçabilité des exports de données
- Historisation des modifications de filtres

## Maintenance et Evolution

### Monitoring
- Performance des requêtes KPIs
- Usage des différentes métriques
- Alertes sur les anomalies de données

### Documentation
- Guide utilisateur pour chaque KPI
- Documentation technique des calculs
- Changelog des évolutions

---

*Ce document évoluera en fonction des besoins métier et des retours utilisateurs.*
