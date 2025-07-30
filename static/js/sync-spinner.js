/**
 * Système de spinners et modals de synchronisation centralisé
 * Fichier : sync-spinner.js
 * Utilisation : Gestion des indicateurs de chargement pour la synchronisation
 */

// Variables globales pour le suivi de la synchronisation
let syncStartTime = null;
let syncTimer = null;
let currentStep = 1;
let progressTimer = null;
let currentProgress = 0;

/**
 * Crée un modal de progression simple et dynamique
 */
function createSimpleProgressModal() {
    const modal = document.createElement('div');
    modal.id = 'syncProgressModal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
        backdrop-filter: blur(8px);
    `;
    
    modal.innerHTML = `
        <div style="
            background: white;
            border-radius: 16px;
            padding: 32px;
            max-width: 400px;
            width: 90%;
            text-align: center;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        ">
            <div style="
                width: 80px;
                height: 80px;
                margin: 0 auto 24px;
                border: 4px solid #e5e7eb;
                border-top: 4px solid #0d9488;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            "></div>
            <h3 id="syncTitle" style="
                font-size: 24px;
                font-weight: bold;
                color: #1f2937;
                margin-bottom: 8px;
            ">Synchronisation en cours...</h3>
            <p id="syncMessage" style="
                color: #6b7280;
                margin-bottom: 16px;
            ">Connexion à Google Sheets et traitement des données...</p>
            
            <!-- Barre de progression animée -->
            <div style="
                width: 100%;
                height: 8px;
                background: #e5e7eb;
                border-radius: 4px;
                overflow: hidden;
                margin-bottom: 16px;
                position: relative;
            ">
                <div id="syncProgressBar" style="
                    height: 100%;
                    background: linear-gradient(90deg, #0d9488, #14b8a6, #5eead4);
                    border-radius: 4px;
                    width: 0%;
                    transition: width 0.3s ease-in-out;
                    animation: progressGlow 2s ease-in-out infinite;
                "></div>
            </div>
            
            <!-- Pourcentage de progression -->
            <div id="syncPercentage" style="
                font-size: 18px;
                font-weight: bold;
                color: #0d9488;
                margin-bottom: 16px;
            ">0%</div>
            
            <div style="
                background: #f9fafb;
                border-radius: 8px;
                padding: 16px;
                font-size: 14px;
            ">
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <span style="color: #6b7280;">Enregistrements traités :</span>
                    <span id="recordsCount" style="font-weight: bold; color: #0d9488;">0</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #6b7280;">Temps écoulé :</span>
                    <span id="elapsedTime" style="font-weight: bold; color: #0d9488;">0s</span>
                </div>
            </div>
        </div>
    `;
    
    return modal;
}

/**
 * Affiche le modal de progression de synchronisation avec animations
 */
function showSyncProgressModal() {
    // Essayer d'abord le modal existant
    let modal = document.getElementById('syncProgressModal');
    if (!modal) {
        // Créer un modal simple dynamiquement
        modal = createSimpleProgressModal();
        document.body.appendChild(modal);
    }
    
    modal.style.display = 'flex';
    modal.classList.remove('hidden');
    
    // Réinitialiser l'état du modal
    resetSyncProgress();
    
    // Démarrer les timers
    syncStartTime = Date.now();
    currentProgress = 0;
    syncTimer = setInterval(updateElapsedTime, 1000);
    
    // Démarrer l'animation de la barre de progression
    animateProgressBar();
    
    // Simuler les étapes de progression
    simulateProgressSteps();
}

/**
 * Cache le modal de progression de synchronisation
 */
function hideSyncProgressModal() {
    const modal = document.getElementById('syncProgressModal');
    if (modal) {
        modal.style.display = 'none';
        modal.classList.add('hidden');
        
        // Si c'est un modal créé dynamiquement, le supprimer
        if (modal.parentNode === document.body && modal.innerHTML.includes('style=')) {
            modal.remove();
        }
    }
    
    // Arrêter tous les timers
    if (syncTimer) {
        clearInterval(syncTimer);
        syncTimer = null;
    }
    if (progressTimer) {
        clearInterval(progressTimer);
        progressTimer = null;
    }
}

/**
 * Réinitialise l'état du modal de progression
 */
function resetSyncProgress() {
    currentStep = 1;
    
    const elements = {
        title: document.getElementById('syncTitle'),
        message: document.getElementById('syncMessage'),
        recordsCount: document.getElementById('recordsCount'),
        elapsedTime: document.getElementById('elapsedTime')
    };
    
    if (elements.title) elements.title.textContent = 'Synchronisation en cours...';
    if (elements.message) elements.message.textContent = 'Connexion à Google Sheets et récupération des données...';
    if (elements.recordsCount) elements.recordsCount.textContent = '0';
    if (elements.elapsedTime) elements.elapsedTime.textContent = '0s';
    
    // Réinitialiser les étapes
    for (let i = 1; i <= 4; i++) {
        const step = document.getElementById(`step${i}`);
        if (!step) continue;
        
        const icon = step.querySelector('i');
        const text = step.querySelector('span');
        
        if (i === 1) {
            step.classList.remove('opacity-50');
            if (icon) icon.className = 'fas fa-circle text-teal-500 mr-2 pulse-sync';
            if (text) text.className = 'text-gray-700';
        } else {
            step.classList.add('opacity-50');
            if (icon) icon.className = 'fas fa-circle text-gray-400 mr-2';
            if (text) text.className = 'text-gray-500';
        }
    }
}

/**
 * Met à jour le temps écoulé depuis le début de la synchronisation
 */
function updateElapsedTime() {
    if (syncStartTime) {
        const elapsed = Math.floor((Date.now() - syncStartTime) / 1000);
        const elapsedTimeEl = document.getElementById('elapsedTime');
        if (elapsedTimeEl) {
            elapsedTimeEl.textContent = `${elapsed}s`;
        }
    }
}

/**
 * Anime la barre de progression de manière fluide
 */
function animateProgressBar() {
    const progressBar = document.getElementById('syncProgressBar');
    const progressPercentage = document.getElementById('syncPercentage');
    
    if (!progressBar || !progressPercentage) return;
    
    // Animation progressive de 0% à 100% sur 5 secondes
    const duration = 5000; // 5 secondes
    const interval = 50; // Mise à jour toutes les 50ms
    const increment = (100 / (duration / interval));
    
    progressTimer = setInterval(() => {
        currentProgress += increment;
        
        if (currentProgress >= 100) {
            currentProgress = 100;
            clearInterval(progressTimer);
        }
        
        // Mise à jour de la barre de progression
        progressBar.style.width = currentProgress + '%';
        progressPercentage.textContent = Math.round(currentProgress) + '%';
        
        // Changer le message selon le pourcentage
        const messageEl = document.getElementById('syncMessage');
        if (messageEl) {
            if (currentProgress < 25) {
                messageEl.textContent = 'Connexion à Google Sheets...';
            } else if (currentProgress < 50) {
                messageEl.textContent = 'Récupération des données...';
            } else if (currentProgress < 75) {
                messageEl.textContent = 'Traitement des enregistrements...';
            } else if (currentProgress < 100) {
                messageEl.textContent = 'Finalisation de la synchronisation...';
            } else {
                messageEl.textContent = 'Synchronisation terminée !';
            }
        }
    }, interval);
}

/**
 * Simule la progression des étapes de synchronisation
 */
function simulateProgressSteps() {
    const steps = [
        { delay: 1000, step: 2, message: 'Récupération des données en cours...' },
        { delay: 2500, step: 3, message: 'Traitement des enregistrements...' },
        { delay: 4000, step: 4, message: 'Finalisation de la synchronisation...' }
    ];

    steps.forEach(({ delay, step, message }) => {
        setTimeout(() => {
            if (currentStep < step) {
                activateStep(step);
                const messageEl = document.getElementById('syncMessage');
                if (messageEl) {
                    messageEl.textContent = message;
                }
                currentStep = step;
            }
        }, delay);
    });
}

/**
 * Active une étape spécifique de la synchronisation
 * @param {number} stepNumber - Numéro de l'étape à activer
 */
function activateStep(stepNumber) {
    // Marquer l'étape précédente comme terminée
    if (stepNumber > 1) {
        const prevStep = document.getElementById(`step${stepNumber - 1}`);
        if (prevStep) {
            const prevIcon = prevStep.querySelector('i');
            if (prevIcon) {
                prevIcon.className = 'fas fa-check-circle text-green-500 mr-2';
            }
        }
    }

    // Activer l'étape actuelle
    const currentStepEl = document.getElementById(`step${stepNumber}`);
    if (currentStepEl) {
        currentStepEl.classList.remove('opacity-50');
        const icon = currentStepEl.querySelector('i');
        const text = currentStepEl.querySelector('span');
        if (icon) icon.className = 'fas fa-circle text-teal-500 mr-2 pulse-sync';
        if (text) text.className = 'text-gray-700';
    }
}

/**
 * Marque toutes les étapes comme terminées avec succès
 */
function markAllStepsComplete() {
    for (let i = 1; i <= 4; i++) {
        const step = document.getElementById(`step${i}`);
        if (step) {
            const icon = step.querySelector('i');
            if (icon) {
                icon.className = 'fas fa-check-circle text-green-500 mr-2';
            }
        }
    }
}

/**
 * Affiche un modal de confirmation pour la synchronisation
 * @param {string} message - Message à afficher
 * @param {function} callback - Fonction à appeler lors de la confirmation
 */
function showSyncConfirmModal(message, callback) {
    const modal = createSyncModal('confirm', 'Confirmation de synchronisation', message, callback);
    document.body.appendChild(modal);
    modal.classList.remove('hidden');
}

/**
 * Affiche un message de succès de synchronisation
 * @param {string} message - Message à afficher
 */
function showSyncSuccessMessage(message) {
    const modal = createSyncModal('success', 'Synchronisation réussie', message);
    document.body.appendChild(modal);
    modal.classList.remove('hidden');
    setTimeout(() => {
        if (modal.parentNode) {
            modal.remove();
        }
    }, 3000);
}

/**
 * Affiche un message d'erreur de synchronisation
 * @param {string} message - Message à afficher
 */
function showSyncErrorMessage(message) {
    const modal = createSyncModal('error', 'Erreur de synchronisation', message);
    document.body.appendChild(modal);
    modal.classList.remove('hidden');
    setTimeout(() => {
        if (modal.parentNode) {
            modal.remove();
        }
    }, 5000);
}

/**
 * Affiche un message d'information
 * @param {string} message - Message à afficher
 */
function showSyncInfoMessage(message) {
    const modal = createSyncModal('info', 'Information', message);
    document.body.appendChild(modal);
    modal.classList.remove('hidden');
    setTimeout(() => {
        if (modal.parentNode) {
            modal.remove();
        }
    }, 3000);
}

/**
 * Crée un modal de synchronisation avec des styles appropriés
 * @param {string} type - Type de modal (success, error, info, confirm)
 * @param {string} title - Titre du modal
 * @param {string} message - Message du modal
 * @param {function} callback - Fonction callback pour les confirmations
 */
function createSyncModal(type, title, message, callback = null) {
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 flex items-center justify-center z-50';
    modal.style.backgroundColor = 'rgba(0, 0, 0, 0.2)';
    modal.style.backdropFilter = 'blur(8px)';
    modal.style.webkitBackdropFilter = 'blur(8px)';
    
    const syncColors = {
        success: { 
            bg: 'bg-gradient-to-br from-green-50 to-emerald-50', 
            icon: 'text-green-600', 
            button: 'bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700',
            border: 'border-green-200'
        },
        error: { 
            bg: 'bg-gradient-to-br from-red-50 to-pink-50', 
            icon: 'text-red-600', 
            button: 'bg-gradient-to-r from-red-600 to-pink-600 hover:from-red-700 hover:to-pink-700',
            border: 'border-red-200'
        },
        info: { 
            bg: 'bg-gradient-to-br from-blue-50 to-cyan-50', 
            icon: 'text-blue-600', 
            button: 'bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700',
            border: 'border-blue-200'
        },
        confirm: { 
            bg: 'bg-gradient-to-br from-teal-50 to-cyan-50', 
            icon: 'text-teal-600', 
            confirmBtn: 'bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-700 hover:to-cyan-700',
            cancelBtn: 'bg-gradient-to-r from-gray-500 to-gray-600 hover:from-gray-600 hover:to-gray-700',
            border: 'border-teal-200'
        }
    };
    
    const iconClass = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle', 
        info: 'fa-info-circle',
        confirm: 'fa-sync-alt'
    };
    
    if (type === 'confirm') {
        modal.innerHTML = `
            <div class="${syncColors[type].bg} ${syncColors[type].border} border-2 rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 transform transition-all duration-300">
                <div class="text-center mb-6">
                    <div class="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-teal-100 mb-4">
                        <i class="fas ${iconClass[type]} ${syncColors[type].icon} text-3xl"></i>
                    </div>
                    <h3 class="text-2xl font-bold text-gray-800 mb-2">${title}</h3>
                    <div class="text-gray-600 whitespace-pre-wrap text-left">${message}</div>
                </div>
                <div class="flex justify-center gap-4">
                    <button onclick="confirmSyncAction()" class="${syncColors[type].confirmBtn} text-white font-bold py-3 px-6 rounded-lg transition duration-300 transform hover:scale-105 shadow-lg">
                        <i class="fas fa-check mr-2"></i>Confirmer
                    </button>
                    <button onclick="this.closest('.fixed').remove()" class="${syncColors[type].cancelBtn} text-white font-bold py-3 px-6 rounded-lg transition duration-300 transform hover:scale-105 shadow-lg">
                        <i class="fas fa-times mr-2"></i>Annuler
                    </button>
                </div>
            </div>
        `;
        
        // Stocker le callback pour l'utiliser plus tard
        window.currentSyncCallback = callback;
    } else {
        const bgClass = type === 'success' ? 'bg-green-100' : type === 'error' ? 'bg-red-100' : 'bg-blue-100';
        modal.innerHTML = `
            <div class="${syncColors[type].bg} ${syncColors[type].border} border-2 rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 transform transition-all duration-300">
                <div class="text-center mb-6">
                    <div class="mx-auto flex items-center justify-center h-16 w-16 rounded-full ${bgClass} mb-4">
                        <i class="fas ${iconClass[type]} ${syncColors[type].icon} text-3xl"></i>
                    </div>
                    <h3 class="text-2xl font-bold text-gray-800 mb-2">${title}</h3>
                    <div class="text-gray-600 whitespace-pre-wrap text-left">${message}</div>
                </div>
                <div class="flex justify-center">
                    <button onclick="this.closest('.fixed').remove()" class="${syncColors[type].button} text-white font-bold py-3 px-6 rounded-lg transition duration-300 transform hover:scale-105 shadow-lg">
                        <i class="fas fa-check mr-2"></i>OK
                    </button>
                </div>
            </div>
        `;
    }
    
    return modal;
}

/**
 * Confirme l'action de synchronisation
 */
function confirmSyncAction() {
    // Fermer d'abord le modal de confirmation
    const confirmModal = document.querySelector('.fixed');
    if (confirmModal) {
        confirmModal.remove();
    }
    
    // Puis exécuter le callback (qui va ouvrir le modal de progression)
    if (window.currentSyncCallback) {
        window.currentSyncCallback();
        window.currentSyncCallback = null;
    }
}

/**
 * Fonction principale de synchronisation avec gestion complète des spinners
 * @param {number} configId - ID de la configuration à synchroniser
 * @param {string} syncUrl - URL de synchronisation (optionnel, par défaut /synchronisation/sync-now/)
 */
function syncNowWithSpinner(configId, syncUrl = null) {
    if (!syncUrl) {
        syncUrl = `/synchronisation/sync-now/${configId}/`;
    }
    
    // Vérification de la disponibilité du modal - si non trouvé, on le crée
    let modalTest = document.getElementById('syncProgressModal');
    if (!modalTest) {
        console.warn('⚠️ Modal syncProgressModal non trouvé, création automatique...');
        modalTest = createSimpleProgressModal();
        document.body.appendChild(modalTest);
    }
    
    showSyncConfirmModal('Voulez-vous lancer la synchronisation maintenant ?', function() {
        const csrftoken = getCookie('csrftoken');
        

        // Afficher le modal de progression
        showSyncProgressModal();

        fetch(syncUrl, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            // Simuler quelques secondes pour voir l'animation complète
            setTimeout(() => {
                hideSyncProgressModal();
                
                if (data.success) {
                    // Marquer toutes les étapes comme terminées
                    markAllStepsComplete();
                    
                    const message = data.records_imported 
                        ? `Synchronisation réussie ! ${data.records_imported} enregistrements importés.`
                        : 'Synchronisation réussie !';
                    
                    showSyncSuccessMessage(message);
                    
                    // Recharger la page après 2 secondes
                    setTimeout(() => location.reload(), 2000);
                } else {
                    const errorMsg = data.error || 'Erreur inconnue lors de la synchronisation';
                    showSyncErrorMessage('Erreur lors de la synchronisation : ' + errorMsg);
                }
            }, 1000);
        })
        .catch(error => {
            hideSyncProgressModal();
            showSyncErrorMessage('Erreur lors de la synchronisation : ' + error.message);
            console.error('Erreur de synchronisation:', error);
        });
    });
}

/**
 * Récupère le token CSRF depuis un input caché ou un cookie
 * @param {string} name - Nom du cookie (par défaut 'csrftoken')
 */
function getCookie(name = 'csrftoken') {
    // Essayer d'abord depuis un input caché
    const csrf_input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (csrf_input) {
        return csrf_input.value;
    }
    
    // Fallback vers les cookies
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Fonction wrapper pour maintenir la compatibilité avec les templates existants
 */
function syncNow(configId) {
    syncNowWithSpinner(configId);
}

/**
 * Test de connexion à Google Sheets pour une configuration
 * @param {number} configId - ID de la configuration à tester
 */
function testConnectionWithSpinner(configId) {
    showSyncInfoMessage('Test de connexion en cours...');
    
    const csrftoken = getCookie('csrftoken');
    
    fetch(`/synchronisation/configs/test/${configId}/`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        // Fermer le modal de chargement
        const existingModals = document.querySelectorAll('.fixed');
        existingModals.forEach(modal => modal.remove());
        
        if (data.success) {
            const details = data.details;
            const message = `✅ Connexion réussie !

📊 Feuille: "${details.spreadsheet_title}"
📋 Onglet: "${details.worksheet_name}"  
📈 Lignes: ${details.total_rows}
📋 Colonnes: ${details.total_columns}
${details.headers.length > 0 ? `🏷️ En-têtes: ${details.headers.join(', ')}` : ''}
${details.has_data ? '✅ Contient des données' : '⚠️ Aucune donnée trouvée'}`;
            
            showSyncSuccessMessage(message);
        } else {
            let errorMessage = `❌ ${data.error}`;
            if (data.details && Array.isArray(data.details)) {
                errorMessage += '\n\n💡 Suggestions:\n' + data.details.map(detail => `• ${detail}`).join('\n');
            }
            showSyncErrorMessage(errorMessage);
        }
    })
    .catch(error => {
        // Fermer le modal de chargement
        const existingModals = document.querySelectorAll('.fixed');
        existingModals.forEach(modal => modal.remove());
        
        showSyncErrorMessage('Erreur réseau lors du test de connexion. Vérifiez votre connexion internet.');
        console.error('Erreur:', error);
    });
}

// Ajout d'un style CSS pour les animations si pas déjà présent
if (!document.querySelector('#sync-spinner-styles')) {
    const style = document.createElement('style');
    style.id = 'sync-spinner-styles';
    style.textContent = `
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        @keyframes progressBar {
            0% { width: 0%; }
            50% { width: 70%; }
            100% { width: 100%; }
        }

        .spinner-sync {
            animation: spin 1s linear infinite;
        }

        .pulse-sync {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        .progress-bar-sync {
            animation: progressBar 3s ease-in-out infinite;
        }

        .sync-modal-backdrop {
            backdrop-filter: blur(10px);
            background: rgba(0, 0, 0, 0.3);
        }

        .sync-modal-content {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        @keyframes progressGlow {
            0%, 100% { box-shadow: 0 0 5px rgba(13, 148, 136, 0.5); }
            50% { box-shadow: 0 0 20px rgba(13, 148, 136, 0.8), 0 0 30px rgba(13, 148, 136, 0.3); }
        }

        @keyframes progressSlide {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
    `;
    document.head.appendChild(style);
}

console.log('✅ Système de spinners de synchronisation chargé avec succès'); 