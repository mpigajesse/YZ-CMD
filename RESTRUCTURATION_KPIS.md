# Restructuration de la gestion des KPIs

## Nouvelle organisation

### URLs et vues

- **Dashboard principal** : `/kpis/` → `views.dashboard_home` → `templates/kpis/dashboard.html`
- **Configuration des paramètres** : `/kpis/configurations/` → `views.configurations` → `templates/kpis/configurations.html`
- **Documentation** : `/kpis/documentation/` → `views.documentation` → `templates/kpis/documentation.html` (future)

### APIs (inchangées)

- `/kpis/api/vue-generale/` → Données Vue Générale
- `/kpis/api/ventes/` → Données Ventes
- `/kpis/api/evolution-ca/` → Données Evolution CA
- `/kpis/api/top-modeles/` → Données Top Modèles
- `/kpis/api/performance-regions/` → Données Performance Régions
- `/kpis/api/clients/` → Données Clients
- `/kpis/api/configurations/` → Récupération des configurations
- `/kpis/api/configurations/save/` → Sauvegarde des configurations
- `/kpis/api/configurations/reset/` → Reset des configurations

## Changements apportés

### 1. Séparation claire des responsabilités

- **Configuration** (`/configurations/`) : Gestion des paramètres et seuils uniquement
- **Documentation** (`/documentation/`) : Guide d'utilisation (à développer)

### 2. Navigation cohérente

- Liens mis à jour dans `dashboard.html` et `home.html`
- Bouton "Documentation" ajouté dans la page de configuration

### 3. Structure des fichiers

```
kpis/
├── views.py
│   ├── dashboard_home()     # Dashboard principal
│   ├── configurations()    # Page de configuration NOUVELLE
│   └── documentation()     # Page de documentation (future)
├── urls.py
│   ├── /                   # Dashboard
│   ├── /configurations/    # Configuration NOUVELLE
│   └── /documentation/     # Documentation
└── templates/kpis/
    ├── dashboard.html      # Dashboard principal
    ├── configurations.html # Configuration NOUVEAU
    └── documentation.html  # Documentation (à nettoyer)
```

## Todo

1. ✅ Créer la route `/configurations/`
2. ✅ Créer la vue `configurations()`
3. ✅ Créer le template `configurations.html`
4. ✅ Mettre à jour les liens dans dashboard et home
5. 🔄 Nettoyer `documentation.html` pour n'avoir que la documentation
6. 🔄 Organiser le contenu de documentation (guide utilisateur)

## Avantages

- **Clarté** : Distinction nette entre configuration et documentation
- **Maintenabilité** : Chaque page a une responsabilité unique
- **Navigation** : URLs cohérentes et intuitives
- **Extensibilité** : Facilite l'ajout de nouvelles fonctionnalités
