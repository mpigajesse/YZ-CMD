# 🎯 Groupe Superviseur - YZ-CMD

## Vue d'ensemble

Le groupe **superviseur** est un nouveau type d'utilisateur qui remplace le type d'opérateur pour les superviseurs de préparation. Ce groupe donne accès à l'interface **Superpreparation** avec des fonctionnalités avancées de supervision.

## 🚀 Configuration

### 1. Créer le groupe superviseur

#### Option A : Commande Django (Recommandée)
```bash
# Créer le groupe
python manage.py create_superviseur --create-group

# Assigner des utilisateurs
python manage.py create_superviseur --assign-users username1 username2

# Lister les superviseurs
python manage.py create_superviseur --list

# Vérifier la cohérence des groupes
python manage.py create_superviseur --check-consistency

# Synchroniser tous les groupes
python manage.py create_superviseur --sync-all
```

#### Option B : Script Python
```bash
python manage.py shell < create_superviseur_group.py
```

#### Option C : Interface Admin Django
1. Aller dans `/admin/auth/group/`
2. Créer un nouveau groupe nommé `superviseur`
3. Assigner les utilisateurs au groupe

### 2. Assigner des utilisateurs

Une fois le groupe créé, vous pouvez assigner des utilisateurs de plusieurs façons :

#### Via l'interface Admin Django
1. Aller dans `/admin/auth/user/`
2. Sélectionner l'utilisateur
3. Ajouter au groupe `superviseur`
4. Sauvegarder

#### Via la commande Django
```bash
python manage.py create_superviseur --assign-users john_doe jane_smith
```

#### Via le script Python
Le script interactif vous demandera les noms d'utilisateur.

## 🔧 Fonctionnalités

### Accès automatique
- **URL de redirection** : `/Superpreparation/`
- **Interface** : Interface Superpreparation avec fonctionnalités avancées
- **Permissions** : Accès complet aux fonctionnalités de supervision

### Profil automatique
- Création automatique du profil `Operateur` avec `type_operateur = 'SUPERVISEUR_PREPARATION'`
- Synchronisation des informations User ↔ Operateur
- Gestion des permissions via le middleware

## 📋 Utilisation

### 1. Connexion
Les utilisateurs superviseurs se connectent normalement via `/login/`

### 2. Redirection automatique
Après connexion, ils sont automatiquement redirigés vers `/Superpreparation/`

### 3. Interface Superpreparation
- **Dashboard** : Vue d'ensemble des opérations de préparation
- **Gestion des commandes** : Supervision des commandes en cours
- **Statistiques** : KPIs et métriques de performance
- **Exports** : Export de données consolidées
- **Gestion du stock** : Supervision des mouvements de stock

## 🔒 Sécurité

### Middleware de validation
- Vérification automatique des types d'utilisateur
- Redirection automatique vers la bonne interface
- Protection contre l'accès non autorisé

### Permissions
- Accès limité à l'interface Superpreparation
- Validation des profils actifs
- Traçabilité des actions

## 🛠️ Dépannage

### Problème : Utilisateur non redirigé
```bash
# Vérifier le groupe
python manage.py create_superviseur --list

# Vérifier le profil Operateur
python manage.py shell
>>> from parametre.models import Operateur
>>> Operateur.objects.filter(user__username='username')
```

### Problème : Accès refusé
1. Vérifier que l'utilisateur est dans le groupe `superviseur`
2. Vérifier que le profil Operateur existe et est actif
3. Vérifier que `type_operateur = 'SUPERVISEUR_PREPARATION'`

### Problème : Erreur de migration
```bash
# Vérifier les migrations
python manage.py showmigrations

# Appliquer les migrations si nécessaire
python manage.py migrate
```

## 📊 Structure des données

### Modèle Operateur
```python
TYPE_OPERATEUR_CHOICES = [
    ('CONFIRMATION', 'Opérateur de Confirmation'),
    ('LOGISTIQUE', 'Opérateur Logistique'),
    ('PREPARATION', 'Opérateur de Préparation'),
    ('SUPERVISEUR_PREPARATION', 'Superviseur de Préparation'),  # ← Nouveau
    ('ADMIN', 'Administrateur'),
]
```

### Propriétés du modèle
```python
@property
def is_superviseur_preparation(self):
    return self.type_operateur == 'SUPERVISEUR_PREPARATION'

@property
def is_superviseur(self):
    return self.type_operateur == 'SUPERVISEUR_PREPARATION'
```

### Méthodes de classe
```python
# Récupérer tous les superviseurs
Operateur.get_superviseurs()

# Récupérer les opérateurs d'un groupe spécifique
Operateur.get_by_group('superviseur')

# Créer un superviseur depuis un utilisateur
Operateur.create_superviseur_from_user(user)

# Obtenir tous les types avec leurs noms d'affichage
Operateur.get_all_types_display()
```

### Méthodes d'instance
```python
# Obtenir le nom du groupe Django correspondant
operateur.get_group_name()

# Synchroniser les groupes Django
operateur.sync_django_groups()

# Vérifier la cohérence des groupes
is_consistent, message = operateur.check_group_consistency()
```

## 🔄 Migration depuis l'ancien système

### Si vous aviez des superviseurs avec l'ancien système
```bash
# 1. Créer le nouveau groupe
python manage.py create_superviseur --create-group

# 2. Assigner les utilisateurs existants
python manage.py create_superviseur --assign-users superviseur1 superviseur2

# 3. Vérifier la migration
python manage.py create_superviseur --list
```

## 📝 Notes importantes

- **Compatibilité** : Le système est rétrocompatible avec l'ancien système de groupes
- **Performance** : Les signaux Django créent automatiquement les profils
- **Sécurité** : Le middleware valide tous les accès
- **Flexibilité** : Possibilité d'avoir plusieurs superviseurs

## 🆘 Support

En cas de problème :
1. Vérifier les logs Django
2. Utiliser la commande `--list` pour diagnostiquer
3. Vérifier les permissions dans l'admin Django
4. Consulter la documentation du middleware

---

**Version** : 1.0  
**Date** : 2025  
**Auteur** : YZ-CMD Team
