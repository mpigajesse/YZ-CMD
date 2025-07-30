/**
 * Gestion améliorée des synchronisations avec notifications détaillées
 * Support du cas spécial : resynchronisation sans nouvelles commandes
 */

class SyncEnhanced {
    constructor() {
        this.isVisible = false;
        this.initModal();
    }

    initModal() {
        // Créer le modal de synchronisation s'il n'existe pas
        if (!document.getElementById('syncModal')) {
            this.createSyncModal();
        }
    }

    createSyncModal() {
        const modalHTML = `
            <div id="syncModal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50 sync-modal-backdrop">
                <div class="flex items-center justify-center min-h-screen p-4">
                    <div class="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 sync-modal-content transform transition-all">
                        <div class="text-center">
                            <div class="mb-4">
                                <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-100">
                                    <i id="syncIcon" class="fas fa-sync-alt text-2xl text-blue-600 spinner-sync"></i>
                                </div>
                            </div>
                            <h3 id="syncTitle" class="text-lg font-semibold text-gray-900 mb-2">Synchronisation en cours...</h3>
                            <p id="syncMessage" class="text-gray-600 mb-4">Vérification des nouvelles commandes en arrière-plan</p>
                            <div class="w-full bg-gray-200 rounded-full h-2 mb-4">
                                <div id="syncProgress" class="bg-blue-600 h-2 rounded-full progress-bar-sync" style="width: 0%"></div>
                            </div>
                            <div id="syncDetails" class="text-sm text-gray-500"></div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    show() {
        this.isVisible = true;
        const modal = document.getElementById('syncModal');
        const icon = document.getElementById('syncIcon');
        const title = document.getElementById('syncTitle');
        const message = document.getElementById('syncMessage');
        const progress = document.getElementById('syncProgress');
        
        // Vérifier que tous les éléments existent avant de les manipuler
        if (!modal) {
            console.error('Modal de synchronisation non trouvé, création du modal...');
            this.createSyncModal();
            // Récupérer les éléments après création
            const newModal = document.getElementById('syncModal');
            const newIcon = document.getElementById('syncIcon');
            const newTitle = document.getElementById('syncTitle');
            const newMessage = document.getElementById('syncMessage');
            const newProgress = document.getElementById('syncProgress');
            
            if (newModal && newIcon && newTitle && newMessage && newProgress) {
                // Reset état initial
                newIcon.className = 'fas fa-sync-alt text-2xl text-blue-600 spinner-sync';
                newTitle.textContent = 'Synchronisation en cours...';
                newMessage.textContent = 'Vérification des nouvelles commandes en arrière-plan';
                newProgress.style.width = '0%';
                
                newModal.classList.remove('hidden');
                setTimeout(() => {
                    newProgress.style.width = '30%';
                }, 500);
            }
            return;
        }
        
        // Reset état initial avec vérifications de nullité
        if (icon) {
            icon.className = 'fas fa-sync-alt text-2xl text-blue-600 spinner-sync';
        }
        if (title) {
            title.textContent = 'Synchronisation en cours...';
        }
        if (message) {
            message.textContent = 'Vérification des nouvelles commandes en arrière-plan';
        }
        if (progress) {
            progress.style.width = '0%';
        }
        
        modal.classList.remove('hidden');
        setTimeout(() => {
            if (progress) {
                progress.style.width = '30%';
            }
        }, 500);
    }

    updateProgress(percentage, message) {
        const progress = document.getElementById('syncProgress');
        const details = document.getElementById('syncDetails');
        
        if (progress) {
            progress.style.width = percentage + '%';
        }
        if (message && details) {
            details.textContent = message;
        }
    }

    showResult(result) {
        const icon = document.getElementById('syncIcon');
        const title = document.getElementById('syncTitle');
        const message = document.getElementById('syncMessage');
        const progress = document.getElementById('syncProgress');
        const details = document.getElementById('syncDetails');

        // Analyser le type de résultat
        const isNoNewOrders = result.new_orders_created === 0 && result.duplicate_orders_found > 0;
        const isSuccess = result.success || result.new_orders_created > 0;
        const hasUpdates = result.existing_orders_updated > 0;

        // Terminer la barre de progression
        if (progress) {
            progress.style.width = '100%';
        }

        // Afficher les statistiques détaillées dans le modal
        this.showDetailedStats(result);

        setTimeout(() => {
            // Configurer l'affichage selon le type de résultat
            if (isNoNewOrders) {
                // Cas spécial : Aucune nouvelle commande
                this.showNoNewOrdersNotification(result);
            } else if (isSuccess) {
                // Cas de succès avec nouvelles commandes
                this.showSuccessNotification(result);
            } else {
                // Cas d'erreur
                this.showErrorNotification(result);
            }

            // Afficher les détails
            if (details) {
                details.innerHTML = this.formatDetails(result);
            }

            // Auto-fermeture après délai (supprimé ici car géré dans syncConfig)
            // setTimeout(() => {
            //     this.hide();
            // }, isNoNewOrders ? 5000 : 4000);

        }, 1000);
    }

    showDetailedStats(result) {
        // Mise à jour des statistiques dans le modal existant ou dans le template _sync_progress_modal.html
        this.updateStatElement('newOrdersDiv', 'newOrdersCount', result.new_orders_created);
        this.updateStatElement('updatesDiv', 'updatesCount', result.existing_orders_updated);
        this.updateStatElement('duplicatesDiv', 'duplicatesCount', result.duplicate_orders_found);
        this.updateStatElement('skippedDiv', 'skippedCount', result.existing_orders_skipped);

        // Afficher la section statistiques si au moins une valeur > 0
        const syncStats = document.getElementById('syncStats');
        if (syncStats && (result.new_orders_created > 0 || result.existing_orders_updated > 0 || result.duplicate_orders_found > 0 || result.existing_orders_skipped > 0)) {
            syncStats.classList.remove('hidden');
        }
    }

    updateStatElement(divId, countId, value) {
        const div = document.getElementById(divId);
        const count = document.getElementById(countId);
        
        if (div && count && value > 0) {
            count.textContent = value;
            div.classList.remove('hidden');
        }
    }

    showNoNewOrdersNotification(result) {
        const icon = document.getElementById('syncIcon');
        const title = document.getElementById('syncTitle');
        const message = document.getElementById('syncMessage');
        const progress = document.getElementById('syncProgress');

        // Configuration pour le cas "Aucune nouvelle commande"
        if (icon) {
            icon.className = 'fas fa-info-circle text-2xl text-blue-600';
        }
        if (title) {
            title.textContent = 'Resynchronisation terminée';
        }
        if (message) {
            message.innerHTML = `
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                    <div class="flex items-center text-blue-800 mb-2">
                        <i class="fas fa-shield-alt mr-2"></i>
                        <strong>Aucune nouvelle commande trouvée</strong>
                    </div>
                    <div class="text-sm text-blue-700">
                        📋 ${result.duplicate_orders_found} commandes existantes détectées dans la feuille
                    </div>
                    <div class="text-xs text-blue-600 mt-2">
                        🔍 Toutes les commandes de la feuille existent déjà dans le système
                    </div>
                </div>
            `;
        }
        if (progress) {
            progress.className = 'bg-blue-600 h-2 rounded-full transition-all';
        }

        // Afficher notification finale spécialisée
        this.showFinalNotification('info', 'Resynchronisation sans nouveautés', 
            `${result.duplicate_orders_found} commandes existantes confirmées`, 'blue');
    }

    showSuccessNotification(result) {
        const icon = document.getElementById('syncIcon');
        const title = document.getElementById('syncTitle');
        const message = document.getElementById('syncMessage');
        const progress = document.getElementById('syncProgress');

        // Configuration pour le succès
        if (icon) {
            icon.className = 'fas fa-check-circle text-2xl text-green-600';
        }
        if (title) {
            title.textContent = 'Synchronisation réussie !';
        }
        if (message) {
            message.innerHTML = this.formatSuccessMessage(result);
        }
        if (progress) {
            progress.className = 'bg-green-600 h-2 rounded-full transition-all';
        }

        // Afficher notification finale de succès
        this.showFinalNotification('success', 'Synchronisation réussie', 
            `${result.new_orders_created || 0} nouvelles commandes ajoutées`, 'green');
    }

    showErrorNotification(result) {
        const icon = document.getElementById('syncIcon');
        const title = document.getElementById('syncTitle');
        const message = document.getElementById('syncMessage');
        const progress = document.getElementById('syncProgress');

        // Configuration pour l'erreur
        if (icon) {
            icon.className = 'fas fa-exclamation-circle text-2xl text-red-600';
        }
        if (title) {
            title.textContent = 'Erreur de synchronisation';
        }
        if (message) {
            message.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div class="text-red-700">
                        <i class="fas fa-exclamation-triangle mr-2"></i>
                        Des erreurs sont survenues pendant la synchronisation
                    </div>
                </div>
            `;
        }
        if (progress) {
            progress.className = 'bg-red-600 h-2 rounded-full transition-all';
        }

        // Afficher notification finale d'erreur
        this.showFinalNotification('error', 'Synchronisation échouée', 
            'Vérifiez les logs pour plus de détails', 'red');
    }

    showFinalNotification(type, title, message, color) {
        const finalNotification = document.getElementById('finalNotification');
        const notificationIcon = document.getElementById('notificationIcon');
        const notificationIconClass = document.getElementById('notificationIconClass');
        const notificationTitle = document.getElementById('notificationTitle');
        const notificationMessage = document.getElementById('notificationMessage');

        if (finalNotification && notificationIcon && notificationIconClass && notificationTitle && notificationMessage) {
            // Configuration des icônes et couleurs selon le type
            const configs = {
                'success': {
                    icon: 'fas fa-check-circle',
                    bgColor: 'bg-green-100',
                    textColor: 'text-green-600',
                    borderColor: 'border-green-200'
                },
                'info': {
                    icon: 'fas fa-info-circle',
                    bgColor: 'bg-blue-100', 
                    textColor: 'text-blue-600',
                    borderColor: 'border-blue-200'
                },
                'error': {
                    icon: 'fas fa-exclamation-circle',
                    bgColor: 'bg-red-100',
                    textColor: 'text-red-600',
                    borderColor: 'border-red-200'
                }
            };

            const config = configs[type] || configs['info'];
            
            notificationIcon.className = `flex items-center justify-center w-12 h-12 mx-auto mb-3 rounded-full ${config.bgColor}`;
            notificationIconClass.className = `${config.icon} text-2xl ${config.textColor}`;
            notificationTitle.textContent = title;
            notificationTitle.className = `font-bold text-lg mb-2 ${config.textColor}`;
            notificationMessage.textContent = message;
            finalNotification.className = `mt-4 p-4 rounded-lg border ${config.borderColor} ${config.bgColor}`;
            finalNotification.classList.remove('hidden');
        }
    }

    formatSuccessMessage(result) {
        const parts = [];
        
        if (result.new_orders_created > 0) {
            parts.push(`<span class="text-green-700"><i class="fas fa-plus-circle mr-1"></i>${result.new_orders_created} nouvelles commandes</span>`);
        }
        
        if (result.existing_orders_updated > 0) {
            parts.push(`<span class="text-orange-600"><i class="fas fa-edit mr-1"></i>${result.existing_orders_updated} mises à jour</span>`);
        }

        if (result.duplicate_orders_found > 0) {
            parts.push(`<span class="text-blue-600"><i class="fas fa-shield-alt mr-1"></i>${result.duplicate_orders_found} doublons évités</span>`);
        }

        return `<div class="space-y-1">${parts.join('<br>')}</div>`;
    }

    formatDetails(result) {
        const timestamp = new Date().toLocaleString('fr-FR');
        let details = `<div class="text-xs text-gray-500">Terminé le ${timestamp}</div>`;
        
        if (result.sync_summary) {
            details += `<div class="text-xs text-gray-600 mt-1">${result.sync_summary.replace(/\|/g, ' •')}</div>`;
        }
        
        return details;
    }

    hide() {
        this.isVisible = false;
        const modal = document.getElementById('syncModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    // Méthode principale pour synchroniser
    async syncConfig(configId, configName) {
        this.show();
        this.updateProgress(10, 'Connexion au serveur...');

        try {
            this.updateProgress(30, 'Connexion à Google Sheets...');
            
            const response = await fetch(`/synchronisation/sync-now/${configId}/`, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json'
                }
            });

            this.updateProgress(60, 'Traitement des données...');

            if (!response.ok) {
                throw new Error(`Erreur HTTP: ${response.status}`);
            }

            const result = await response.json();
            
            this.updateProgress(90, 'Finalisation...');
            
            // Afficher le résultat après un petit délai
            setTimeout(() => {
                this.showResult(result);
            }, 500);

            // Afficher le toast de notification après fermeture du modal
            const isNoNewOrders = result.new_orders_created === 0 && result.duplicate_orders_found > 0;
            setTimeout(() => {
                this.hide();
                // Afficher le toast si la fonction existe
                if (typeof showSyncToast === 'function') {
                    showSyncToast(result);
                }
            }, isNoNewOrders ? 5000 : 4000);

            // Recharger la page après fermeture complète (optionnel)
            setTimeout(() => {
                if (result.success || result.new_orders_created > 0) {
                    // window.location.reload();
                }
            }, 8000);

        } catch (error) {
            console.error('Erreur de synchronisation:', error);
            this.showResult({
                success: false,
                errors: ['Erreur de connexion au serveur'],
                sync_summary: 'Erreur technique'
            });
        }
    }

    getCSRFToken() {
        // Essayer plusieurs méthodes pour récupérer le token CSRF
        let token = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        if (!token) {
            // Essayer depuis les cookies
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                const [name, value] = cookie.trim().split('=');
                if (name === 'csrftoken') {
                    token = value;
                    break;
                }
            }
        }
        
        if (!token) {
            // Essayer depuis les meta tags
            const metaTag = document.querySelector('meta[name="csrf-token"]');
            if (metaTag) {
                token = metaTag.getAttribute('content');
            }
        }
        
        return token || '';
    }
}

// Initialisation globale
window.syncEnhanced = new SyncEnhanced();

// Fonction globale pour déclencher une synchronisation
window.syncNow = function(configId, configName) {
    window.syncEnhanced.syncConfig(configId, configName);
};

// Fonctions d'intégration avec les messages Django
window.showDjangoSyncMessage = function(result) {
    // Créer un message Django-style pour affichage dans les templates
    const messageType = result.new_orders_created === 0 && result.duplicate_orders_found > 0 ? 'info' : 'success';
    const messageContent = result.notification_message || result.sync_summary || 'Synchronisation terminée';
    
    // Si des éléments de message Django existent, les mettre à jour
    const messagesContainer = document.querySelector('.messages') || document.querySelector('#messages');
    if (messagesContainer) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `alert alert-${messageType} alert-dismissible fade show`;
        messageDiv.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${messageType === 'info' ? 'fa-info-circle' : 'fa-check-circle'} mr-2"></i>
                <span>${messageContent}</span>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        messagesContainer.appendChild(messageDiv);
        
        // Auto-suppression après délai
        setTimeout(() => {
            messageDiv.remove();
        }, 6000);
    }
};

// Intégration avec les notifications des pages
window.updatePageNotifications = function(result) {
    // Mettre à jour les badges ou compteurs sur la page
    const badges = document.querySelectorAll('[data-sync-badge]');
    badges.forEach(badge => {
        const type = badge.dataset.syncBadge;
        switch(type) {
            case 'new-orders':
                if (result.new_orders_created > 0) {
                    badge.textContent = `+${result.new_orders_created}`;
                    badge.classList.add('animate-pulse');
                }
                break;
            case 'duplicates':
                if (result.duplicate_orders_found > 0) {
                    badge.textContent = result.duplicate_orders_found;
                    badge.classList.add('bg-red-500', 'text-white');
                }
                break;
        }
    });
};

// Auto-initialisation
document.addEventListener('DOMContentLoaded', function() {
    console.log('🔄 Système de synchronisation amélioré initialisé');
    
    // Améliorer les boutons de synchronisation existants
    document.querySelectorAll('[data-sync-config]').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const configId = this.dataset.syncConfig;
            const configName = this.dataset.configName || 'Configuration';
            window.syncNow(configId, configName);
        });
    });

    // Intégrer les notifications avec les éléments de la page
    document.querySelectorAll('[data-sync-notification-target]').forEach(element => {
        element.addEventListener('syncComplete', function(event) {
            const result = event.detail;
            window.showDjangoSyncMessage(result);
            window.updatePageNotifications(result);
        });
    });
}); 