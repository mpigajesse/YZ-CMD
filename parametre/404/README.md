# Pages 404 Personnalisées YZ-CMD

Ce module fournit des pages d'erreur 404 personnalisées pour chaque interface de l'application YZ-CMD.

## Structure

```
parametre/404/
├── __init__.py
├── utils.py                 # Utilitaires de détection et redirection
├── README.md               # Ce fichier
├── admin/
│   ├── __init__.py
│   ├── views.py           # Vue 404 pour l'interface admin
│   └── urls.py            # URLs pour l'interface admin
├── confirmation/
│   ├── __init__.py
│   ├── views.py           # Vue 404 pour l'interface confirmation
│   └── urls.py            # URLs pour l'interface confirmation
├── preparation/
│   ├── __init__.py
│   ├── views.py           # Vue 404 pour l'interface préparation
│   └── urls.py            # URLs pour l'interface préparation
└── logistique/
    ├── __init__.py
    ├── views.py           # Vue 404 pour l'interface logistique
    └── urls.py            # URLs pour l'interface logistique
```

## Templates

```
templates/parametre/404/
├── admin/404.html          # Template 404 admin (thème gris)
├── confirmation/404.html   # Template 404 confirmation (thème brun)
├── preparation/404.html    # Template 404 préparation (thème brun foncé)
└── logistique/404.html     # Template 404 logistique (thème bleu marine)
```

## Utilisation

### 1. Accès Direct aux Pages 404

- **Admin** : `http://localhost:8000/404/admin/404/`
- **Confirmation** : `http://localhost:8000/404/confirmation/404/`
- **Préparation** : `http://localhost:8000/404/preparation/404/`
- **Logistique** : `http://localhost:8000/404/logistique/404/`

### 2. Utilisation dans les Vues

```python
from parametre.404.utils import get_custom_404_view, redirect_to_interface_404

# Retourner une page 404 adaptée à l'interface
def ma_vue(request):
    if not objet_existe:
        return get_custom_404_view(request)
    
    # Ou rediriger vers la page 404 appropriée
    if erreur_critique:
        return redirect_to_interface_404(request, 'confirmation')
```

### 3. Détection Automatique d'Interface

```python
from parametre.404.utils import detect_interface_from_path

interface = detect_interface_from_path(request.path)
# Retourne: 'admin', 'confirmation', 'preparation', ou 'logistique'
```

## Thèmes par Interface

### Admin (Gris)
- Couleur principale : `#1f2937`
- Icône : `fas fa-cogs`
- Gradient : Gris foncé vers gris moyen

### Confirmation (Brun)
- Couleur principale : `#4B352A`
- Icône : `fas fa-clipboard-check`
- Gradient : Brun vers brun clair

### Préparation (Brun Foncé)
- Couleur principale : `#361f27`
- Icône : `fas fa-boxes`
- Gradient : Brun très foncé vers brun moyen

### Logistique (Bleu Marine)
- Couleur principale : `#0B1D51`
- Icône : `fas fa-truck`
- Gradient : Bleu marine vers bleu moyen

## Fonctionnalités

- ✅ **Thèmes cohérents** avec chaque interface
- ✅ **Animations** d'icônes (bounce)
- ✅ **Boutons d'action** personnalisés
- ✅ **Messages contextuels** par interface
- ✅ **Responsive design** pour tous les écrans
- ✅ **Navigation** vers tableau de bord ou page précédente

## Configuration

Les URLs sont automatiquement incluses dans `config/urls.py` :

```python
# Pages 404 personnalisées par interface
path('404/admin/', include('parametre.404.admin.urls')),
path('404/confirmation/', include('parametre.404.confirmation.urls')),
path('404/preparation/', include('parametre.404.preparation.urls')),
path('404/logistique/', include('parametre.404.logistique.urls')),
```
