# Guide de Déploiement YZ-CMD sur Vercel

Ce guide vous explique comment déployer votre application Django YZ-CMD sur Vercel.

## Prérequis

- Un compte GitHub avec votre projet
- Un compte Vercel
- Une base de données PostgreSQL (Vercel Postgres ou externe)
- Un service Redis (optionnel, pour Celery)

## Configuration Locale

### 1. Test avec Docker

```bash
# Cloner le projet
git clone <votre-repo-github>
cd YZ-CMD

# Construire et démarrer avec Docker Compose
docker-compose up --build

# L'application sera disponible sur http://localhost:8000
```

### 2. Configuration des Variables d'Environnement

Créez un fichier `.env` basé sur `env.example` :

```bash
cp env.example .env
```

Modifiez les variables selon votre environnement :

```env
DEBUG=False
SECRET_KEY=votre-clé-secrète-générée
ALLOWED_HOSTS=localhost,127.0.0.1,votre-domaine.vercel.app

# Base de données
DB_NAME=yzcmd_db
DB_USER=postgres
DB_PASSWORD=votre-mot-de-passe
DB_HOST=votre-host-postgres
DB_PORT=5432

# Redis (optionnel)
REDIS_URL=redis://votre-redis-host:6379/0
```

## Déploiement sur Vercel

### 1. Préparation du Projet

Assurez-vous que tous les fichiers de configuration sont présents :
- `vercel.json`
- `build_files.sh`
- `runtime.txt`
- `requirements.txt`

### 2. Import sur Vercel

1. Allez sur [vercel.com/new](https://vercel.com/new)
2. Connectez-vous avec votre compte GitHub
3. Sélectionnez votre repository YZ-CMD
4. Cliquez sur "Import"

### 3. Configuration des Variables d'Environnement

Dans les paramètres de votre projet Vercel, ajoutez les variables d'environnement :

```env
DEBUG=False
SECRET_KEY=votre-clé-secrète-générée
ALLOWED_HOSTS=votre-domaine.vercel.app
DB_NAME=yzcmd_db
DB_USER=postgres
DB_PASSWORD=votre-mot-de-passe
DB_HOST=votre-host-postgres
DB_PORT=5432
```

### 4. Base de Données

#### Option A : Vercel Postgres
1. Dans votre projet Vercel, allez dans "Storage"
2. Créez une nouvelle base de données PostgreSQL
3. Copiez les variables de connexion dans vos variables d'environnement

#### Option B : Base de Données Externe
- Utilisez un service comme Supabase, Railway, ou PlanetScale
- Configurez les variables d'environnement avec les informations de connexion

### 5. Déploiement

1. Vercel détectera automatiquement que c'est un projet Django
2. Le build se lancera automatiquement
3. Votre application sera déployée sur `https://votre-projet.vercel.app`

## Configuration Post-Déploiement

### 1. Migrations de Base de Données

Si les migrations ne se sont pas exécutées automatiquement :

```bash
# Via Vercel CLI
vercel --prod
```

### 2. Création d'un Superuser

```bash
# Via Vercel CLI
vercel env pull .env
python manage.py createsuperuser
```

### 3. Collecte des Fichiers Statiques

Les fichiers statiques sont automatiquement collectés lors du build.

## Monitoring et Logs

- **Logs** : Disponibles dans l'interface Vercel
- **Monitoring** : Utilisez Vercel Analytics
- **Erreurs** : Configurez des notifications d'erreur

## Optimisations

### 1. Cache Redis
Pour améliorer les performances, configurez Redis :

```env
REDIS_URL=redis://votre-redis-host:6379/0
```

### 2. CDN pour les Fichiers Statiques
Utilisez AWS S3 ou Cloudinary pour les fichiers média :

```env
USE_S3=True
AWS_ACCESS_KEY_ID=votre-clé
AWS_SECRET_ACCESS_KEY=votre-secret
AWS_STORAGE_BUCKET_NAME=votre-bucket
```

### 3. Email
Configurez un service d'email :

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=votre-email@gmail.com
EMAIL_HOST_PASSWORD=votre-app-password
```

## Dépannage

### Erreurs Courantes

1. **Erreur de Migration** : Vérifiez les variables de base de données
2. **Erreur de Fichiers Statiques** : Vérifiez `STATIC_ROOT` et `STATIC_URL`
3. **Erreur de CORS** : Configurez `CORS_ALLOWED_ORIGINS`
4. **Erreur de CSRF** : Configurez `CSRF_TRUSTED_ORIGINS`

### Logs de Debug

```bash
# Voir les logs en temps réel
vercel logs --follow
```

## Support

Pour toute question ou problème :
1. Vérifiez les logs Vercel
2. Testez localement avec Docker
3. Vérifiez la configuration des variables d'environnement 