# 🏗️ Architecture Visuelle - Organisation des Projets YZ-CMD

## 📁 Structure Complète du Dossier YZ-CMD

```
YZ-CMD/                                    # Dossier racine principal
├── 📋 README.md                          # Documentation générale du projet
├── 🚀 ouverture-projet.md                # Document d'ouverture multi-tenants
├── 🏗️ architecture-visuelle.md           # Ce fichier
│
├── 🔧 YZ-PLATFORM/                       # Plateforme principale multi-tenants
│   ├── 📁 config/                        # Configuration globale
│   │   ├── 📄 __init__.py
│   │   ├── 📄 settings/
│   │   │   ├── 📄 base.py               # Configuration de base
│   │   │   ├── 📄 development.py        # Développement
│   │   │   ├── 📄 production.py         # Production
│   │   │   └── 📄 multi_tenant.py       # Configuration multi-tenants
│   │   ├── 📄 urls.py                   # URLs principales
│   │   ├── 📄 wsgi.py                   # Configuration WSGI
│   │   └── 📄 asgi.py                   # Configuration ASGI
│   │
│   ├── 🧩 core/                          # Services centraux partagés
│   │   ├── 📁 tenant_management/        # Gestion des entreprises
│   │   │   ├── 📄 models.py             # Modèles Tenant
│   │   │   ├── 📄 views.py              # Vues de gestion
│   │   │   ├── 📄 admin.py              # Interface admin
│   │   │   └── 📄 urls.py               # URLs spécifiques
│   │   │
│   │   ├── 📁 user_management/          # Gestion des utilisateurs
│   │   │   ├── 📄 models.py             # Profils utilisateurs
│   │   │   ├── 📄 views.py              # Vues utilisateurs
│   │   │   ├── 📄 forms.py              # Formulaires
│   │   │   └── 📄 permissions.py        # Système de permissions
│   │   │
│   │   ├── 📁 authentication/            # Authentification
│   │   │   ├── 📄 models.py             # Modèles d'auth
│   │   │   ├── 📄 views.py              # Vues d'auth
│   │   │   ├── 📄 services.py           # Services d'auth
│   │   │   └── 📄 middleware.py         # Middleware d'auth
│   │   │
│   │   ├── 📁 billing/                   # Facturation et abonnements
│   │   │   ├── 📄 models.py             # Plans, factures, paiements
│   │   │   ├── 📄 views.py              # Vues de facturation
│   │   │   ├── 📄 services.py           # Services de facturation
│   │   │   └── 📄 stripe_integration.py # Intégration Stripe
│   │   │
│   │   ├── 📁 communication/             # Communication
│   │   │   ├── 📄 email/                # Service emails
│   │   │   ├── 📄 sms/                  # Service SMS
│   │   │   ├── 📄 notifications/        # Notifications push
│   │   │   └── 📄 webhooks/             # Webhooks externes
│   │   │
│   │   ├── 📁 analytics/                 # Analytics et reporting
│   │   │   ├── 📄 models.py             # Modèles analytics
│   │   │   ├── 📄 views.py              # Vues de reporting
│   │   │   ├── 📄 charts.py             # Génération de graphiques
│   │   │   └── 📄 exports.py            # Export de données
│   │   │
│   │   ├── 📁 configuration/             # Configuration dynamique
│   │   │   ├── 📄 models.py             # Configuration par tenant
│   │   │   ├── 📄 views.py              # Interface de config
│   │   │   └── 📄 services.py           # Services de config
│   │   │
│   │   └── 📁 shared/                    # Utilitaires partagés
│   │       ├── 📄 constants.py          # Constantes globales
│   │       ├── 📄 utils.py              # Fonctions utilitaires
│   │       ├── 📄 decorators.py         # Décorateurs personnalisés
│   │       └── 📄 exceptions.py         # Exceptions personnalisées
│   │
│   ├── 🌐 api/                           # API Gateway
│   │   ├── 📁 v1/                       # Version 1 de l'API
│   │   │   ├── 📄 urls.py               # Routes API v1
│   │   │   ├── 📄 views.py              # Vues API
│   │   │   ├── 📄 serializers.py        # Sérialiseurs
│   │   │   └── 📄 permissions.py        # Permissions API
│   │   │
│   │   ├── 📁 middleware/                # Middleware API
│   │   │   ├── 📄 tenant_middleware.py  # Identification tenant
│   │   │   ├── 📄 rate_limiting.py      # Limitation de débit
│   │   │   ├── 📄 authentication.py     # Auth API
│   │   │   └── 📄 cors.py               # Gestion CORS
│   │   │
│   │   ├── 📁 documentation/             # Documentation API
│   │   │   ├── 📄 swagger.py            # Configuration Swagger
│   │   │   ├── 📄 redoc.py              # Configuration ReDoc
│   │   │   └── 📄 examples.py           # Exemples d'utilisation
│   │   │
│   │   └── 📄 urls.py                   # URLs API principales
│   │
│   ├── 🎨 frontend/                      # Interface utilisateur
│   │   ├── 📁 components/                # Composants réutilisables
│   │   │   ├── 📁 common/                # Composants communs
│   │   │   │   ├── 📄 Header.jsx        # En-tête
│   │   │   │   ├── 📄 Sidebar.jsx       # Barre latérale
│   │   │   │   ├── 📄 Footer.jsx        # Pied de page
│   │   │   │   ├── 📄 Modal.jsx         # Modales
│   │   │   │   └── 📄 Table.jsx         # Tableaux
│   │   │   │
│   │   │   ├── 📁 forms/                 # Composants de formulaires
│   │   │   │   ├── 📄 Input.jsx         # Champs de saisie
│   │   │   │   ├── 📄 Select.jsx        # Sélections
│   │   │   │   ├── 📄 DatePicker.jsx    # Sélecteur de date
│   │   │   │   └── 📄 FileUpload.jsx    # Upload de fichiers
│   │   │   │
│   │   │   └── 📁 charts/                # Composants de graphiques
│   │   │       ├── 📄 LineChart.jsx      # Graphique linéaire
│   │   │       ├── 📄 BarChart.jsx       # Graphique en barres
│   │   │       ├── 📄 PieChart.jsx       # Graphique circulaire
│   │   │       └── 📄 Dashboard.jsx      # Tableau de bord
│   │   │
│   │   ├── 📁 themes/                    # Thèmes par entreprise
│   │   │   ├── 📁 default/               # Thème par défaut
│   │   │   │   ├── 📄 colors.css         # Couleurs
│   │   │   │   ├── 📄 typography.css     # Typographie
│   │   │   │   └── 📄 components.css     # Styles des composants
│   │   │   │
│   │   │   ├── 📁 yoozak/                # Thème Yoozak
│   │   │   │   ├── 📄 colors.css         # Couleurs Yoozak
│   │   │   │   ├── 📄 logo.svg           # Logo Yoozak
│   │   │   │   └── 📄 favicon.ico        # Favicon Yoozak
│   │   │   │
│   │   │   ├── 📁 textile/               # Thème textile
│   │   │   ├── 📁 pharmacie/             # Thème pharmacie
│   │   │   ├── 📁 restaurant/            # Thème restaurant
│   │   │   └── 📁 autres/                # Autres thèmes
│   │   │
│   │   ├── 📁 pages/                     # Pages principales
│   │   │   ├── 📄 Dashboard.jsx          # Tableau de bord
│   │   │   ├── 📄 Login.jsx              # Page de connexion
│   │   │   ├── 📄 Settings.jsx           # Paramètres
│   │   │   └── 📄 Profile.jsx            # Profil utilisateur
│   │   │
│   │   └── 📄 App.jsx                    # Application principale
│   │
│   ├── 📊 management/                     # Commandes de gestion
│   │   ├── 📄 create_tenant.py           # Créer une entreprise
│   │   ├── 📄 migrate_tenant.py          # Migrer une entreprise
│   │   ├── 📄 backup_tenant.py           # Sauvegarder une entreprise
│   │   ├── 📄 setup_demo.py              # Configurer une démo
│   │   └── 📄 health_check.py            # Vérification de santé
│   │
│   ├── 🧪 tests/                          # Tests de la plateforme
│   │   ├── 📁 unit/                      # Tests unitaires
│   │   ├── 📁 integration/               # Tests d'intégration
│   │   ├── 📁 e2e/                       # Tests end-to-end
│   │   └── 📄 conftest.py                # Configuration des tests
│   │
│   ├── 📄 manage.py                       # Gestion Django
│   ├── 📄 requirements.txt                # Dépendances Python
│   ├── 📄 package.json                    # Dépendances Node.js
│   ├── 📄 docker-compose.yml             # Configuration Docker
│   └── 📄 README.md                       # Documentation plateforme
│
├── 👟 YZ-CMD-YOOZAK/                     # Projet Yoozak (cas de base - EXISTANT)
│   ├── 📁 config/                        # Configuration spécifique
│   │   ├── 📄 __init__.py
│   │   ├── 📄 settings.py                # Settings Yoozak
│   │   ├── 📄 urls.py                    # URLs Yoozak
│   │   └── 📄 wsgi.py                    # WSGI Yoozak
│   │
│   ├── 📁 apps/                           # Applications métier Yoozak
│   │   ├── 📁 commande/                  # Gestion des commandes
│   │   │   ├── 📄 models.py              # Modèles commandes
│   │   │   ├── 📄 views.py               # Vues commandes
│   │   │   ├── 📄 admin.py               # Admin commandes
│   │   │   ├── 📄 urls.py                # URLs commandes
│   │   │   ├── 📄 forms.py               # Formulaires commandes
│   │   │   └── 📄 tests.py               # Tests commandes
│   │   │
│   │   ├── 📁 article/                   # Gestion des articles
│   │   │   ├── 📄 models.py              # Modèles articles
│   │   │   ├── 📄 views.py               # Vues articles
│   │   │   ├── 📄 admin.py               # Admin articles
│   │   │   ├── 📄 urls.py                # URLs articles
│   │   │   ├── 📄 forms.py               # Formulaires articles
│   │   │   └── 📄 tests.py               # Tests articles
│   │   │
│   │   ├── 📁 client/                    # Gestion des clients
│   │   ├── 📁 livraison/                 # Gestion des livraisons
│   │   ├── 📁 operatConfirme/            # Opérateurs de confirmation
│   │   ├── 📁 operatLogistic/            # Opérateurs logistiques
│   │   ├── 📁 Prepacommande/             # Opérateurs de préparation
│   │   ├── 📁 synchronisation/           # Synchronisation Google Sheets
│   │   ├── 📁 kpis/                      # Tableaux de bord
│   │   └── 📁 notifications/             # Notifications
│   │
│   ├── 📁 templates/                      # Templates Django Yoozak (EXISTANTS)
│   │   ├── 📁 base/                       # Templates de base
│   │   ├── 📁 commande/                   # Templates commandes
│   │   ├── 📁 article/                    # Templates articles
│   │   ├── 📁 client/                     # Templates clients
│   │   └── 📁 autres/                     # Autres templates
│   │
│   ├── 📁 static/                         # Assets statiques Django Yoozak (EXISTANTS)
│   │   ├── 📁 css/                        # Styles CSS
│   │   ├── 📁 js/                         # JavaScript
│   │   ├── 📁 images/                     # Images
│   │   └── 📁 fonts/                      # Polices
│   │
│   ├── 📁 migrations/                     # Migrations Yoozak
│   ├── 📄 manage.py                       # Gestion Django Yoozak
│   ├── 📄 requirements.txt                # Dépendances Python Yoozak
│   └── 📄 README.md                       # Documentation Yoozak
│
├── 🧵 YZ-TEXTILE-ENTREPRISE-A/            # Projet E-commerce Textile
│   ├── 📁 config/                         # Configuration textile
│   ├── 📁 apps/                           # Applications métier
│   │   ├── 📁 produit/                    # Gestion des produits textiles
│   │   ├── 📁 collection/                 # Gestion des collections
│   │   ├── 📁 taille/                     # Système de tailles
│   │   ├── 📁 commande/                   # Commandes e-commerce
│   │   ├── 📁 livraison/                  # Livraison textile
│   │   └── 📁 retour/                     # Gestion des retours
│   ├── 🎨 frontend/                       # Frontend spécifique Textile
│   │   ├── 📁 src/                        # Code source React/Vue
│   │   │   ├── 📁 components/             # Composants textile
│   │   │   │   ├── 📁 produit/            # Composants produits
│   │   │   │   ├── 📁 collection/         # Composants collections
│   │   │   │   ├── 📁 taille/             # Composants tailles
│   │   │   │   ├── 📁 ecommerce/          # Composants e-commerce
│   │   │   │   └── 📁 common/             # Composants communs
│   │   │   ├── 📁 pages/                  # Pages de l'application
│   │   │   ├── 📁 hooks/                  # Hooks personnalisés
│   │   │   ├── 📁 utils/                  # Utilitaires
│   │   │   ├── 📁 styles/                 # Styles SCSS/CSS
│   │   │   ├── 📁 assets/                 # Images, icônes, polices
│   │   │   ├── 📄 App.jsx                 # Application principale
│   │   │   ├── 📄 index.jsx               # Point d'entrée
│   │   │   └── 📄 routes.jsx              # Configuration des routes
│   │   ├── 📁 public/                     # Fichiers publics
│   │   │   ├── 📄 index.html              # Template HTML
│   │   │   ├── 📄 favicon.ico             # Favicon textile
│   │   │   └── 📄 manifest.json           # Manifest PWA
│   │   ├── 📄 package.json                # Dépendances frontend
│   │   ├── 📄 webpack.config.js           # Configuration Webpack
│   │   ├── 📄 tailwind.config.js          # Configuration Tailwind
│   │   ├── 📄 .babelrc                    # Configuration Babel
│   │   └── 📄 README.md                   # Documentation frontend
│   ├── 📁 templates/                      # Templates Django textile
│   ├── 📁 static/                         # Assets statiques Django textile
│   └── 📄 README.md                       # Documentation textile
│
├── 🏭 YZ-LOGISTIQUE-ENTREPRISE-B/         # Projet Logistique Industrielle
│   ├── 📁 config/                         # Configuration logistique
│   ├── 📁 apps/                           # Applications métier
│   │   ├── 📁 entrepot/                   # Gestion des entrepôts
│   │   ├── 📁 zone/                       # Zones de stockage
│   │   ├── 📁 mouvement/                  # Mouvements de stock
│   │   ├── 📁 transport/                  # Gestion des transports
│   │   ├── 📁 fournisseur/                # Gestion des fournisseurs
│   │   └── 📁 maintenance/                # Maintenance des équipements
│   ├── 🎨 frontend/                       # Frontend spécifique Logistique
│   │   ├── 📁 src/                        # Code source React/Vue
│   │   │   ├── 📁 components/             # Composants logistique
│   │   │   │   ├── 📁 entrepot/           # Composants entrepôts
│   │   │   │   ├── 📁 zone/               # Composants zones
│   │   │   │   ├── 📁 mouvement/          # Composants mouvements
│   │   │   │   ├── 📁 transport/          # Composants transport
│   │   │   │   └── 📁 common/             # Composants communs
│   │   │   ├── 📁 pages/                  # Pages de l'application
│   │   │   ├── 📁 hooks/                  # Hooks personnalisés
│   │   │   ├── 📁 utils/                  # Utilitaires
│   │   │   ├── 📁 styles/                 # Styles SCSS/CSS
│   │   │   ├── 📁 assets/                 # Images, icônes, polices
│   │   │   ├── 📄 App.jsx                 # Application principale
│   │   │   ├── 📄 index.jsx               # Point d'entrée
│   │   │   └── 📄 routes.jsx              # Configuration des routes
│   │   ├── 📁 public/                     # Fichiers publics
│   │   │   ├── 📄 index.html              # Template HTML
│   │   │   ├── 📄 favicon.ico             # Favicon logistique
│   │   │   └── 📄 manifest.json           # Manifest PWA
│   │   ├── 📄 package.json                # Dépendances frontend
│   │   ├── 📄 webpack.config.js           # Configuration Webpack
│   │   ├── 📄 tailwind.config.js          # Configuration Tailwind
│   │   ├── 📄 .babelrc                    # Configuration Babel
│   │   └── 📄 README.md                   # Documentation frontend
│   ├── 📁 templates/                      # Templates Django logistique
│   ├── 📁 static/                         # Assets statiques Django logistique
│   └── 📄 README.md                       # Documentation logistique
│
├── 🍽️ YZ-RESTAURANT-ENTREPRISE-C/         # Projet Restauration et Livraison
│   ├── 📁 config/                         # Configuration restaurant
│   ├── 📁 apps/                           # Applications métier
│   │   ├── 📁 menu/                       # Gestion des menus
│   │   ├── 📁 ingredient/                 # Gestion des ingrédients
│   │   ├── 📁 commande/                   # Commandes en ligne
│   │   ├── 📁 livraison/                  # Livraison à domicile
│   │   ├── 📁 livreur/                    # Gestion des livreurs
│   │   ├── 📁 horaire/                    # Horaires d'ouverture
│   │   └── 📁 promotion/                  # Promotions et offres
│   ├── 🎨 frontend/                       # Frontend spécifique Restaurant
│   │   ├── 📁 src/                        # Code source React/Vue
│   │   │   ├── 📁 components/             # Composants restaurant
│   │   │   │   ├── 📁 menu/               # Composants menus
│   │   │   │   ├── 📁 ingredient/         # Composants ingrédients
│   │   │   │   ├── 📁 commande/           # Composants commandes
│   │   │   │   ├── 📁 livraison/          # Composants livraison
│   │   │   │   └── 📁 common/             # Composants communs
│   │   │   ├── 📁 pages/                  # Pages de l'application
│   │   │   ├── 📁 hooks/                  # Hooks personnalisés
│   │   │   ├── 📁 utils/                  # Utilitaires
│   │   │   ├── 📁 styles/                 # Styles SCSS/CSS
│   │   │   ├── 📁 assets/                 # Images, icônes, polices
│   │   │   ├── 📄 App.jsx                 # Application principale
│   │   │   ├── 📄 index.jsx               # Point d'entrée
│   │   │   └── 📄 routes.jsx              # Configuration des routes
│   │   ├── 📁 public/                     # Fichiers publics
│   │   │   ├── 📄 index.html              # Template HTML
│   │   │   ├── 📄 favicon.ico             # Favicon restaurant
│   │   │   └── 📄 manifest.json           # Manifest PWA
│   │   ├── 📄 package.json                # Dépendances frontend
│   │   ├── 📄 webpack.config.js           # Configuration Webpack
│   │   ├── 📄 tailwind.config.js          # Configuration Tailwind
│   │   ├── 📄 .babelrc                    # Configuration Babel
│   │   └── 📄 README.md                   # Documentation frontend
│   ├── 📁 templates/                      # Templates Django restaurant
│   ├── 📁 static/                         # Assets statiques Django restaurant
│   └── 📄 README.md                       # Documentation restaurant
│
├── 💊 YZ-PHARMACIE-ENTREPRISE-D/          # Projet Pharmacie et Parapharmacie
│   ├── 📁 config/                         # Configuration pharmacie
│   ├── 📁 apps/                           # Applications métier
│   │   ├── 📁 medicament/                 # Gestion des médicaments
│   │   ├── 📁 ordonnance/                 # Gestion des ordonnances
│   │   ├── 📁 stock_pharma/               # Stock pharmaceutique
│   │   ├── 📁 commande/                   # Commandes en ligne
│   │   ├── 📁 livraison/                  # Livraison express
│   │   ├── 📁 conseil/                    # Conseils pharmaceutiques
│   │   └── 📁 alertes/                    # Alertes de péremption
│   ├── 🎨 frontend/                       # Frontend spécifique Pharmacie
│   │   ├── 📁 src/                        # Code source React/Vue
│   │   │   ├── 📁 components/             # Composants pharmacie
│   │   │   │   ├── 📁 medicament/         # Composants médicaments
│   │   │   │   ├── 📁 ordonnance/         # Composants ordonnances
│   │   │   │   ├── 📁 stock/              # Composants stock
│   │   │   │   ├── 📁 conseil/            # Composants conseils
│   │   │   │   └── 📁 common/             # Composants communs
│   │   │   ├── 📁 pages/                  # Pages de l'application
│   │   │   ├── 📁 hooks/                  # Hooks personnalisés
│   │   │   ├── 📁 utils/                  # Utilitaires
│   │   │   ├── 📁 styles/                 # Styles SCSS/CSS
│   │   │   ├── 📁 assets/                 # Images, icônes, polices
│   │   │   ├── 📄 App.jsx                 # Application principale
│   │   │   ├── 📄 index.jsx               # Point d'entrée
│   │   │   └── 📄 routes.jsx              # Configuration des routes
│   │   ├── 📁 public/                     # Fichiers publics
│   │   │   ├── 📄 index.html              # Template HTML
│   │   │   ├── 📄 favicon.ico             # Favicon pharmacie
│   │   │   └── 📄 manifest.json           # Manifest PWA
│   │   ├── 📄 package.json                # Dépendances frontend
│   │   ├── 📄 webpack.config.js           # Configuration Webpack
│   │   ├── 📄 tailwind.config.js          # Configuration Tailwind
│   │   ├── 📄 .babelrc                    # Configuration Babel
│   │   └── 📄 README.md                   # Documentation frontend
│   ├── 📁 templates/                      # Templates Django pharmacie
│   ├── 📁 static/                         # Assets statiques Django pharmacie
│   └── 📄 README.md                       # Documentation pharmacie
│
├── 💻 YZ-ELECTRONIQUE-ENTREPRISE-E/       # Projet Électronique et High-Tech
│   ├── 📁 config/                         # Configuration électronique
│   ├── 📁 apps/                           # Applications métier
│   │   ├── 📁 produit/                    # Gestion des produits tech
│   │   ├── 📁 categorie/                  # Catégories électroniques
│   │   ├── 📁 commande/                   # Commandes en ligne
│   │   ├── 📁 livraison/                  # Livraison sécurisée
│   │   ├── 📁 garantie/                   # Gestion des garanties
│   │   ├── 📁 support/                    # Support technique
│   │   └── 📁 reparation/                 # Service de réparation
│   ├── 🎨 frontend/                       # Frontend spécifique Électronique
│   │   ├── 📁 src/                        # Code source React/Vue
│   │   │   ├── 📁 components/             # Composants électronique
│   │   │   │   ├── 📁 produit/            # Composants produits
│   │   │   │   ├── 📁 categorie/          # Composants catégories
│   │   │   │   ├── 📁 garantie/           # Composants garanties
│   │   │   │   ├── 📁 support/            # Composants support
│   │   │   │   └── 📁 common/             # Composants communs
│   │   │   ├── 📁 pages/                  # Pages de l'application
│   │   │   ├── 📁 hooks/                  # Hooks personnalisés
│   │   │   ├── 📁 utils/                  # Utilitaires
│   │   │   ├── 📁 styles/                 # Styles SCSS/CSS
│   │   │   ├── 📁 assets/                 # Images, icônes, polices
│   │   │   ├── 📄 App.jsx                 # Application principale
│   │   │   ├── 📄 index.jsx               # Point d'entrée
│   │   │   └── 📄 routes.jsx              # Configuration des routes
│   │   ├── 📁 public/                     # Fichiers publics
│   │   │   ├── 📄 index.html              # Template HTML
│   │   │   ├── 📄 favicon.ico             # Favicon électronique
│   │   │   └── 📄 manifest.json           # Manifest PWA
│   │   ├── 📄 package.json                # Dépendances frontend
│   │   ├── 📄 webpack.config.js           # Configuration Webpack
│   │   ├── 📄 tailwind.config.js          # Configuration Tailwind
│   │   ├── 📄 .babelrc                    # Configuration Babel
│   │   └── 📄 README.md                   # Documentation frontend
│   ├── 📁 templates/                      # Templates Django électronique
│   ├── 📁 static/                         # Assets statiques Django électronique
│   └── 📄 README.md                       # Documentation électronique
│
├── 💄 YZ-COSMETIQUE-ENTREPRISE-F/         # Projet Cosmétiques et Beauté
│   ├── 📁 config/                         # Configuration cosmétique
│   ├── 📁 apps/                           # Applications métier
│   │   ├── 📁 produit/                    # Gestion des cosmétiques
│   │   ├── 📁 marque/                     # Gestion des marques
│   │   ├── 📁 commande/                   # Commandes beauté
│   │   ├── 📁 livraison/                  # Livraison fragile
│   │   ├── 📁 conseil/                    # Conseils beauté
│   │   ├── 📁 fidelite/                   # Programme de fidélité
│   │   └── 📁 test_virtuel/               # Tests virtuels produits
│   ├── 🎨 frontend/                       # Frontend spécifique Cosmétique
│   │   ├── 📁 src/                        # Code source React/Vue
│   │   │   ├── 📁 components/             # Composants cosmétique
│   │   │   │   ├── 📁 produit/            # Composants produits
│   │   │   │   ├── 📁 marque/             # Composants marques
│   │   │   │   ├── 📁 conseil/            # Composants conseils
│   │   │   │   ├── 📁 fidelite/           # Composants fidélité
│   │   │   │   └── 📁 common/             # Composants communs
│   │   │   ├── 📁 pages/                  # Pages de l'application
│   │   │   ├── 📁 hooks/                  # Hooks personnalisés
│   │   │   ├── 📁 utils/                  # Utilitaires
│   │   │   ├── 📁 styles/                 # Styles SCSS/CSS
│   │   │   ├── 📁 assets/                 # Images, icônes, polices
│   │   │   ├── 📄 App.jsx                 # Application principale
│   │   │   ├── 📄 index.jsx               # Point d'entrée
│   │   │   └── 📄 routes.jsx              # Configuration des routes
│   │   ├── 📁 public/                     # Fichiers publics
│   │   │   ├── 📄 index.html              # Template HTML
│   │   │   ├── 📄 favicon.ico             # Favicon cosmétique
│   │   │   └── 📄 manifest.json           # Manifest PWA
│   │   ├── 📄 package.json                # Dépendances frontend
│   │   ├── 📄 webpack.config.js           # Configuration Webpack
│   │   ├── 📄 tailwind.config.js          # Configuration Tailwind
│   │   ├── 📄 .babelrc                    # Configuration Babel
│   │   └── 📄 README.md                   # Documentation frontend
│   ├── 📁 templates/                      # Templates Django cosmétique
│   ├── 📁 static/                         # Assets statiques Django cosmétique
│   └── 📄 README.md                       # Documentation cosmétique
│
├── 🚗 YZ-AUTOMOBILE-ENTREPRISE-G/         # Projet Automobile et Pièces
│   ├── 📁 config/                         # Configuration automobile
│   ├── 📁 apps/                           # Applications métier
│   │   ├── 📁 vehicule/                   # Gestion des véhicules
│   │   ├── 📁 piece/                      # Gestion des pièces
│   │   ├── 📁 commande/                   # Commandes pièces
│   │   ├── 📁 livraison/                  # Livraison express
│   │   ├── 📁 garage/                     # Services garage
│   │   ├── 📁 rdv/                        # Prise de rendez-vous
│   │   └── 📁 diagnostic/                 # Diagnostic véhicule
│   ├── 🎨 frontend/                       # Frontend spécifique Automobile
│   │   ├── 📁 src/                        # Code source React/Vue
│   │   │   ├── 📁 components/             # Composants automobile
│   │   │   │   ├── 📁 vehicule/           # Composants véhicules
│   │   │   │   ├── 📁 piece/              # Composants pièces
│   │   │   │   ├── 📁 garage/             # Composants garage
│   │   │   │   ├── 📁 diagnostic/         # Composants diagnostic
│   │   │   │   └── 📁 common/             # Composants communs
│   │   │   ├── 📁 pages/                  # Pages de l'application
│   │   │   ├── 📁 hooks/                  # Hooks personnalisés
│   │   │   ├── 📁 utils/                  # Utilitaires
│   │   │   ├── 📁 styles/                 # Styles SCSS/CSS
│   │   │   ├── 📁 assets/                 # Images, icônes, polices
│   │   │   ├── 📄 App.jsx                 # Application principale
│   │   │   ├── 📄 index.jsx               # Point d'entrée
│   │   │   └── 📄 routes.jsx              # Configuration des routes
│   │   ├── 📁 public/                     # Fichiers publics
│   │   │   ├── 📄 index.html              # Template HTML
│   │   │   ├── 📄 favicon.ico             # Favicon automobile
│   │   │   └── 📄 manifest.json           # Manifest PWA
│   │   ├── 📄 package.json                # Dépendances frontend
│   │   ├── 📄 webpack.config.js           # Configuration Webpack
│   │   ├── 📄 tailwind.config.js          # Configuration Tailwind
│   │   ├── 📄 .babelrc                    # Configuration Babel
│   │   └── 📄 README.md                   # Documentation frontend
│   ├── 📁 templates/                      # Templates Django automobile
│   ├── 📁 static/                         # Assets statiques Django automobile
│   └── 📄 README.md                       # Documentation automobile
│
├── 🏠 YZ-IMMOBILIER-ENTREPRISE-H/         # Projet Immobilier et Location
│   ├── 📁 config/                         # Configuration immobilier
│   ├── 📁 apps/                           # Applications métier
│   │   ├── 📁 bien/                       # Gestion des biens
│   │   ├── 📁 client/                     # Gestion des clients
│   │   ├── 📁 visite/                     # Planification des visites
│   │   ├── 📁 contrat/                    # Gestion des contrats
│   │   ├── 📁 maintenance/                # Maintenance des biens
│   │   ├── 📁 comptabilite/               # Comptabilité locative
│   │   └── 📁 syndic/                     # Gestion syndicale
│   ├── 🎨 frontend/                       # Frontend spécifique Immobilier
│   │   ├── 📁 src/                        # Code source React/Vue
│   │   │   ├── 📁 components/             # Composants immobilier
│   │   │   │   ├── 📁 bien/               # Composants biens
│   │   │   │   ├── 📁 visite/             # Composants visites
│   │   │   │   ├── 📁 contrat/            # Composants contrats
│   │   │   │   ├── 📁 recherche/          # Composants recherche
│   │   │   │   └── 📁 common/             # Composants communs
│   │   │   ├── 📁 pages/                  # Pages de l'application
│   │   │   ├── 📁 hooks/                  # Hooks personnalisés
│   │   │   ├── 📁 utils/                  # Utilitaires
│   │   │   ├── 📁 styles/                 # Styles SCSS/CSS
│   │   │   ├── 📁 assets/                 # Images, icônes, polices
│   │   │   ├── 📄 App.jsx                 # Application principale
│   │   │   ├── 📄 index.jsx               # Point d'entrée
│   │   │   └── 📄 routes.jsx              # Configuration des routes
│   │   ├── 📁 public/                     # Fichiers publics
│   │   │   ├── 📄 index.html              # Template HTML
│   │   │   ├── 📄 favicon.ico             # Favicon immobilier
│   │   │   └── 📄 manifest.json           # Manifest PWA
│   │   ├── 📄 package.json                # Dépendances frontend
│   │   ├── 📄 webpack.config.js           # Configuration Webpack
│   │   ├── 📄 tailwind.config.js          # Configuration Tailwind
│   │   ├── 📄 .babelrc                    # Configuration Babel
│   │   └── 📄 README.md                   # Documentation frontend
│   ├── 📁 templates/                      # Templates Django immobilier
│   ├── 📁 static/                         # Assets statiques Django immobilier
│   └── 📄 README.md                       # Documentation immobilier
│
├── 🎓 YZ-EDUCATION-ENTREPRISE-I/          # Projet Éducation et Formation
│   ├── 📁 config/                         # Configuration éducation
│   ├── 📁 apps/                           # Applications métier
│   │   ├── 📁 formation/                  # Gestion des formations
│   │   ├── 📁 etudiant/                   # Gestion des étudiants
│   │   ├── 📁 formateur/                  # Gestion des formateurs
│   │   ├── 📁 planning/                   # Planning des cours
│   │   ├── 📁 evaluation/                 # Évaluations et notes
│   │   ├── 📁 certification/              # Gestion des certifications
│   │   └── 📁 finance/                    # Gestion financière
│   ├── 🎨 frontend/                       # Frontend spécifique Éducation
│   │   ├── 📁 src/                        # Code source React/Vue
│   │   │   ├── 📁 components/             # Composants éducation
│   │   │   │   ├── 📁 formation/          # Composants formations
│   │   │   │   ├── 📁 etudiant/           # Composants étudiants
│   │   │   │   ├── 📁 planning/           # Composants planning
│   │   │   │   ├── 📁 evaluation/         # Composants évaluations
│   │   │   │   └── 📁 common/             # Composants communs
│   │   │   ├── 📁 pages/                  # Pages de l'application
│   │   │   ├── 📁 hooks/                  # Hooks personnalisés
│   │   │   ├── 📁 utils/                  # Utilitaires
│   │   │   ├── 📁 styles/                 # Styles SCSS/CSS
│   │   │   ├── 📁 assets/                 # Images, icônes, polices
│   │   │   ├── 📄 App.jsx                 # Application principale
│   │   │   ├── 📄 index.jsx               # Point d'entrée
│   │   │   └── 📄 routes.jsx              # Configuration des routes
│   │   ├── 📁 public/                     # Fichiers publics
│   │   │   ├── 📄 index.html              # Template HTML
│   │   │   ├── 📄 favicon.ico             # Favicon éducation
│   │   │   └── 📄 manifest.json           # Manifest PWA
│   │   ├── 📄 package.json                # Dépendances frontend
│   │   ├── 📄 webpack.config.js           # Configuration Webpack
│   │   ├── 📄 tailwind.config.js          # Configuration Tailwind
│   │   ├── 📄 .babelrc                    # Configuration Babel
│   │   └── 📄 README.md                   # Documentation frontend
│   ├── 📁 templates/                      # Templates Django éducation
│   ├── 📁 static/                         # Assets statiques Django éducation
│   └── 📄 README.md                       # Documentation éducation
│
├── 🏥 YZ-SANTE-ENTREPRISE-J/              # Projet Santé et Bien-être
│   ├── 📁 config/                         # Configuration santé
│   ├── 📁 apps/                           # Applications métier
│   │   ├── 📁 patient/                    # Gestion des patients
│   │   ├── 📁 medecin/                    # Gestion des médecins
│   │   ├── 📁 rdv/                        # Prise de rendez-vous
│   │   ├── 📁 dossier/                    # Dossiers médicaux
│   │   ├── 📁 prescription/               # Gestion des prescriptions
│   │   ├── 📁 telemedecine/               # Consultations à distance
│   │   └── 📁 facturation/                # Facturation médicale
│   ├── 🎨 frontend/                       # Frontend spécifique Santé
│   │   ├── 📁 src/                        # Code source React/Vue
│   │   │   ├── 📁 components/             # Composants santé
│   │   │   │   ├── 📁 patient/            # Composants patients
│   │   │   │   ├── 📁 medecin/            # Composants médecins
│   │   │   │   ├── 📁 rdv/                # Composants rendez-vous
│   │   │   │   ├── 📁 dossier/            # Composants dossiers
│   │   │   │   └── 📁 common/             # Composants communs
│   │   │   ├── 📁 pages/                  # Pages de l'application
│   │   │   ├── 📁 hooks/                  # Hooks personnalisés
│   │   │   ├── 📁 utils/                  # Utilitaires
│   │   │   ├── 📁 styles/                 # Styles SCSS/CSS
│   │   │   ├── 📁 assets/                 # Images, icônes, polices
│   │   │   ├── 📄 App.jsx                 # Application principale
│   │   │   ├── 📄 index.jsx               # Point d'entrée
│   │   │   └── 📄 routes.jsx              # Configuration des routes
│   │   ├── 📁 public/                     # Fichiers publics
│   │   │   ├── 📄 index.html              # Template HTML
│   │   │   ├── 📄 favicon.ico             # Favicon santé
│   │   │   └── 📄 manifest.json           # Manifest PWA
│   │   ├── 📄 package.json                # Dépendances frontend
│   │   ├── 📄 webpack.config.js           # Configuration Webpack
│   │   ├── 📄 tailwind.config.js          # Configuration Tailwind
│   │   ├── 📄 .babelrc                    # Configuration Babel
│   │   └── 📄 README.md                   # Documentation frontend
│   ├── 📁 templates/                      # Templates Django santé
│   ├── 📁 static/                         # Assets statiques Django santé
│   └── 📄 README.md                       # Documentation santé
│

│
├── 🐳 docker/                              # Configuration Docker globale
│   ├── 📄 docker-compose.yml              # Compose principal
│   ├── 📄 Dockerfile                      # Image de base
│   ├── 📁 nginx/                          # Configuration Nginx
│   ├── 📁 postgres/                       # Configuration PostgreSQL
│   └── 📁 redis/                          # Configuration Redis
│
├── 🚀 deployment/                          # Scripts de déploiement
│   ├── 📄 deploy.sh                       # Script de déploiement
│   ├── 📄 backup.sh                       # Script de sauvegarde
│   ├── 📄 restore.sh                      # Script de restauration
│   └── 📄 monitoring.sh                   # Script de monitoring
│
├── 📚 docs/                                # Documentation globale
│   ├── 📄 architecture.md                 # Architecture technique
│   ├── 📄 api.md                          # Documentation API
│   ├── 📄 deployment.md                   # Guide de déploiement
│   ├── 📄 user_guide.md                   # Guide utilisateur
│   └── 📁 images/                         # Images de documentation
│
├── 🧪 tests_globaux/                       # Tests globaux
│   ├── 📁 integration/                    # Tests d'intégration
│   ├── 📁 performance/                    # Tests de performance
│   ├── 📁 security/                       # Tests de sécurité
│   └── 📄 run_tests.py                    # Lanceur de tests
│
├── 📊 monitoring/                          # Monitoring et observabilité
│   ├── 📄 prometheus.yml                  # Configuration Prometheus
│   ├── 📄 grafana.yml                     # Configuration Grafana
│   ├── 📄 alertmanager.yml                # Configuration alertes
│   └── 📁 dashboards/                     # Dashboards Grafana
│
├── 🔐 secrets/                             # Gestion des secrets (gitignored)
│   ├── 📄 .env.example                    # Exemple de variables d'environnement
│   ├── 📄 .env.local                      # Variables locales
│   └── 📄 .env.production                 # Variables de production
│
├── 📄 .gitignore                           # Fichiers ignorés par Git
├── 📄 docker-compose.override.yml          # Override Docker local
├── 📄 Makefile                             # Commandes Make
├── 📄 requirements.txt                     # Dépendances Python globales
├── 📄 package.json                         # Dépendances Node.js globales
└── 📄 README.md                            # Documentation principale
```

## 🎨 Structure Frontend par Projet

### **Différence entre Projet Existant et Nouveaux Projets**

#### **👟 YZ-CMD-YOOZAK (PROJET EXISTANT)**
- **Frontend** : Utilise les templates Django et assets statiques existants
- **Pas de dossier frontend/** : Interface déjà en place et fonctionnelle
- **Migration** : Peut être migré vers l'architecture multi-tenants sans modification frontend

#### **🧵 YZ-TEXTILE-ENTREPRISE-A à 🏥 YZ-SANTE-ENTREPRISE-J (NOUVEAUX PROJETS)**
- **Frontend** : Chaque projet possède son propre dossier `frontend/` personnalisé
- **Technologies** : React/Vue.js avec composants métier spécifiques
- **Développement** : Interface complètement nouvelle et adaptée au secteur

---

### **Architecture Frontend Commune à Tous les Nouveaux Projets**

Chaque projet sectoriel possède son propre dossier `frontend/` avec une structure standardisée mais personnalisée selon ses besoins métier :

```
📁 frontend/                                # Frontend spécifique au projet
├── 📁 src/                                 # Code source principal
│   ├── 📁 components/                      # Composants métier spécifiques
│   │   ├── 📁 [module_metier]/            # Composants par module métier
│   │   └── 📁 common/                     # Composants communs réutilisables
│   ├── 📁 pages/                          # Pages de l'application
│   ├── 📁 hooks/                          # Hooks personnalisés
│   ├── 📁 utils/                          # Utilitaires et helpers
│   ├── 📁 styles/                         # Styles SCSS/CSS personnalisés
│   ├── 📁 assets/                         # Images, icônes, polices spécifiques
│   ├── 📄 App.jsx                         # Application principale
│   ├── 📄 index.jsx                       # Point d'entrée
│   └── 📄 routes.jsx                      # Configuration des routes
├── 📁 public/                             # Fichiers publics
│   ├── 📄 index.html                      # Template HTML
│   ├── 📄 favicon.ico                     # Favicon spécifique au projet
│   └── 📄 manifest.json                   # Manifest PWA
├── 📄 package.json                         # Dépendances frontend
├── 📄 webpack.config.js                    # Configuration Webpack
├── 📄 tailwind.config.js                   # Configuration Tailwind
├── 📄 .babelrc                             # Configuration Babel
└── 📄 README.md                            # Documentation frontend
```

### **Personnalisation par Secteur d'Activité**

#### **🧵 YZ-TEXTILE-ENTREPRISE-A**
- **Composants spécifiques** : Gestion des tailles, collections, variantes
- **Interface e-commerce** : Catalogue, panier, commandes
- **Thème** : Couleurs et styles adaptés au textile

#### **🏭 YZ-LOGISTIQUE-ENTREPRISE-B**
- **Composants spécifiques** : Gestion des entrepôts, zones, mouvements
- **Interface logistique** : Plans d'entrepôt, traçabilité
- **Thème** : Interface industrielle et technique

#### **🍽️ YZ-RESTAURANT-ENTREPRISE-C**
- **Composants spécifiques** : Menus, ingrédients, livreurs
- **Interface restauration** : Commandes en ligne, livraison
- **Thème** : Design culinaire et convivial

#### **💊 YZ-PHARMACIE-ENTREPRISE-D**
- **Composants spécifiques** : Médicaments, ordonnances, alertes
- **Interface pharmaceutique** : Conseils, prescriptions
- **Thème** : Design médical et rassurant

#### **💻 YZ-ELECTRONIQUE-ENTREPRISE-E**
- **Composants spécifiques** : Produits tech, garanties, support
- **Interface high-tech** : Spécifications techniques, diagnostics
- **Thème** : Design moderne et technologique

#### **💄 YZ-COSMETIQUE-ENTREPRISE-F**
- **Composants spécifiques** : Produits beauté, conseils, fidélité
- **Interface cosmétique** : Tests virtuels, recommandations
- **Thème** : Design élégant et féminin

#### **🚗 YZ-AUTOMOBILE-ENTREPRISE-G**
- **Composants spécifiques** : Véhicules, pièces, rendez-vous
- **Interface automobile** : Services garage, diagnostics
- **Thème** : Design mécanique et professionnel

#### **🏠 YZ-IMMOBILIER-ENTREPRISE-H**
- **Composants spécifiques** : Biens, visites, contrats
- **Interface immobilier** : Recherche, planification
- **Thème** : Design professionnel et rassurant

#### **🎓 YZ-EDUCATION-ENTREPRISE-I**
- **Composants spécifiques** : Formations, étudiants, planning
- **Interface éducation** : Cours, évaluations, certifications
- **Thème** : Design éducatif et motivant

#### **🏥 YZ-SANTE-ENTREPRISE-J**
- **Composants spécifiques** : Patients, médecins, rendez-vous
- **Interface santé** : Consultations, dossiers médicaux
- **Thème** : Design médical et rassurant

---

## 🔄 Relations entre les Projets

### **1. YZ-PLATFORM (Cœur du Système)**
- **Centralise** tous les services communs
- **Gère** l'authentification multi-tenants
- **Fournit** les APIs partagées
- **Contrôle** la facturation et les abonnements

### **2. YZ-CMD-YOOZAK (Cas de Base)**
- **Hérite** de YZ-PLATFORM
- **Utilise** les services communs
- **Ajoute** ses fonctionnalités spécifiques
- **Sert** de référence pour les autres projets

### **3. Projets Sectoriels (A à J)**
- **Héritent** tous de YZ-PLATFORM
- **Réutilisent** les composants communs
- **Implémentent** leurs modèles métier spécifiques
- **Personnalisent** l'interface utilisateur

## 🚀 Avantages de cette Architecture

### **1. Frontend Décentralisé et Personnalisé**

#### **Indépendance des Projets**
- **Chaque projet** a son propre frontend complètement indépendant
- **Développement parallèle** possible sans conflits
- **Technologies** adaptées aux besoins spécifiques de chaque secteur
- **Équipes dédiées** peuvent travailler sur leur frontend sans interférence

#### **Personnalisation Métier**
- **Interface adaptée** aux processus spécifiques de chaque secteur
- **Composants métier** développés selon les besoins réels
- **Thèmes visuels** cohérents avec l'identité de chaque entreprise
- **UX/UI** optimisée pour les utilisateurs finaux de chaque domaine

#### **Maintenance et Évolutions**
- **Mises à jour** indépendantes par projet
- **Bugs isolés** à un seul frontend
- **Évolutions** sans impact sur les autres projets
- **Tests** spécifiques à chaque interface

- **Séparation** logique des responsabilités
- **Navigation** facile dans le code
- **Maintenance** simplifiée par projet

### **3. Réutilisation Maximale**
- **Composants** partagés entre tous les projets
- **Modèles** universels avec extensions sectorielles
- **APIs** centralisées et documentées

### **4. Développement Parallèle**
- **Équipes** peuvent travailler sur différents projets
- **Tests** isolés par projet
- **Déploiements** indépendants possibles

### **5. Évolutivité**
- **Ajout** facile de nouveaux projets
- **Migration** progressive des fonctionnalités
- **Scalabilité** horizontale et verticale

## 📋 Commandes Utiles

### **Développement Local**

#### **Backend Django**
```bash
# Démarrer la plateforme principale
cd YZ-CMD/YZ-PLATFORM
python manage.py runserver

# Démarrer un projet spécifique
cd YZ-CMD/YZ-CMD-YOOZAK
python manage.py runserver 8001

# Démarrer avec Docker
cd YZ-CMD
docker-compose up -d
```

#### **Frontend React/Vue (Nouveaux Projets)**
```bash
# Démarrer le frontend Textile
cd YZ-CMD/YZ-TEXTILE-ENTREPRISE-A/frontend
npm install
npm start

# Démarrer le frontend Logistique
cd YZ-CMD/YZ-LOGISTIQUE-ENTREPRISE-B/frontend
npm install
npm start

# Démarrer le frontend Restaurant
cd YZ-CMD/YZ-RESTAURANT-ENTREPRISE-C/frontend
npm install
npm start

# Démarrer tous les frontends en parallèle
cd YZ-CMD
npm run dev:all
```

#### **Note sur YZ-CMD-YOOZAK**
```bash
# Le projet Yoozak utilise les templates Django existants
# Pas de commandes frontend nécessaires
cd YZ-CMD/YZ-CMD-YOOZAK
python manage.py runserver 8001
```

### **Gestion des Tenants**
```bash
# Créer un nouveau tenant
cd YZ-CMD/YZ-PLATFORM
python manage.py create_tenant "Nom Entreprise" "domaine.com"

# Migrer un tenant existant
python manage.py migrate_tenant "domaine.com"

# Sauvegarder un tenant
python manage.py backup_tenant "domaine.com"
```

### **Tests et Qualité**
```bash
# Tests globaux
cd YZ-CMD
python tests_globaux/run_tests.py

# Tests d'un projet spécifique
cd YZ-CMD/YZ-CMD-YOOZAK
python manage.py test

# Tests de performance
cd YZ-CMD
python tests_globaux/performance/run_performance_tests.py
```

## 🎯 **Résumé de l'Approche Frontend Décentralisée**

### **Philosophie "Un Projet = Un Frontend"**

Cette architecture adopte une approche **hybride** :
- **YZ-CMD-YOOZAK** : Conserve son interface Django existante (pas de dossier frontend)
- **Nouveaux projets sectoriels** : Chaque projet possède son propre frontend complètement indépendant
- **Backend partagé** : Tous les projets partagent le même backend Django multi-tenants

### **Avantages de cette Approche**

1. **🎨 Personnalisation Totale** : Chaque frontend est adapté aux besoins métier spécifiques
2. **🚀 Développement Parallèle** : Les équipes peuvent travailler simultanément sur différents frontends
3. **🔒 Isolation des Problèmes** : Un bug dans un frontend n'affecte pas les autres
4. **📱 Technologies Adaptées** : Chaque projet peut choisir React, Vue, ou d'autres frameworks
5. **🎯 UX/UI Spécialisée** : Interface optimisée pour chaque secteur d'activité
6. **📦 Déploiements Indépendants** : Mise à jour d'un frontend sans impact sur les autres

### **Architecture Hybride**

- **Backend** : Centralisé et partagé (YZ-PLATFORM)
- **Frontend** : Décentralisé et personnalisé (1 par projet)
- **Base de données** : Multi-tenants avec isolation des données
- **APIs** : Centralisées mais consommées différemment par chaque frontend

### **Workflow de Développement**

1. **YZ-PLATFORM** fournit les APIs et services communs
2. **Chaque projet** développe son frontend spécifique
3. **Les frontends** consomment les APIs communes
4. **Chaque projet** peut ajouter des APIs spécifiques si nécessaire
5. **Déploiement** indépendant de chaque frontend

---

Cette architecture vous permet de voir tous vos projets dans le même dossier YZ-CMD tout en maintenant une séparation claire et une organisation logique. Chaque projet peut être développé, testé et déployé indépendamment tout en bénéficiant des services communs de la plateforme. **L'approche frontend décentralisée garantit une personnalisation maximale tout en conservant la cohérence technique du backend.**
