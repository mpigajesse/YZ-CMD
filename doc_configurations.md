# Documentation des Paramètres KPI Configurables

## Vue d'ensemble

Ce document liste tous les paramètres configurables du système KPI YZ-CMD, organisés par catégorie. Ces paramètres permettent de personnaliser les calculs, seuils et affichages des indicateurs de performance.

**Résumé des catégories :**
- 🎯 **Seuils et Objectifs** : 4 paramètres de base
- 🚨 **Seuils d'Alerte et Performance** : 10 nouveaux paramètres
- ⚙️ **Paramètres de Calcul** : 4 paramètres de base + 4 avancés
- 📊 **Limites d'Affichage** : 6 paramètres d'interface
- 🖥️ **Affichage et Interface** : 4 paramètres UX
- 📈 **Périodes et Cycles** : 3 paramètres temporels
- 🎨 **Visuels et Couleurs** : 3 paramètres esthétiques

**Total : 38+ paramètres configurables identifiés**

---

## 🎯 Catégorie : Seuils et Objectifs

Ces paramètres définissent les valeurs cibles et les seuils d'alerte pour les différents KPIs.

### `stock_critique_seuil`
- **Description** : Seuil en dessous duquel un article est considéré en stock critique
- **Valeur par défaut** : `5.0`
- **Unité** : unités
- **Plage** : 0 - 100
- **Type** : Entier
- **Impact** : Détermine quand un article populaire est marqué comme "stock critique"

### `taux_conversion_objectif`
- **Description** : Objectif de taux de conversion (confirmations/appels)
- **Valeur par défaut** : `70.0`
- **Unité** : %
- **Plage** : 0 - 100
- **Type** : Décimal
- **Impact** : Référence pour évaluer la performance des opérateurs téléphoniques

### `delai_livraison_cible`
- **Description** : Délai de livraison cible en jours
- **Valeur par défaut** : `3.0`
- **Unité** : jours
- **Plage** : 1 - 30
- **Type** : Décimal
- **Impact** : Seuil pour l'évaluation de la performance logistique

### `satisfaction_minimale`
- **Description** : Score de satisfaction client minimal acceptable
- **Valeur par défaut** : `4.0`
- **Unité** : /5
- **Plage** : 1 - 5
- **Type** : Décimal
- **Impact** : Référence pour l'évaluation de la qualité de service

---

## ⚙️ Catégorie : Paramètres de Calcul

Ces paramètres influencent les algorithmes de calcul des KPIs et les critères d'analyse.

### `periode_analyse_defaut`
- **Description** : Période d'analyse par défaut pour les KPIs
- **Valeur par défaut** : `30`
- **Unité** : jours
- **Plage** : 1 - 365
- **Type** : Entier
- **Impact** : Définit la fenêtre temporelle standard pour tous les calculs KPI

### `article_populaire_seuil`
- **Description** : Nombre minimum de ventes pour qu'un article soit considéré populaire
- **Valeur par défaut** : `2`
- **Unité** : ventes
- **Plage** : 1 - 50
- **Type** : Entier
- **Impact** : Critère pour identifier les articles à surveiller en stock critique

### `client_fidele_seuil`
- **Description** : Nombre minimum de commandes pour qu'un client soit considéré fidèle
- **Valeur par défaut** : `2`
- **Unité** : commandes
- **Plage** : 2 - 10
- **Type** : Entier
- **Impact** : Définit le critère de fidélisation client dans les analyses

### `fidelisation_periode_jours`
- **Description** : Période en jours pour calculer la fidélisation
- **Valeur par défaut** : `90`
- **Unité** : jours
- **Plage** : 30 - 365
- **Type** : Entier
- **Impact** : Fenêtre temporelle pour l'analyse de fidélisation client

---

## 🖥️ Catégorie : Paramètres d'Affichage

Ces paramètres contrôlent l'interface utilisateur et l'expérience visuelle du dashboard.

### `rafraichissement_auto`
- **Description** : Intervalle de rafraîchissement automatique des données
- **Valeur par défaut** : `5`
- **Unité** : minutes
- **Plage** : 1 - 60
- **Type** : Entier
- **Impact** : Fréquence de mise à jour automatique du dashboard

### `afficher_tendances`
- **Description** : Afficher les indicateurs de tendance (1=Oui, 0=Non)
- **Valeur par défaut** : `1`
- **Unité** : booléen
- **Plage** : 0 - 1
- **Type** : Entier
- **Impact** : Active/désactive l'affichage des flèches de tendance

### `activer_animations`
- **Description** : Activer les animations dans l'interface (1=Oui, 0=Non)
- **Valeur par défaut** : `1`
- **Unité** : booléen
- **Plage** : 0 - 1
- **Type** : Entier
- **Impact** : Active/désactive les effets visuels et transitions

### `decimales_affichage`
- **Description** : Nombre de décimales à afficher pour les valeurs
- **Valeur par défaut** : `1`
- **Unité** : décimales
- **Plage** : 0 - 3
- **Type** : Entier
- **Impact** : Précision d'affichage des valeurs numériques

---

## 🚨 Catégorie : Seuils d'Alerte et de Performance

Ces paramètres définissent les seuils qui déterminent les statuts (excellent/bon/warning/critique) des KPIs.

### `delai_livraison_excellent`
- **Description** : Seuil délai livraison considéré comme excellent
- **Valeur par défaut** : `2.0`
- **Unité** : jours
- **Plage** : 1 - 5
- **Type** : Décimal
- **Impact** : Statut "excellent" pour le délai de livraison

### `delai_livraison_bon`
- **Description** : Seuil délai livraison considéré comme bon
- **Valeur par défaut** : `3.0`
- **Unité** : jours
- **Plage** : 2 - 7
- **Type** : Décimal
- **Impact** : Statut "good" pour le délai de livraison

### `delai_livraison_warning`
- **Description** : Seuil délai livraison en alerte
- **Valeur par défaut** : `5.0`
- **Unité** : jours
- **Plage** : 3 - 10
- **Type** : Décimal
- **Impact** : Statut "warning" pour le délai de livraison

### `taux_retour_excellent`
- **Description** : Seuil taux retour considéré comme excellent
- **Valeur par défaut** : `5.0`
- **Unité** : %
- **Plage** : 0 - 10
- **Type** : Décimal
- **Impact** : Statut "excellent" pour le taux de retour

### `taux_retour_bon`
- **Description** : Seuil taux retour considéré comme bon
- **Valeur par défaut** : `10.0`
- **Unité** : %
- **Plage** : 5 - 15
- **Type** : Décimal
- **Impact** : Statut "good" pour le taux de retour

### `taux_retour_warning`
- **Description** : Seuil taux retour en alerte
- **Valeur par défaut** : `15.0`
- **Unité** : %
- **Plage** : 10 - 25
- **Type** : Décimal
- **Impact** : Statut "warning" pour le taux de retour

### `taux_confirmation_excellent`
- **Description** : Seuil taux confirmation considéré comme excellent
- **Valeur par défaut** : `80.0`
- **Unité** : %
- **Plage** : 70 - 100
- **Type** : Décimal
- **Impact** : Statut "excellent" pour le taux de confirmation

### `taux_confirmation_bon`
- **Description** : Seuil taux confirmation considéré comme bon
- **Valeur par défaut** : `70.0`
- **Unité** : %
- **Plage** : 60 - 90
- **Type** : Décimal
- **Impact** : Statut "good" pour le taux de confirmation

### `taux_confirmation_warning`
- **Description** : Seuil taux confirmation en alerte
- **Valeur par défaut** : `60.0`
- **Unité** : %
- **Plage** : 40 - 80
- **Type** : Décimal
- **Impact** : Statut "warning" pour le taux de confirmation

### `stock_critique_alerte_seuil`
- **Description** : Nombre d'articles critiques déclenchant une alerte
- **Valeur par défaut** : `3`
- **Unité** : articles
- **Plage** : 1 - 10
- **Type** : Entier
- **Impact** : Statut "critical" pour le stock critique

---

## ⚡ Catégorie : Paramètres de Calcul Avancés

Ces paramètres influencent les formules et algorithmes de calcul des KPIs.

### `facteur_impact_retour_satisfaction`
- **Description** : Facteur d'impact du taux retour sur le score de satisfaction
- **Valeur par défaut** : `0.15`
- **Unité** : coefficient
- **Plage** : 0.1 - 0.5
- **Type** : Décimal
- **Impact** : Sensibilité du calcul de satisfaction aux retours

### `client_regulier_commandes_min`
- **Description** : Nombre minimum de commandes pour être considéré comme client régulier
- **Valeur par défaut** : `3`
- **Unité** : commandes
- **Plage** : 2 - 10
- **Type** : Entier
- **Impact** : Critère de segmentation client "régulier"

### `client_occasionnel_commandes`
- **Description** : Nombre exact de commandes pour être considéré comme client occasionnel
- **Valeur par défaut** : `2`
- **Unité** : commandes
- **Plage** : 1 - 5
- **Type** : Entier
- **Impact** : Critère de segmentation client "occasionnel"

### `periode_comparaison_jours`
- **Description** : Période en jours pour la comparaison des tendances
- **Valeur par défaut** : `30`
- **Unité** : jours
- **Plage** : 7 - 90
- **Type** : Entier
- **Impact** : Calcul des tendances et comparaisons période précédente

---

## 📊 Catégorie : Limites d'Affichage et Interface

Ces paramètres contrôlent la présentation et les limites des données affichées.

### `top_villes_limite`
- **Description** : Nombre de villes à afficher dans le top géographique
- **Valeur par défaut** : `5`
- **Unité** : éléments
- **Plage** : 3 - 20
- **Type** : Entier
- **Impact** : Limite d'affichage du top des villes

### `top_modeles_limite_defaut`
- **Description** : Limite par défaut pour le top des modèles
- **Valeur par défaut** : `10`
- **Unité** : éléments
- **Plage** : 5 - 50
- **Type** : Entier
- **Impact** : Nombre de modèles affichés par défaut

### `top_operateurs_limite`
- **Description** : Nombre d'opérateurs à afficher dans les performances
- **Valeur par défaut** : `3`
- **Unité** : éléments
- **Plage** : 2 - 10
- **Type** : Entier
- **Impact** : Limite d'affichage des performances opérateurs

### `top_clients_vip_limite`
- **Description** : Nombre de clients VIP à afficher
- **Valeur par défaut** : `5`
- **Unité** : éléments
- **Plage** : 3 - 15
- **Type** : Entier
- **Impact** : Limite d'affichage des clients VIP

### `seuil_format_milliers`
- **Description** : Seuil à partir duquel utiliser le format K (milliers)
- **Valeur par défaut** : `1000`
- **Unité** : montant
- **Plage** : 500 - 5000
- **Type** : Entier
- **Impact** : Formatage automatique en "K DH"

### `seuil_format_millions`
- **Description** : Seuil à partir duquel utiliser le format M (millions)
- **Valeur par défaut** : `1000000`
- **Unité** : montant
- **Plage** : 500000 - 5000000
- **Type** : Entier
- **Impact** : Formatage automatique en "M DH"

---

## 🔧 Paramètres Additionnels (Legacy)

Ces paramètres sont référencés dans le code pour la validation mais peuvent nécessiter une configuration explicite :

### `delai_livraison_defaut`
- **Description** : Délai de livraison par défaut (legacy)
- **Type** : Entier
- **Usage** : Validation des champs entiers

### `fidelisation_commandes_min`
- **Description** : Nombre minimum de commandes pour fidélisation (legacy)
- **Type** : Entier
- **Usage** : Validation des champs entiers

### `periode_analyse_standard`
- **Description** : Période d'analyse standard (legacy)
- **Type** : Entier
- **Usage** : Validation des champs entiers

### `delai_livraison_alerte`
- **Description** : Seuil d'alerte délai livraison (legacy)
- **Type** : Entier
- **Usage** : Validation des champs entiers

### `stock_ventes_minimum`
- **Description** : Minimum de ventes pour analyse stock (legacy)
- **Type** : Entier
- **Usage** : Validation des champs entiers

---

## 📈 Catégorie : Paramètres de Périodes et Cycles

Ces paramètres définissent les cycles temporels pour les analyses et calculs.

### `periode_analyse_evolution`
- **Description** : Période par défaut pour l'évolution du CA (7j/30j/90j)
- **Valeur par défaut** : `30`
- **Unité** : jours
- **Plage** : 7 - 365
- **Type** : Entier
- **Impact** : Période d'analyse des graphiques d'évolution

### `periode_top_modeles`
- **Description** : Période par défaut pour le calcul du top modèles
- **Valeur par défaut** : `30`
- **Unité** : jours
- **Plage** : 7 - 180
- **Type** : Entier
- **Impact** : Période d'analyse des ventes par modèle

### `periode_performance_regions`
- **Description** : Période par défaut pour l'analyse des performances régionales
- **Valeur par défaut** : `30`
- **Unité** : jours
- **Plage** : 7 - 365
- **Type** : Entier
- **Impact** : Période d'analyse géographique

---

## 🎨 Catégorie : Paramètres Visuels et Couleurs

Ces paramètres contrôlent l'apparence visuelle des graphiques et interfaces.

### `couleurs_graphiques_primaires`
- **Description** : Palette de couleurs principale pour les graphiques
- **Valeur par défaut** : `"#3b82f6,#ef4444,#10b981,#f59e0b,#8b5cf6"`
- **Unité** : hex colors
- **Type** : Chaîne
- **Impact** : Couleurs des éléments graphiques principaux

### `couleurs_graphiques_secondaires`
- **Description** : Palette de couleurs secondaire pour les graphiques
- **Valeur par défaut** : `"#ec4899,#6b7280,#14b8a6,#f97316,#84cc16"`
- **Unité** : hex colors
- **Type** : Chaîne
- **Impact** : Couleurs des éléments graphiques secondaires

### `animation_duree_transition`
- **Description** : Durée des animations de transition en millisecondes
- **Valeur par défaut** : `300`
- **Unité** : ms
- **Plage** : 100 - 1000
- **Type** : Entier
- **Impact** : Vitesse des animations d'interface

---

## 📊 Impact Business des Paramètres

### Paramètres Critiques
- `stock_critique_seuil` : Impact direct sur les alertes de rupture de stock
- `taux_conversion_objectif` : Référence pour l'évaluation des performances commerciales
- `periode_analyse_defaut` : Base de tous les calculs KPI
- `facteur_impact_retour_satisfaction` : Influence directe sur le score de satisfaction

### Paramètres d'Optimisation
- `article_populaire_seuil` : Affine la détection des produits stratégiques
- `client_fidele_seuil` : Améliore la segmentation client
- `delai_livraison_cible` : Optimise la satisfaction logistique
- Seuils de performance (excellent/bon/warning) : Optimisent les alertes et notifications

### Paramètres UX
- `rafraichissement_auto` : Balance performance vs actualité des données
- `afficher_tendances` : Aide à la prise de décision rapide
- `decimales_affichage` : Clarté vs précision des données
- Limites d'affichage : Performance vs complétude de l'information
- Couleurs et animations : Expérience utilisateur et lisibilité

### Paramètres de Segmentation
- `client_regulier_commandes_min` : Affine l'analyse comportementale
- `client_occasionnel_commandes` : Améliore les stratégies marketing ciblées
- `periode_comparaison_jours` : Précision des analyses de tendance

---

## 🔧 Recommandations d'Implémentation

### Phase 1 - Seuils Critiques
1. Implémenter les seuils de performance (excellent/bon/warning)
2. Ajouter le facteur d'impact satisfaction
3. Configurer les limites de stock critique

### Phase 2 - Optimisation Calculs
1. Paramétrer les critères de segmentation clients
2. Rendre configurables les périodes d'analyse
3. Ajuster les limites d'affichage

### Phase 3 - Interface et UX
1. Personnaliser les couleurs graphiques
2. Configurer les formats d'affichage (K, M)
3. Optimiser les animations et transitions

### Phase 4 - Avancé
1. Paramètres de cycles temporels
2. Configurations visuelles avancées
3. Intégration avec les préférences utilisateur

---

## 🔄 Gestion des Configurations

### États Système
1. **BD Vide** : Utilisation automatique des valeurs par défaut codées en dur
2. **BD Peuplée** : Chargement depuis `KPIConfiguration`
3. **Reset** : Restauration aux valeurs par défaut via API

### Validation
- **Types** : Entiers vs décimaux selon le paramètre
- **Plages** : Respect des min/max définis
- **Métier** : Validations spécifiques (ex: pourcentages 0-100)

### API Endpoints
- `GET /get_configurations` : Récupération des paramètres
- `POST /save_configurations` : Sauvegarde avec validation
- `POST /reset_configurations` : Restauration par défaut

---

*Dernière mise à jour : Juillet 2025*
*Système : YZ-CMD KPI Dashboard*
