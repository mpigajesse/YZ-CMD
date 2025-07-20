# 🛠️ Guide de Dépannage SAV

## 🚨 Problèmes Identifiés et Solutions

### **1. Erreur "Cette commande n'est pas retournée"**

**💡 Problème :** 
- Message d'erreur affiché lors de la tentative de création d'une commande SAV
- La validation était trop restrictive (seulement pour les commandes "Retournées")

**🔧 Solution Appliquée :**
```python
# AVANT (restrictif)
if commande_originale.etat_actuel.enum_etat.libelle != 'Retournée':
    return JsonResponse({'error': 'Cette commande n\'est pas retournée.'})

# APRÈS (corrigé)
etats_sav_autorises = ['Retournée', 'Livrée', 'Livrée Partiellement', 'Livrée avec changement']
if commande_originale.etat_actuel.enum_etat.libelle not in etats_sav_autorises:
    return JsonResponse({'error': f'Cette commande ne peut pas avoir de SAV. État actuel: {etat_actuel}'})
```

**✅ États Autorisés pour SAV :**
- ✅ **Retournée** : Commande retournée par le client
- ✅ **Livrée** : Commande livrée avec articles défectueux
- ✅ **Livrée Partiellement** : Commande partiellement livrée
- ✅ **Livrée avec changement** : Commande livrée avec modifications

### **2. Erreur JavaScript "Incohérence dans les sous-totaux"**

**💡 Problème :**
- Erreur dans la fonction `validerCalculs()` lors de l'accès aux propriétés des éléments DOM
- Gestion d'erreur insuffisante pour les éléments manquants

**🔧 Solution Appliquée :**
```javascript
// AVANT (vulnérable aux erreurs)
const prix = parseFloat(prixElement.textContent.replace(' DH', ''));

// APRÈS (robuste)
const prixText = prixElement.textContent || prixElement.innerText || '';
const prix = parseFloat(prixText.replace(' DH', '').replace(',', '.').trim()) || 0;
if (!isNaN(sousTotal) && isFinite(sousTotal)) {
    totalArticlesCalcule += sousTotal;
}
```

**🛡️ Améliorations :**
- Gestion des éléments DOM manquants
- Validation des valeurs numériques
- Try-catch pour éviter les erreurs critiques
- Messages d'erreur plus informatifs

### **3. Erreur "A listener indicated an asynchronous response"**

**💡 Problème :**
- Extension de navigateur qui interfère avec les API calls
- Channel de message fermé prématurément

**🔧 Solutions :**
1. **Ajout de timeouts appropriés** dans les requêtes AJAX
2. **Gestion d'erreur améliorée** pour les réponses asynchrones
3. **Validation des réponses** avant traitement

## 🧪 Scripts de Test

### **1. Test Global des Validations SAV**
```bash
python test_validations_sav.py
```

**Vérifications effectuées :**
- ✅ Commandes livrées partiellement et leur éligibilité SAV
- ✅ Commandes retournées et leurs validations
- ✅ Cohérence des calculs de prix
- ✅ Opérateurs logistiques actifs
- ✅ Détection d'anomalies SAV

### **2. Test des Affectations (Existant)**
```bash
python test_affectation_futures.py
```

**Vérifications supplémentaires :**
- ✅ Commandes renvoyées correctement affectées
- ✅ Commandes de livraison partielle
- ✅ Surveillance des anomalies

## 🔧 Procédures de Dépannage

### **Si "Cette commande n'est pas retournée" apparaît :**

1. **Vérifier l'état de la commande :**
   ```python
   commande = Commande.objects.get(id=commande_id)
   print(f"État actuel: {commande.etat_actuel.enum_etat.libelle}")
   ```

2. **États autorisés pour SAV :**
   - Si la commande est en état `Livrée Partiellement` → ✅ Autorisé
   - Si la commande est en état `Livrée` → ✅ Autorisé
   - Si la commande est en état `Retournée` → ✅ Autorisé
   - Si la commande est en état `Livrée avec changement` → ✅ Autorisé

3. **Si l'état n'est pas autorisé :**
   - Changer l'état via l'interface logistique
   - Ou corriger l'état manuellement via l'admin Django

### **Si erreurs de calculs JavaScript :**

1. **Vérifier les éléments DOM :**
   ```javascript
   // Dans la console du navigateur
   console.log(document.getElementById('total-commande'));
   console.log(document.querySelectorAll('.article-card'));
   ```

2. **Réexécuter la validation :**
   ```javascript
   // Dans la console du navigateur
   validerCalculs();
   ```

3. **Si erreurs persistantes :**
   - Recharger la page
   - Vider le cache du navigateur
   - Vérifier les extensions de navigateur

### **Si erreurs de listener asynchrone :**

1. **Identifier l'extension problématique :**
   - Désactiver temporairement les extensions
   - Tester en mode navigation privée

2. **Vérifier les requêtes réseau :**
   - Onglet "Network" des outils de développement
   - Chercher les requêtes qui échouent

## 🛡️ Mesures Préventives

### **1. Validation Côté Serveur Renforcée**
```python
def valider_eligibilite_sav(commande):
    """Valider qu'une commande peut avoir un SAV"""
    etats_autorises = ['Retournée', 'Livrée', 'Livrée Partiellement', 'Livrée avec changement']
    
    if not commande.etat_actuel:
        return False, "Commande sans état actuel"
    
    if commande.etat_actuel.enum_etat.libelle not in etats_autorises:
        return False, f"État '{commande.etat_actuel.enum_etat.libelle}' non autorisé pour SAV"
    
    return True, "Commande éligible pour SAV"
```

### **2. Validation Côté Client Améliorée**
```javascript
function validerEligibiliteSAV() {
    const etatActuel = document.querySelector('[data-etat-commande]')?.dataset.etatCommande;
    const etatsAutorises = ['Retournée', 'Livrée', 'Livrée Partiellement', 'Livrée avec changement'];
    
    if (!etatActuel || !etatsAutorises.includes(etatActuel)) {
        showNotification('❌ Cette commande ne peut pas avoir de SAV', 'error');
        return false;
    }
    
    return true;
}
```

### **3. Surveillance Continue**
```python
# Dans operatLogistic/views.py - à ajouter à la surveillance
def surveiller_sav():
    """Surveiller les anomalies SAV"""
    anomalies = []
    
    # Commandes éligibles SAV non traitées
    commandes_eligibles = Commande.objects.filter(
        etats__enum_etat__libelle__in=['Retournée', 'Livrée', 'Livrée Partiellement'],
        etats__date_fin__isnull=True
    ).exclude(
        num_cmd__startswith='SAV-'
    )
    
    # Détecter les commandes anciennes sans SAV
    from datetime import timedelta
    seuil_anciennete = timezone.now() - timedelta(days=7)
    
    for commande in commandes_eligibles:
        if commande.etat_actuel.date_debut < seuil_anciennete:
            anomalies.append({
                'type': 'SAV_NON_TRAITE',
                'commande_id': commande.id,
                'message': f'Commande {commande.id_yz} éligible SAV depuis > 7 jours'
            })
    
    return anomalies
```

## 📊 Métriques de Surveillance

### **Indicateurs Clés :**
1. **Taux d'erreur SAV** : Nombre d'erreurs / Tentatives SAV
2. **Commandes éligibles non traitées** : Commandes > 7 jours sans SAV
3. **Temps de traitement SAV** : Délai entre éligibilité et création SAV
4. **Erreurs JavaScript** : Fréquence des erreurs de calcul

### **Alertes Automatiques :**
- ⚠️ Erreur SAV > 5% des tentatives
- ⚠️ Commande éligible SAV non traitée > 24h
- ⚠️ Erreur JavaScript > 10 par jour
- ⚠️ Incohérence de calculs détectée

## ✅ Checklist de Vérification

### **Avant Déploiement :**
- [ ] Tester la création SAV pour chaque état autorisé
- [ ] Vérifier les calculs JavaScript sans erreur
- [ ] Valider les requêtes AJAX sans timeout
- [ ] Tester en navigation privée
- [ ] Exécuter les scripts de validation

### **Surveillance Post-Déploiement :**
- [ ] Surveiller les logs d'erreur SAV
- [ ] Vérifier les métriques de performance
- [ ] Contrôler les commandes éligibles SAV
- [ ] Valider les calculs en production

---

**🎯 Résultat Attendu :** Zéro erreur SAV et système robuste pour tous les cas d'usage ! 