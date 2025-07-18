# 📦 Guide de la Livraison Partielle - YZ-CMD

## 🎯 Objectif

Le système de **Livraison Partielle** permet aux opérateurs logistiques de gérer les situations où certains articles d'une commande ne peuvent pas être livrés au client (défaut, indisponibilité, changement demandé, etc.) tout en livrant les articles disponibles.

## 🔄 Workflow de la Livraison Partielle

### **1. Déclenchement**
- L'opérateur logistique constate qu'il ne peut pas livrer tous les articles d'une commande
- Il clique sur le bouton **"Livraison Partielle"** dans l'interface de détail de commande

### **2. Sélection des Articles**
- **Interface intuitive** : Modale avec sélection visuelle des articles
- **Articles à livrer** : Cases à cocher avec quantités ajustables
- **Articles à renvoyer** : Affichage automatique des articles non sélectionnés
- **Résumé en temps réel** : Statistiques et valeurs mises à jour dynamiquement

### **3. Traitement Automatique**
- **Commande originale** : Mise à jour avec les articles livrés uniquement
- **Nouvelle commande** : Création automatique pour les articles renvoyés
- **États mis à jour** : Traçabilité complète des actions

## 🎨 Interface Utilisateur

### **Modale de Livraison Partielle**

#### **Section "Articles à Livrer au Client"**
- ✅ **Cases à cocher** : Sélection des articles à livrer
- 📊 **Quantités ajustables** : Possibilité de livrer une partie seulement
- 💰 **Prix affichés** : Informations complètes sur chaque article
- 🎨 **Design vert** : Couleur positive pour les articles livrés

#### **Section "Articles à Renvoyer en Préparation"**
- 🔄 **Affichage automatique** : Articles non sélectionnés
- 📦 **Détails complets** : Quantités, prix, valeurs
- 🎨 **Design orange** : Couleur d'alerte pour les articles renvoyés

#### **Résumé de la Livraison Partielle**
- 📊 **Statistiques** : Nombre d'articles livrés/renvoyés
- 💰 **Valeur livrée** : Montant total des articles livrés
- ✅ **Validation** : Bouton activé uniquement si configuration valide

## 🔧 Fonctionnalités Techniques

### **Validation Automatique**
- ✅ **Au moins un article livré** : Obligatoire
- ✅ **Au moins un article renvoyé** : Obligatoire pour une livraison partielle
- ✅ **Commentaire obligatoire** : Explication des raisons
- ✅ **Quantités cohérentes** : Respect des quantités maximales

### **Gestion des Données**
- 🔄 **Transactions atomiques** : Intégrité des données garantie
- 📝 **Traçabilité complète** : Opérations enregistrées
- 🔗 **Liens entre commandes** : Relation commande originale ↔ commande de renvoi

### **Création de Commandes**
- **Commande originale** : Mise à jour avec articles livrés
- **Commande de renvoi** : Nouvelle commande avec préfixe "RENVOI-"
- **États appropriés** : "Livrée Partiellement" et "Non affectée"

## 📋 Cas d'Usage Typiques

### **1. Article Défectueux**
```
Situation : Un article présente un défaut de fabrication
Action : 
- Livrer les autres articles
- Renvoyer l'article défectueux en préparation
- Créer une commande de remplacement
```

### **2. Indisponibilité Temporaire**
```
Situation : Un article n'est plus en stock
Action :
- Livrer les articles disponibles
- Renvoyer l'article indisponible
- Attendre la réapprovisionnement
```

### **3. Changement Demandé par le Client**
```
Situation : Le client souhaite un autre article
Action :
- Livrer les articles non concernés
- Renvoyer l'article à changer
- Préparer l'article de remplacement
```

### **4. Livraison Partielle de Quantité**
```
Situation : Seule une partie de la quantité peut être livrée
Action :
- Livrer la quantité disponible
- Renvoyer la quantité manquante
- Programmer une livraison complémentaire
```

## 🚀 Avantages du Système

### **Pour les Opérateurs Logistiques**
- ✅ **Interface intuitive** : Sélection visuelle simple
- ✅ **Validation automatique** : Prévention des erreurs
- ✅ **Temps réel** : Résumé mis à jour instantanément
- ✅ **Traçabilité** : Historique complet des actions

### **Pour la Gestion**
- 📊 **Statistiques précises** : Suivi des livraisons partielles
- 🔄 **Workflow automatisé** : Création automatique des commandes de renvoi
- 📝 **Documentation** : Commentaires obligatoires pour traçabilité
- 🎯 **Efficacité** : Réduction du temps de traitement

### **Pour les Clients**
- ⚡ **Livraison rapide** : Articles disponibles livrés immédiatement
- 🔄 **Suivi transparent** : Articles manquants traités séparément
- 💬 **Communication** : Raisons de la livraison partielle documentées

## 🔍 Suivi et Monitoring

### **Liste des Commandes Livrées Partiellement**
- 📋 **Vue dédiée** : Interface de suivi spécifique
- 🔍 **Recherche** : Filtrage par critères
- 📊 **Statistiques** : Métriques de performance

### **Commandes de Renvoi**
- 🔗 **Liens automatiques** : Relation avec commande originale
- 📝 **Commentaires** : Raisons du renvoi documentées
- 🔄 **Workflow** : Traitement par les opérateurs de préparation

## ⚠️ Points d'Attention

### **Validation des Données**
- ✅ **Quantités cohérentes** : Respect des quantités maximales
- ✅ **Articles valides** : Vérification de l'existence des articles
- ✅ **États appropriés** : Seules les commandes en livraison éligibles

### **Gestion des Erreurs**
- 🔄 **Transactions sécurisées** : Rollback en cas d'erreur
- 💬 **Messages clairs** : Explications des erreurs
- 🔧 **Récupération** : Possibilité de recommencer

## 🎯 Bonnes Pratiques

### **Pour les Opérateurs**
1. **Vérifier les articles** avant de déclencher une livraison partielle
2. **Documenter précisément** les raisons dans le commentaire
3. **Valider les quantités** avant confirmation
4. **Informer le client** des articles non livrés

### **Pour la Gestion**
1. **Former les opérateurs** à l'utilisation du système
2. **Surveiller les statistiques** de livraisons partielles
3. **Analyser les causes** récurrentes pour améliorer le processus
4. **Maintenir la traçabilité** des opérations

## 🔮 Évolutions Futures

### **Fonctionnalités Prévues**
- 📱 **Notifications** : Alertes automatiques aux clients
- 📊 **Tableaux de bord** : Métriques avancées
- 🔄 **Intégration** : Liaison avec le système de SAV
- 📈 **Analytics** : Analyse prédictive des livraisons partielles

---

*Ce guide est mis à jour régulièrement pour refléter les évolutions du système.* 