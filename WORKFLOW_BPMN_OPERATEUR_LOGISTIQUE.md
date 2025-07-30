# 📋 WORKFLOW BPMN - OPÉRATEUR LOGISTIQUE YZ-CMD

## Vue d'Ensemble du Processus

**Nom du Processus :** Livraison et Gestion Logistique des Commandes  
**Acteur Principal :** Opérateur Logistique  
**Objectif :** Assurer la livraison des commandes préparées, gérer les retours et garantir la traçabilité des expéditions  
**Durée Moyenne :** 10-60 minutes par tournée (selon volume et distance)

---

## 🔄 PROCESSUS PRINCIPAL : LIVRAISON D'UNE COMMANDE

### **[ÉVÉNEMENT DE DÉBUT]**
**Déclencheur :** Commande préparée disponible pour expédition  
**État Initial :** Commande en statut "Préparée" ou "À livrer"  
**Pré-conditions :**
- Opérateur logistique connecté
- Colis physiquement disponible
- Documents de transport imprimés

---

### **[TÂCHE 1]** Organisation de la Tournée de Livraison
**Responsable :** Opérateur Logistique  
**Durée :** 5-15 minutes  
**Actions :**
1. Consulter la liste des colis à livrer
2. Planifier l'itinéraire optimal
3. Préparer les documents nécessaires
4. Charger les colis dans le véhicule

**Données d'Entrée :**
- Liste des commandes à livrer
- Adresses clients
- Contraintes de temps

**Données de Sortie :**
- Planning de tournée
- Colis prêts à être livrés

---

### **[TÂCHE 2]** Livraison au Client
**Responsable :** Opérateur Logistique  
**Durée :** 5-30 minutes par livraison  
**Actions :**
1. Se rendre à l'adresse du client
2. Contacter le client à l'arrivée
3. Remettre le colis et obtenir la signature ou confirmation
4. Encaisser le paiement si nécessaire (contre-remboursement)
5. Documenter la livraison dans le système

**Données de Sortie :**
- Statut de livraison (livrée, partielle, échec)
- Preuve de livraison (signature, photo)
- Paiement encaissé

---

### **[PASSERELLE DE DÉCISION 1]** Livraison Réussie ?
**Question :** Le colis a-t-il été remis au client ?

#### **[BRANCHE OUI]** Livraison Complète
**Action :** Passer à la clôture de la livraison

#### **[BRANCHE NON]** Livraison Échouée ou Partielle
**Action :** Déclencher le sous-processus de gestion des échecs ou retours

---

### **[SOUS-PROCESSUS]** Gestion des Échecs et Retours
**Déclencheur :** Livraison échouée ou partielle  
**Responsable :** Opérateur Logistique

#### **[TÂCHE 3A]** Tentative de Relivraison ou Contact
**Durée :** 2-10 minutes  
**Actions :**
1. Recontacter le client (téléphone, SMS)
2. Proposer un nouveau créneau
3. Documenter la tentative

#### **[PASSERELLE DE DÉCISION 2A]** Relivraison Possible ?
- **[OUI]** → Programmer une nouvelle livraison
- **[NON]** → Passer à la gestion du retour

#### **[TÂCHE 3B]** Gestion du Retour
**Actions :**
- Récupérer le colis
- Documenter le motif du retour
- Mettre à jour le statut dans le système
- Informer les équipes concernées

---

### **[TÂCHE 4]** Clôture de la Livraison
**Responsable :** Opérateur Logistique  
**Durée :** 1-3 minutes  
**Actions :**
1. Mettre à jour le statut de la commande (livrée, retour, partielle)
2. Générer la preuve de livraison
3. Remettre les paiements collectés
4. Documenter les anomalies éventuelles

**Données Système Mises à Jour :**
- Statut commande
- Preuve de livraison
- Paiement enregistré

---

### **[ÉVÉNEMENT DE FIN PRINCIPAL]**
**Résultat :** Commande livrée, retournée ou à relivrer  
**Statut Final :** "Livrée", "Retour", "À relivrer"  
**Livrables :**
- Colis livré ou retourné
- Documentation complète
- Paiement traité

---

## 🔄 PROCESSUS PARALLÈLES ET CONNEXES

### **[PROCESSUS PARALLÈLE 1]** Suivi des Tournées
**Déclencheur :** Début de chaque tournée  
**Actions :**
- Suivi GPS des véhicules
- Mise à jour en temps réel des statuts
- Notification des retards

### **[PROCESSUS PARALLÈLE 2]** Gestion des Paiements
**Déclencheur :** Livraison contre-remboursement  
**Actions :**
- Encaissement sécurisé
- Remise des fonds à l'administration
- Suivi des écarts

---

## 📊 INDICATEURS DE PERFORMANCE (KPI)

### **Indicateurs de Productivité :**
- Nombre de colis livrés par tournée
- Temps moyen de livraison
- Respect des délais
- Taux de relivraison

### **Indicateurs de Qualité :**
- Taux de retours
- Taux de satisfaction client
- Précision des statuts
- Gestion des paiements

---

## 🚨 GESTION DES EXCEPTIONS ET ESCALADES

### **Exception 1 :** Client absent
**Actions :**
- Programmer une relivraison
- Notifier le client et le superviseur

### **Exception 2 :** Problème de paiement
**Actions :**
- Noter l'incident
- Informer l'administration
- Suspendre la livraison si nécessaire

### **Exception 3 :** Incident de transport
**Actions :**
- Documenter l'incident
- Prendre des mesures de sécurité
- Informer la logistique

---

## 🔄 PROCESSUS DE RETOUR ET AMÉLIORATION CONTINUE

### **Révision Quotidienne :**
1. Analyse des livraisons et retours
2. Identification des difficultés
3. Proposition d'améliorations
4. Planification des actions correctives

### **Révision Hebdomadaire :**
1. Analyse des tournées
2. Évaluation des itinéraires
3. Formation continue
4. Ajustement des objectifs

### **Révision Mensuelle :**
1. Bilan des performances
2. Identification des axes de progrès
3. Formation approfondie
4. Partage des bonnes pratiques

---

**[FIN DU WORKFLOW BPMN]**

*Ce workflow constitue le processus standard de livraison. Des variations peuvent s'appliquer selon la zone, le type de colis ou les situations exceptionnelles.* 