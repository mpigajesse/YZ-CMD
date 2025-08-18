# 🚨 Guide de Dépannage - Erreur MWI-005

## Problème identifié

**Erreur :** `Une erreur inattendue s'est produite lors de la validation de votre profil. Veuillez vous reconnecter. (Code: MWI-005)`

**Cause :** Erreur dans le middleware `UserTypeValidationMiddleware` lors de l'authentification des superviseurs.

## 🔍 Diagnostic

### 1. Vérifier les logs Django
```bash
# Regarder les logs pour l'erreur spécifique
tail -f debug.log | grep "UserTypeValidationMiddleware Error"
```

### 2. Erreur typique
```
[UserTypeValidationMiddleware Error]: unsupported operand type(s) for +: 'NoneType' and 'str'
```

## ✅ Solutions appliquées

### 1. Ajout du préfixe manquant pour SUPERVISEUR_PREPARATION
```python
# Dans config/middleware.py
self.allowed_prefixes = {
    'CONFIRMATION': '/operateur-confirme/',
    'LOGISTIQUE': '/operateur-logistique/',
    'PREPARATION': '/operateur-preparation/',
    'SUPERVISEUR_PREPARATION': '/Superpreparation/',  # ← AJOUTÉ
    'ADMIN': '/parametre/',
}
```

### 2. Ajout du chemin /home/ aux chemins autorisés
```python
self.universal_allowed_paths_startswith = (
    settings.STATIC_URL,
    settings.MEDIA_URL,
    '/login/',
    '/logout/',
    '/home/',  # ← AJOUTÉ
    '/password_reset/',
    '/__reload__/',
    '/api/csrf/',
)
```

### 3. Validation robuste des types d'opérateur
```python
# Vérifier que le type d'opérateur est géré
if not expected_prefix:
    messages.error(request, f"Type d'opérateur '{user_type}' non géré. (Code: MWI-003)")
    logout(request)
    return redirect(settings.LOGIN_URL)
```

### 4. Simplification de la logique de redirection
```python
# Utilisation d'un dictionnaire pour éviter les erreurs
redirect_urls = {
    'CONFIRMATION': 'operatConfirme:home',
    'LOGISTIQUE': 'operatLogistic:home',
    'PREPARATION': 'Prepacommande:home',
    'SUPERVISEUR_PREPARATION': 'Superpreparation:home',
    'ADMIN': 'app_admin:home'
}
```

## 🧪 Test de la correction

### 1. Tester le middleware
```bash
python manage.py shell < test_middleware.py
```

### 2. Vérifier la configuration
```bash
# Créer le groupe superviseur
python manage.py create_superviseur --create-group

# Vérifier la cohérence
python manage.py create_superviseur --check-consistency

# Synchroniser les groupes
python manage.py create_superviseur --sync-all
```

## 🔧 Vérifications supplémentaires

### 1. Vérifier que l'utilisateur superviseur existe
```python
# Dans le shell Django
from parametre.models import Operateur
from django.contrib.auth.models import User

# Vérifier l'utilisateur
user = User.objects.get(username='votre_username')
print(f"Groupes: {[g.name for g in user.groups.all()]}")

# Vérifier le profil
try:
    operateur = user.profil_operateur
    print(f"Type: {operateur.type_operateur}")
    print(f"Actif: {operateur.actif}")
except Operateur.DoesNotExist:
    print("Pas de profil Operateur")
```

### 2. Vérifier les URLs
```python
# Vérifier que l'URL Superpreparation existe
from django.urls import reverse
try:
    url = reverse('Superpreparation:home')
    print(f"URL Superpreparation: {url}")
except:
    print("Erreur: URL Superpreparation non trouvée")
```

## 🚀 Redémarrage après correction

### 1. Redémarrer le serveur Django
```bash
# Arrêter le serveur (Ctrl+C)
# Puis redémarrer
python manage.py runserver
```

### 2. Tester la connexion
1. Aller sur `/login/`
2. Se connecter avec un compte superviseur
3. Vérifier la redirection vers `/Superpreparation/`

## 📋 Codes d'erreur du middleware

| Code | Description | Solution |
|------|-------------|----------|
| **MWI-001** | Accès non autorisé | Redirection automatique |
| **MWI-002** | Type d'opérateur non géré | Vérifier le modèle Operateur |
| **MWI-003** | Type d'opérateur non géré | Ajouter dans allowed_prefixes |
| **MWI-004** | Profil Operateur manquant | Créer le profil via create_superviseur |
| **MWI-005** | Erreur inattendue | Voir ce guide de dépannage |
| **MWI-007** | Compte désactivé | Réactiver dans l'admin |

## 🔍 Logs à surveiller

### 1. Logs de connexion
```
INFO [CSRF Debug] URL: /login/
INFO [CSRF Debug] Cookie: yz_csrf_token
INFO [CSRF Debug] POST: [token]
```

### 2. Logs du middleware
```
INFO [UserTypeValidationMiddleware] Redirection: user_type -> expected_prefix
ERROR [UserTypeValidationMiddleware Error]: [détails de l'erreur]
```

## 🆘 Si le problème persiste

### 1. Vérifier la version Django
```bash
python -c "import django; print(django.get_version())"
```

### 2. Vérifier les migrations
```bash
python manage.py showmigrations
python manage.py migrate
```

### 3. Vérifier la configuration
```bash
python manage.py check
```

### 4. Mode DEBUG
```python
# Dans settings.py, vérifier que DEBUG = True
DEBUG = True
```

## 📞 Support

En cas de problème persistant :
1. Vérifier les logs complets
2. Utiliser le script de test
3. Vérifier la configuration des URLs
4. Consulter la documentation Django

---

**Version :** 1.0  
**Date :** 2025  
**Auteur :** YZ-CMD Team
