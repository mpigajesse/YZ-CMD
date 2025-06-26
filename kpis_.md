# Dashboard KPIs Yoozak - Documentation Technique

## Vue d'ensemble

Le Dashboard KPIs Yoozak est un système de suivi en temps réel des indicateurs de performance clés pour l'activité e-commerce de chaussures. Il est organisé en 5 onglets principaux, chacun ciblant un aspect spécifique de l'activité.

---

## 🏠 Onglet Vue Générale

### Description
Vue d'ensemble des 4 indicateurs critiques pour le pilotage quotidien + indicateurs synthétiques et graphiques de tendances.

### KPIs Principaux (Critiques)

#### 1. **Chiffre d'Affaires**
- **Nom affiché :** "Chiffre d'Affaires - Ce mois"
- **Signification :** Revenus générés depuis le début du mois en cours
- **Méthode de calcul :** Additionne le montant total de toutes les commandes passées depuis le 1er du mois, en excluant les commandes annulées
- **Tendance :** Comparaison avec le mois précédent (en pourcentage d'évolution)
- **Icône :** fas fa-coins (pièces)
- **Couleur :** Bleu

#### 2. **Commandes du Jour**
- **Nom affiché :** "Commandes - Aujourd'hui"
- **Signification :** Nombre de commandes passées dans la journée actuelle
- **Méthode de calcul :** Compte toutes les commandes créées à la date du jour, sans distinction de statut
- **Tendance :** Différence absolue avec le nombre de commandes d'hier
- **Icône :** fas fa-shopping-cart
- **Couleur :** Vert

#### 3. **Stock Critique**
- **Nom affiché :** "Stock Critique - Articles populaires"
- **Signification :** Nombre d'articles populaires en risque de rupture de stock
- **Méthode de calcul :** 
  - Identifie d'abord les articles populaires (ayant généré au moins 2 ventes dans les 30 derniers jours)
  - Compte ensuite parmi ces articles populaires ceux qui ont moins de 5 unités en stock
- **Logique business :** Se concentre uniquement sur les articles à forte rotation pour éviter les alertes inutiles sur les articles dormants
- **Icône :** fas fa-exclamation-triangle
- **Couleur :** Orange

#### 4. **Taux de Conversion Téléphonique**
- **Nom affiché :** "Taux Conversion - Appels téléphoniques"
- **Signification :** Pourcentage d'appels téléphoniques qui génèrent une commande confirmée
- **Méthode de calcul :** Divise le nombre de commandes confirmées par le nombre total d'appels effectués par les opérateurs
- **Cible métier :** 70% (objectif de performance)
- **Icône :** fas fa-phone
- **Couleur :** Violet

### KPIs Secondaires (Synthétiques)

#### 1. **Panier Moyen**
- **Méthode de calcul :** Divise le chiffre d'affaires total des 30 derniers jours par le nombre de commandes sur la même période
- **Exclusions :** Les commandes annulées ne sont pas prises en compte
- **Couleur :** Vert

#### 2. **Délai de Livraison**
- **Méthode de calcul :** Calcule la moyenne des délais entre la date de commande et la date de livraison effective sur les 30 derniers jours
- **Condition :** Seules les commandes effectivement livrées sont incluses dans le calcul
- **Valeur par défaut :** 3 jours si aucune donnée n'est disponible
- **Couleur :** Violet

#### 3. **Satisfaction Client**
- **Méthode de calcul :** Basée sur une formule inverse du taux de retour : Satisfaction = 5 - (taux_retour × 0.15)
- **Échelle d'interprétation :**
  - 0-5% de retours = Excellent (4.5-5.0/5)
  - 5-10% de retours = Très bon (4.0-4.5/5)
  - 10-15% de retours = Bon (3.25-4.0/5)
  - 15-25% de retours = Moyen (2.5-3.25/5)
  - Plus de 25% de retours = Mauvais (moins de 2.5/5)
- **Unité :** Sur 5 points
- **Couleur :** Jaune

#### 4. **Taux de Livraison**
- **Méthode de calcul :** Divise le nombre de commandes livrées par le nombre de commandes confirmées, multiplié par 100 pour obtenir un pourcentage
- **Période de référence :** 30 derniers jours
- **Couleur :** Vert

#### 5. **Stock Total**
- **Méthode de calcul :** Additionne la quantité disponible de tous les articles actifs du catalogue
- **Tendance :** Variation par rapport à il y a 7 jours
- **Couleur :** Bleu

### Graphiques

#### 1. **Évolution du Chiffre d'Affaires**
- **Type de graphique :** Courbe linéaire interactive
- **Périodes sélectionnables :** 7 jours, 30 jours, ou 90 jours
- **Données affichées :** Chiffre d'affaires quotidien cumulé
- **Résumé affiché :** CA du mois actuel, pourcentage de tendance, et CA des 30 derniers jours
- **Technologie :** Chart.js pour l'interactivité

#### 2. **Performance par Région**
- **Type de graphique :** Barres horizontales avec code couleur
- **Données affichées :** Chiffre d'affaires par région (top 5 des meilleures performances)
- **Période de référence :** 30 derniers jours
- **Informations détaillées :** Pourcentage de contribution, montant en dirhams, et nombre de commandes par région

---

## 📊 Onglet Ventes

### Description
Analyse approfondie des performances commerciales, répartitions géographiques et par produits.

### KPIs Principaux

#### 1. **Chiffre d'Affaires 30j**
- **Méthode de calcul :** Additionne le montant de toutes les commandes des 30 derniers jours en excluant les commandes annulées
- **Tendance :** Comparaison avec la période précédente de 30 jours
- **Format d'affichage :** Adaptatif (K DH pour les milliers, M DH pour les millions)

#### 2. **Panier Moyen**
- **Méthode de calcul :** Divise le chiffre d'affaires total par le nombre de commandes
- **Exclusions :** Commandes annulées et commandes de montant nul
- **Utilité métier :** Indicateur clé de l'évolution du comportement d'achat des clients

#### 3. **Taux de Confirmation**
- **Méthode de calcul :** Divise le nombre de commandes confirmées par le nombre total de commandes, multiplié par 100
- **Signification métier :** Mesure l'efficacité du processus de confirmation téléphonique de Yoozak
- **Période de référence :** 30 derniers jours

#### 4. **Nombre de Commandes**
- **Méthode de calcul :** Décompte de toutes les commandes non annulées sur les 30 derniers jours
- **Tendance :** Différence absolue (en nombre) avec la période précédente
- **Indicateur de :** Volume global d'activité commerciale

### Analyses Détaillées

#### **Top 5 Modèles par Chiffre d'Affaires**
- **Critère de sélection :** Les 5 articles ayant généré le plus de revenus sur les 30 derniers jours
- **Exclusions :** Commandes annulées
- **Données affichées :** Chiffre d'affaires total et quantité vendue par article
- **Utilité :** Identifier les modèles de chaussures les plus rentables

#### **Répartition par Catégorie**
- **Objectif :** Analyser la performance par type de chaussures (sneakers, boots, sandales, etc.)
- **Métriques :** Chiffre d'affaires et quantités vendues par catégorie
- **Utilité métier :** Identifier les segments de produits porteurs et adapter la stratégie d'achat

#### **Répartition Géographique**
- **Données :** Top 5 des villes génératrices de chiffre d'affaires
- **Informations détaillées :** Chiffre d'affaires et nombre de commandes par ville
- **Analyse :** Corrélation entre région et ville pour optimiser la logistique

#### **Performance des Opérateurs**
- **Métrique principale :** Statistiques sur les appels téléphoniques effectués
- **Indicateurs :** Taux de conversion et nombre d'appels par opérateur
- **Classement :** Top 3 des opérateurs par volume d'appels
- **Utilité :** Évaluation des performances individuelles et formation ciblée

---

## 👥 Onglet Clients

### Description
Analyse comportementale de la clientèle, fidélisation et segmentation.

### KPIs Principaux

#### 1. **Nouveaux Clients**
- **Nom affiché :** "Nouveaux Clients - Ce mois"
- **Méthode de calcul :** Compte tous les clients créés depuis le début du mois en cours
- **Tendance :** Comparaison avec le nombre de nouveaux clients du mois précédent
- **Métrique complémentaire :** Affichage de la moyenne journalière de création de comptes

#### 2. **Clients Actifs**
- **Nom affiché :** "Clients Actifs - 30 derniers jours"
- **Définition :** Clients ayant passé au moins une commande au cours des 30 derniers jours
- **Exclusions :** Les commandes annulées ne comptent pas pour déterminer l'activité
- **Indicateur de :** Niveau d'engagement et de rétention de la base client

#### 3. **Taux de Fidélisation**
- **Définition de la fidélité :** Un client est considéré comme fidèle s'il a passé 2 commandes ou plus sur les 30 derniers jours
- **Méthode de calcul :** Divise le nombre de clients fidèles par le nombre total de clients actifs, multiplié par 100
- **Logique métier :** Le seuil de 2 commandes correspond aux standards réalistes du e-commerce
- **Objectif cible :** Dépasser 30% de taux de fidélisation

#### 4. **Valeur Vie Client (CLV)**
- **Définition :** Customer Lifetime Value - revenus moyens générés par client
- **Méthode de calcul :** Divise le chiffre d'affaires total par le nombre de clients actifs sur la période
- **Utilité métier :** Évaluation de la rentabilité moyenne par client et aide à la segmentation

### Analyses Avancées

#### **Performance Mensuelle**
- **Commandes du Mois :** Évolution vs mois précédent
- **CA Moyen par Client :** Répartition du CA sur la base active
- **Segmentation :** Identification des gros clients

#### **Top Clients**
- Classement par CA généré (période 30j)
- Nombre de commandes par client VIP
- Analyse comportementale

#### **Répartition Géographique des Clients**
- Distribution par région
- Concentration urbaine vs rurale
- Potentiel de développement territorial

---

## 🔧 Architecture Technique

### Backend (Django)
- **Fichier principal :** `kpis/views.py` - contient toute la logique de calcul des indicateurs
- **Endpoints API disponibles :**
  - `/kpis/api/vue-generale/` - Fournit les données pour l'onglet Vue Générale
  - `/kpis/api/ventes/` - Fournit les données pour l'onglet Ventes
  - `/kpis/api/clients/` - Fournit les données pour l'onglet Clients
  - `/kpis/api/evolution-ca/` - Données pour le graphique d'évolution du CA
  - `/kpis/api/performance-regions/` - Données pour les graphiques régionaux

### Frontend (JavaScript)
- **Gestionnaire principal :** `static/js/kpis/dashboard.js` - coordonne tous les affichages
- **Classe principale :** `YoozakKPIManager` - gère les interactions et mises à jour
- **Rafraîchissement automatique :** Toutes les 5 minutes pour maintenir les données à jour
- **Bibliothèque graphiques :** Chart.js pour tous les graphiques interactifs

### Base de Données
- **Modèles principaux utilisés :**
  - `Commande` - Stockage des commandes clients avec dates et montants
  - `Client` - Base de données clientèle avec dates de création
  - `Article` - Catalogue produits avec stocks et catégories
  - `Panier` - Détail des articles commandés (liaison commande-article)
  - `EtatCommande` - Suivi du workflow des commandes (confirmé, livré, etc.)
  - `Operation` - Actions des opérateurs (appels, confirmations)

### Sécurité et Performance
- **Authentification obligatoire :** Toutes les vues nécessitent une connexion utilisateur
- **Validation des données :** Filtrage et vérification de tous les paramètres d'entrée
- **Gestion d'erreurs robuste :** Messages d'erreur explicites et gestion des cas limites
- **Optimisation requêtes :** Utilisation d'annotations et de filtres pour limiter les accès base

---

## 📈 Logiques Métier Spécifiques

### Logiques Intelligentes Implementées

1. **Stock Critique vs Stock Faible**
   - Ne se contente pas d'alerter sur tous les articles en stock bas
   - Se concentre uniquement sur les articles ayant une forte rotation (vendus récemment)
   - Évite les fausses alertes sur les articles dormants ou en fin de vie

2. **Satisfaction Client Réaliste**
   - Plutôt que de demander une notation directe aux clients (peu fiable)
   - Utilise le taux de retour comme indicateur objectif de satisfaction
   - Applique une échelle réaliste adaptée aux standards du e-commerce

3. **Performance des Opérateurs**
   - Distingue les différents types d'appels (prospection, suivi, etc.)
   - Se base sur les confirmations réelles plutôt que sur les promesses
   - Permet une évaluation objective des performances individuelles

4. **Fidélisation Pragmatique**
   - Définit un seuil réaliste (2+ commandes) pour qualifier un client fidèle
   - Adapté au cycle d'achat des chaussures (achat pas quotidien)
   - Exclut les commandes problématiques qui faussent l'analyse

### Gestion des Situations Particulières

- **Absence de données :** Valeurs par défaut cohérentes avec le métier (exemple : délai de 3 jours par défaut)
- **Divisions par zéro :** Vérifications systématiques pour éviter les erreurs de calcul  
- **Données incohérentes :** Filtrage automatique des anomalies (commandes négatives, dates futures, etc.)
- **Optimisation performance :** Requêtes optimisées pour éviter la surcharge de la base de données

---

## 🎯 Objectifs et Seuils Métier

| KPI | Excellent | Bon | Attention | Critique |
|-----|-----------|-----|-----------|----------|
| Taux Conversion | >70% | 60-70% | 50-60% | <50% |
| Délai Livraison | <2j | 2-3j | 3-5j | >5j |
| Satisfaction | >4.5/5 | 4.0-4.5 | 3.0-4.0 | <3.0 |
| Taux Retour | <5% | 5-10% | 10-15% | >15% |
| Fidélisation | >40% | 30-40% | 20-30% | <20% |

Cette documentation reflète l'implémentation actuelle du dashboard, optimisée pour le business model Yoozak de vente de chaussures par téléphone.
