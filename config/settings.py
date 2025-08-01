"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 5.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-beulebpje4!9xvoqg(@rn7$j0rt2)n2%8z=!euaw%t3&3j_z8*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '192.168.216.128',  # Votre adresse IP locale
    '192.168.66.128',
    '192.168.216.*',    # Toutes les adresses de votre sous-réseau
    '192.168.8.114',
    '192.168.145.129',
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Applications tierces
    'rest_framework',
    'django_filters',
    'crispy_forms',
    'widget_tweaks',
    'corsheaders',
    'django_extensions',
    'tailwind',
    'theme',
    'django_browser_reload',
    
    # Applications locales
    'commande',
    'article',
    'client',
    'livraison',
    'parametre',
    'operatConfirme',
    'operatLogistic',
    'synchronisation',
    'Prepacommande',
    'kpis',
    
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'config.middleware.SessionTimeoutMiddleware',
    'config.middleware.UserTypeValidationMiddleware',
    'config.middleware.CSRFDebugMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_browser_reload.middleware.BrowserReloadMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuration PostgreSQL (commentée)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME', default='yzcmd_db'),
#         'USER': config('DB_USER', default='postgres'),
#         'PASSWORD': config('DB_PASSWORD', default=''),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Africa/Casablanca'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (Uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Django REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
}

# Crispy Forms configuration
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# CORS configuration
CORS_ALLOW_ALL_ORIGINS = True  # Pour le développement seulement
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://192.168.216.128:8000",
    "http://192.168.66.128:8000",    
    "http://192.168.8.114:8000",
    "http://192.168.145.129:8000",
    "http://192.168.20.128:8000",
]

# Autoriser les requêtes depuis votre réseau local
CORS_ALLOW_CREDENTIALS = True

# Tailwind configuration
TAILWIND_APP_NAME = 'theme'

# Configuration des sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400  # 24 heures en secondes
SESSION_COOKIE_SECURE = not DEBUG  # Cookies sécurisés en HTTPS (False en dev, True en prod)
SESSION_COOKIE_HTTPONLY = True  # Protection XSS
SESSION_SAVE_EVERY_REQUEST = True  # Rafraîchir la session à chaque requête
SESSION_EXPIRE_AT_BROWSER_CLOSE = False  # La session persiste même après fermeture du navigateur
SESSION_COOKIE_NAME = 'yz_cmd_sessionid'  # Nom personnalisé du cookie de session

# Protection CSRF renforcée
CSRF_COOKIE_SECURE = not DEBUG  # False en développement, True en production
CSRF_COOKIE_HTTPONLY = True
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000', 
    'http://127.0.0.1:8000',
    'http://192.168.216.128:8000',
    'http://192.168.216.*:8000',
    'http://192.168.66.128:8000',
    "http://192.168.8.114:8000",
    "http://192.168.145.129:8000",
    "http://192.168.20.128:8000",
    # Ajout de toutes les origines possibles pour le développement local
    'http://localhost',
    'http://127.0.0.1',
    'http://[::1]',
    'http://localhost:*',
    'http://127.0.0.1:*',
    'http://192.168.66.128:*',
    "http://192.168.8.114:*",
    "http://192.168.20.128:*",
]
# Désactiver l'utilisation des sessions pour le CSRF token en développement
CSRF_USE_SESSIONS = False
# Augmenter la durée de vie du cookie CSRF
CSRF_COOKIE_AGE = 31449600  # 1 an en secondes
# Définir un nom personnalisé pour le cookie CSRF
CSRF_COOKIE_NAME = 'yz_csrf_token'

# Configuration Google Sheets
GOOGLE_CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
GOOGLE_SHEET_URL = config('GOOGLE_SHEET_URL', default='')

# Délai d'inactivité avant déconnexion (en secondes) - 2 heures
SESSION_IDLE_TIMEOUT = 7200

# Configuration de redirection après connexion
LOGIN_REDIRECT_URL = '/home/'
LOGIN_URL = '/login/'
LOGOUT_REDIRECT_URL = '/login/'

# Configuration du logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'config.middleware': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuration pour éviter l'erreur TooManyFieldsSent
DATA_UPLOAD_MAX_NUMBER_FIELDS = 50000  # Augmenter la limite par défaut (1000) à 50000
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB en octets



NPM_BIN_PATH = "C:/Program Files/nodejs/npm.cmd"  # Chemin vers l'exécutable npm
