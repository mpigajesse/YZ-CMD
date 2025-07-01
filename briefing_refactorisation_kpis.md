# Briefing : Refactorisation KPIs Dashboard - Remplacement Tab "Stocks" par "Vue Quantitative"

## 📋 OBJECTIF

Supprimer l'onglet "Stocks" du tableau de bord KPIs et le remplacer par un nouvel onglet "Vue Quantitative" contenant une section "Suivi de l'état des commandes" qui affiche les compteurs pour chaque état de commande.

## 🎯 ÉLÉMENTS IDENTIFIÉS

### 1. Structure Actuelle des Onglets
**Fichier :** `/workspaces/YZ-CMD/templates/kpis/components/tabs_navigation.html`

**Onglets actuels :**
- Vue Générale (onglet par défaut)
- Ventes
- Clients
- Opérations
- **Stocks** ← À SUPPRIMER

### 2. Modèles d'État des Commandes
**Fichiers :** `/workspaces/YZ-CMD/commande/models.py`

**Modèles concernés :**
- `EnumEtatCmd` : Définitions des états de commande
- `EtatCommande` : Historique/suivi des états par commande

**États disponibles dans STATUS_CHOICES :**
- `non_affectee` : Non affectée
- `affectee` : Affectée  
- `en_cours_confirmation` : En cours de confirmation
- `confirmee` : Confirmée
- `erronnee` : Erronée
- `doublon` : Doublon

**États DELIVERY_STATUS_CHOICES :**
- `en_preparation` : En préparation
- `en_livraison` : En livraison
- `livree` : Livrée
- `retournee` : Retournée

### 3. États Requis pour "Suivi de l'état des commandes"
D'après les spécifications, nous devons afficher les compteurs pour :
1. **reçue** (probablement l'état initial)
2. **affectée** → `affectee`
3. **non affectée** → `non_affectee`
4. **erronnee** → `erronnee`
5. **doublon** → `doublon`
6. **en cours confirmation** → `en_cours_confirmation`
7. **confirmé** → `confirmee`
8. **en cours de préparation** → `en_preparation`
9. **préparé** (état intermédiaire à identifier)
10. **en cours de livraison** → `en_livraison`
11. **livré** → `livree`
12. **retourné** → `retournee`

## 🔧 TÂCHES À RÉALISER

### ÉTAPE 1 : Suppression de l'onglet "Stocks"

**Fichier à modifier :** `/workspaces/YZ-CMD/templates/kpis/components/tabs_navigation.html`

**Actions :**
1. Supprimer le bouton "Stocks" (lignes ~68-71)
2. Supprimer le div de contenu "chaussures-stocks-content" (lignes ~85-87)
3. Supprimer l'include du template stocks

### ÉTAPE 2 : Ajout de l'onglet "Vue Quantitative"

**Fichier à modifier :** `/workspaces/YZ-CMD/templates/kpis/components/tabs_navigation.html`

**Actions :**
1. Ajouter le bouton "Vue Quantitative" avec icône appropriée
2. Ajouter le div de contenu correspondant
3. Créer l'include vers le nouveau template

### ÉTAPE 3 : Création de la vue pour les compteurs d'états

**Fichier à modifier :** `/workspaces/YZ-CMD/kpis/views.py`

**Nouvelle fonction :**
```python
@login_required
def vue_quantitative_data(request):
    """API pour les données de l'onglet Vue Quantitative"""
    # Calculer les compteurs pour chaque état de commande
    # Retourner un JSON avec les données
```

**Logique requise :**
- Compter les commandes par état actuel (dernier état non terminé)
- Gérer les états multiples (statut + livraison)
- Retourner un dictionnaire avec les compteurs

### ÉTAPE 4 : Mise à jour des URLs

**Fichier à modifier :** `/workspaces/YZ-CMD/kpis/urls.py`

**Action :**
```python
path('api/vue-quantitative/', views.vue_quantitative_data, name='vue_quantitative_data'),
```

### ÉTAPE 5 : Création du template Vue Quantitative

**Nouveau fichier :** `/workspaces/YZ-CMD/templates/kpis/tabs/vue_quantitative.html`

**Contenu requis :**
- Section "Suivi de l'état des commandes"
- Affichage des compteurs pour chaque état
- Design cohérent avec les autres onglets
- Appel AJAX vers la nouvelle API

### ÉTAPE 6 : Nettoyage des fichiers Stocks

**Fichiers à supprimer/vérifier :**
- `/workspaces/YZ-CMD/templates/kpis/tabs/chaussures_stocks.html`
- Vues liées aux stocks dans `kpis/views.py` (si existantes)
- URLs liées aux stocks dans `kpis/urls.py` (si existantes)

## 🎨 SPÉCIFICATIONS DESIGN

### Icône pour "Vue Quantitative"
Suggestions : `fas fa-chart-bar`, `fas fa-analytics`, `fas fa-chart-column`

### Structure de la section "Suivi de l'état des commandes"
- Titre de section clairement identifié
- Grille de cartes/badges pour chaque état
- Codes couleur distinctifs pour chaque état
- Nombres bien visibles
- Animation/hover effects cohérents

### Disposition suggérée
```html
<div class="bg-white rounded-xl shadow-lg p-6">
  <h3 class="text-lg font-semibold mb-4">Suivi de l'état des commandes</h3>
  <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
    <!-- Cartes d'états -->
  </div>
</div>
```

## 📋 STRUCTURE DE DONNÉES API

### Response de `vue_quantitative_data` :
```json
{
  "success": true,
  "data": {
    "etats_commandes": {
      "recue": 45,
      "affectee": 23,
      "non_affectee": 12,
      "erronnee": 3,
      "doublon": 1,
      "en_cours_confirmation": 8,
      "confirmee": 15,
      "en_cours_preparation": 7,
      "preparee": 5,
      "en_cours_livraison": 18,
      "livree": 125,
      "retournee": 2
    },
    "total_commandes": 264,
    "derniere_maj": "2024-01-15T14:30:00Z"
  }
}
```

## 🔍 POINTS D'ATTENTION

1. **Gestion des états multiples** : Une commande peut avoir plusieurs états actifs simultanément
2. **Performance** : Optimiser les requêtes pour éviter les N+1 queries
3. **Consistance UI** : Maintenir le style et les animations existantes
4. **Accessibilité** : Conserver les attributs ARIA et la navigation clavier
5. **Tests** : Vérifier que la suppression de l'onglet Stocks n'impacte pas d'autres fonctionnalités

## 🚀 ORDRE D'EXÉCUTION RECOMMANDÉ

1. Créer la nouvelle vue et l'URL pour les données quantitatives
2. Créer le template Vue Quantitative
3. Modifier la navigation pour remplacer Stocks par Vue Quantitative
4. Tester le fonctionnement complet
5. Nettoyer les fichiers/code liés aux stocks
6. Validation finale et tests d'intégration

---

**Note :** Ce briefing servira de référence pour l'implémentation complète de la refactorisation.
