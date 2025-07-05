# 📈 Performance Opérateurs - Spécifications Techniques

## 🎯 Objectif
Analyser la performance individuelle et collective des opérateurs avec des métriques détaillées de productivité et efficacité pour optimiser les processus de confirmation et de vente.

---

## 📊 Métriques à Afficher

### 1. 📞 Métriques de Confirmation
| Métrique | Description | Calcul | Exemple |
|----------|-------------|---------|---------|
| **Actions pour confirmation** | Nombre moyen d'actions nécessaires avant confirmation | `total_actions / nb_confirmations` | 8.5 tentatives |
| **Commandes affectées** | Nombre de commandes assignées à l'opérateur | `COUNT(commandes WHERE affectee)` | 45 commandes |
| **Commandes confirmées** | Nombre de commandes confirmées par l'opérateur | `COUNT(commandes WHERE confirmee)` | 32 commandes |
| **En cours confirmation** | Commandes actuellement en traitement | `COUNT(commandes WHERE en_cours_confirmation)` | 8 commandes |
| **Taux de confirmation** | Efficacité de confirmation | `(confirmees / affectees) × 100` | 71.1% |

### 2. 💰 Métriques Commerciales
| Métrique | Description | Calcul | Exemple |
|----------|-------------|---------|---------|
| **Commandes upsell** | Ventes additionnelles réalisées | `COUNT(commandes WHERE is_upsell=True)` | 12 upsells |
| **Panier moyen** | Montant moyen par commande | `AVG(total_cmd)` | 245 DH |
| **Panier maximum** | Plus grosse vente de la période | `MAX(total_cmd)` | 1,250 DH |
| **Panier minimum** | Plus petite vente de la période | `MIN(total_cmd)` | 85 DH |
| **Articles par commande** | Nombre moyen d'articles | `AVG(nb_articles_par_commande)` | 2.3 articles |

---

## 🏗️ Architecture UX

### Structure Hiérarchique
```
📈 Performance Opérateurs
├── 🎛️ Filtres & Contrôles (en haut)
│   ├── Période (Aujourd'hui, Cette semaine, Ce mois, Cette année, Personnalisée)
│   ├── Type d'opérateur (Tous, CONFIRMATION, LOGISTIQUE, PREPARATION)
│   └── Recherche par nom
├── 📊 Vue Générale (métriques globales équipe)
├── 👥 Performance par Type d'Opérateur (sections accordéon)
│   ├── 📞 CONFIRMATION
│   ├── 📦 LOGISTIQUE  
│   └── 🎯 PREPARATION
└── 👤 Détail Individuel (tableau interactif sortable)
```

### Types d'Opérateurs (selon modèle existant)
- **📞 CONFIRMATION** : Opérateurs de confirmation téléphonique
- **📦 LOGISTIQUE** : Opérateurs logistiques (livraison, transport)
- **🎯 PREPARATION** : Opérateurs de préparation de commandes

---

## 🎨 Design UX Détaillé

### Section 1 : Vue Générale (Cards métriques)
```
┌─────── Actions Totales ──────┐ ┌─────── Taux Global ──────┐ ┌─────── Panier Moyen ──────┐
│           1,247              │ │          73.2%           │ │         245 DH            │
│        tentatives            │ │      confirmation        │ │    tous opérateurs        │
│   📈 +15% vs hier           │ │   🔻 -2.3% vs hier      │ │   📈 +8% vs hier         │
└──────────────────────────────┘ └──────────────────────────┘ └───────────────────────────┘

┌─────── Commandes Totales ────┐ ┌─────── Taux Upsell ──────┐ ┌─────── Nb Opérateurs ─────┐
│           156                │ │          18.5%           │ │         22 actifs         │
│       confirmées             │ │       sur confirmées     │ │      sur 28 total         │
│   📈 +12 vs hier           │ │   📈 +3.2% vs hier      │ │   🟢 Tous connectés      │
└──────────────────────────────┘ └──────────────────────────┘ └───────────────────────────┘
```

### Section 2 : Performance par Type (Accordéon)
```
📞 CONFIRMATION (12 actifs) ────────────────────▼
┌─────────────────────────────────────────────────────────────────────┐
│ Métrique              │ Moyenne  │ Meilleur      │ Pire        │ Obj.│
├───────────────────────┼──────────┼───────────────┼─────────────┼─────┤
│ Taux confirmation     │  68.5%   │ 89.2% (Ali M.)│ 45% (Sara K)│ 70% │
│ Actions/confirmation  │   8.2    │ 4.1 (Ali M.)  │ 15.3 (Sara) │ <10 │
│ Panier moyen         │ 235 DH   │ 456 DH (Ali)  │ 125 DH      │ 250 │
│ Commandes/jour       │   15.3   │ 28 (Ali M.)   │ 8 (Sara K.) │ 20  │
│ Taux upsell          │  12.8%   │ 25% (Ali M.)  │ 3% (Sara K.)│ 15% │
└─────────────────────────────────────────────────────────────────────┘

📦 LOGISTIQUE (5 actifs) ────────────────────────▼
┌─────────────────────────────────────────────────────────────────────┐
│ Métrique              │ Moyenne  │ Meilleur      │ Pire        │ Obj.│
├───────────────────────┼──────────┼───────────────┼─────────────┼─────┤
│ Commandes traitées    │   45.2   │ 78 (Hassan)   │ 25 (Amina)  │ 50  │
│ Temps moyen/commande  │  12.5min │ 8min (Hassan) │ 18min       │ <15 │
│ Taux erreur livraison │   2.1%   │ 0.5% (Hassan) │ 5.2%        │ <3% │
│ Satisfaction client   │   4.2/5  │ 4.8/5         │ 3.5/5       │ >4  │
└─────────────────────────────────────────────────────────────────────┘

🎯 PREPARATION (8 actifs) ───────────────────────▼
┌─────────────────────────────────────────────────────────────────────┐
│ Métrique              │ Moyenne  │ Meilleur      │ Pire        │ Obj.│
├───────────────────────┼──────────┼───────────────┼─────────────┼─────┤
│ Commandes préparées   │   32.1   │ 52 (Youssef)  │ 18 (Nadia)  │ 35  │
│ Temps préparation     │  15.8min │ 11min (Youssef)│ 22min      │ <18 │
│ Taux erreur articles  │   1.8%   │ 0.2% (Youssef)│ 4.1%        │ <2% │
│ Articles/heure        │   18.5   │ 28 (Youssef)  │ 12 (Nadia)  │ 20  │
└─────────────────────────────────────────────────────────────────────┘
```

### Section 3 : Tableau Détaillé Individuel
```
🔍 Rechercher: [_____________] 📊 Trier par: [Taux confirmation ▼] 📄 Export: [Excel]

┌─────────────┬────────┬──────────┬──────────┬────────┬─────────┬────────┬──────────┬─────────┐
│ Opérateur   │ Type   │ Affectées│Confirmées│ Taux % │ Actions │ Upsell │ Panier   │ Status  │
├─────────────┼────────┼──────────┼──────────┼────────┼─────────┼────────┼──────────┼─────────┤
│ 🥇 Ali M.   │Confirm │    52    │    46    │ 88.5%  │   4.8   │   12   │ 456 DH   │ 🟢 Actif│
│ 🥈 Hassan B.│Logist. │    67    │    63    │ 94.0%  │   2.1   │   N/A  │ N/A      │ 🟢 Actif│
│ 🥉 Youssef K│Prepar. │    45    │    42    │ 93.3%  │   3.2   │   N/A  │ N/A      │ 🟢 Actif│
│ Fatima M.   │Confirm │    38    │    29    │ 76.3%  │   6.1   │    8   │ 289 DH   │ � Actif│
│ Nadia R.    │Prepar. │    33    │    25    │ 75.8%  │   8.1   │   N/A  │ N/A      │ � Pause│
│ ...         │ ...    │   ...    │   ...    │  ...   │   ...   │  ...   │   ...    │   ...   │
└─────────────┴────────┴──────────┴──────────┴────────┴─────────┴────────┴──────────┴─────────┘

📈 Légende: 🥇🥈🥉 Top performers | 🟢 Performance normale | 🟡 Attention | 🔴 Intervention requise
```

---

## 🔧 Fonctionnalités Avancées

### 1. 🎛️ Interactions
- **Tri dynamique** par colonne (croissant/décroissant)
- **Filtrage en temps réel** par type d'opérateur (CONFIRMATION, LOGISTIQUE, PREPARATION)
- **Recherche instantanée** par nom d'opérateur
- **Export Excel** complet avec métriques
- **Drill-down** : clic sur opérateur → détail des commandes
- **Comparaison période** : vs hier, vs semaine dernière

### 2. 📊 Visualisations
- **Graphique en barres horizontales** : Top 10 opérateurs par taux de confirmation
- **Graphique en secteurs** : Répartition des confirmations par type d'opérateur
- **Sparklines** : Évolution individuelle sur la période sélectionnée
- **Heatmap** : Performance croisée (opérateurs × métriques)
- **Gauge charts** : Progression vers objectifs individuels

### 3. 🚨 Alertes & Indicateurs
| Indicateur | Condition | Action |
|------------|-----------|--------|
| 🔴 **Critique** | Performance < 50% objectif | Notification immédiate superviseur |
| 🟡 **Attention** | Performance 50-80% objectif | Suivi renforcé |
| 🟢 **Normal** | Performance 80-100% objectif | Monitoring standard |
| ⭐ **Excellence** | Performance > 100% objectif | Reconnaissance/bonus |

### 4. 📱 Responsive Design
- **Desktop** : Vue complète avec toutes les sections
- **Tablet** : Sections collapsibles, tableaux avec scroll horizontal
- **Mobile** : Cards individuelles, métriques empilées

---

## 🛠️ Architecture Technique

### 1. Structure Backend

#### Nouvelle Vue Django
```python
@login_required  
def performance_operateurs_data(request):
    """
    API pour les données de performance des opérateurs
    Filtres: period, operator_type, operator_id
    """
    # Gestion des filtres temporels
    # Agrégation par opérateur avec jointures optimisées
    # Calculs des métriques avancées
    # Classification par type d'opérateur
    # Retour JSON structuré avec pagination
```

#### Modèles Utilisés
```python
# Principaux modèles impliqués
- Operateur (parametre.models)
- Commande (commande.models) 
- Operation (commande.models)
- EtatCommande (commande.models)
- Panier (commande.models)
```

### 2. Structure Frontend

#### Template Principal
```
templates/kpis/tabs/performance_operateurs.html
├── Section filtres et contrôles
├── Section métriques générales (6 cards)
├── Section performance par type (accordéon)
├── Section tableau détaillé (DataTable)
├── Modales pour drill-down
└── Scripts JavaScript pour interactions
```

#### Composants JavaScript
```javascript
// Fonctions principales
- loadPerformanceData(filters)
- renderGeneralMetrics(data)
- renderOperatorsByType(data)
- renderDetailTable(data)
- exportToExcel()
- showOperatorDetails(operatorId)
```

### 3. API Endpoints
```python
# Nouvelles routes à ajouter
path('api/performance-operateurs/', views.performance_operateurs_data, name='performance_operateurs_data'),
path('api/operateur-details/<int:operator_id>/', views.operateur_details, name='operateur_details'),
path('api/export-performance/', views.export_performance_excel, name='export_performance'),
```

---

## 📈 Métriques Business - Formules Détaillées

### 1. Actions pour Confirmation
```sql
SELECT 
    operateur_id,
    COUNT(operations.id) as total_actions,
    COUNT(DISTINCT commandes.id WHERE etat='confirmee') as confirmations,
    ROUND(COUNT(operations.id) / NULLIF(COUNT(DISTINCT commandes.id WHERE etat='confirmee'), 0), 2) as actions_par_confirmation
FROM operations
JOIN commandes ON operations.commande_id = commandes.id
GROUP BY operateur_id
```

### 2. Taux de Confirmation
```sql
SELECT 
    operateur_id,
    COUNT(CASE WHEN etat='affectee' THEN 1 END) as affectees,
    COUNT(CASE WHEN etat='confirmee' THEN 1 END) as confirmees,
    ROUND(
        COUNT(CASE WHEN etat='confirmee' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(CASE WHEN etat='affectee' THEN 1 END), 0), 
        2
    ) as taux_confirmation
FROM commandes
JOIN etats_commande ON commandes.id = etats_commande.commande_id
GROUP BY operateur_id
```

### 3. Performance Relative
```sql
WITH moyennes AS (
    SELECT AVG(taux_confirmation) as moyenne_equipe
    FROM (-- sous-requête des taux individuels)
)
SELECT 
    operateur_id,
    taux_confirmation,
    ROUND((taux_confirmation / moyenne_equipe) * 100, 1) as performance_relative
FROM operateurs_performance, moyennes
```

---

## 🎯 Roadmap d'Implémentation

### Phase 1 : Fondations (Jour 1-2)
- [ ] Ajout de l'onglet dans la navigation
- [ ] Création de la vue Django de base
- [ ] Template HTML avec structure principale
- [ ] Filtres temporels fonctionnels
- [ ] Tests de base

### Phase 2 : Métriques Core (Jour 3-4)
- [ ] Calcul des métriques principales
- [ ] Section vue générale (6 cards)
- [ ] Identification des types d'opérateurs
- [ ] Tests unitaires des calculs

### Phase 3 : Interface Avancée (Jour 5-6)
- [ ] Section performance par type (accordéon)
- [ ] Tableau détaillé avec tri/recherche
- [ ] Responsive design
- [ ] Tests d'intégration

### Phase 4 : Fonctionnalités Premium (Jour 7-8)
- [ ] Visualisations (graphiques)
- [ ] Export Excel avancé
- [ ] Système d'alertes
- [ ] Drill-down vers détails

### Phase 5 : Optimisations (Jour 9-10)
- [ ] Performance queries
- [ ] Cache intelligent
- [ ] Tests de charge
- [ ] Documentation utilisateur

---

## 🧪 Tests & Validation

### Tests Unitaires
```python
# Tests des calculs de métriques
test_actions_par_confirmation()
test_taux_confirmation()
test_panier_moyen()
test_classification_operateurs()
```

### Tests d'Intégration
```python
# Tests des filtres
test_filtre_periode()
test_filtre_type_operateur()
test_recherche_operateur()
```

### Tests de Performance
```python
# Tests de charge
test_performance_100_operateurs()
test_performance_1000_commandes()
test_cache_efficiency()
```

---

## 📚 Documentation Utilisateur

### Guide d'Utilisation
1. **Navigation** : Accès via onglet "Performance Opérateurs"
2. **Filtres** : Sélection de période et type d'opérateur
3. **Lecture des métriques** : Interprétation des indicateurs
4. **Actions** : Export, drill-down, comparaisons
5. **Alertes** : Compréhension des seuils et actions

### FAQ Prévues
- Comment interpréter le "nombre d'actions pour confirmation" ?
- Pourquoi mon taux de confirmation est-il bas ?
- Comment améliorer mon panier moyen ?
- Que signifient les couleurs dans le tableau ?

---

## 🔐 Sécurité & Permissions

### Niveaux d'Accès
- **Opérateur** : Voir ses propres performances uniquement
- **Superviseur** : Voir son équipe + métriques générales
- **Manager** : Accès complet à tous les opérateurs
- **Admin** : Accès total + configuration des seuils

### Données Sensibles
- Anonymisation partielle des noms (initiales)
- Logs d'accès aux données de performance
- Respect RGPD pour données personnelles

---

*Document créé le 2 juillet 2025 - Version 1.0*  
*Prêt pour implémentation* 🚀
