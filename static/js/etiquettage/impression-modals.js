/**
 * Gestion des modales d'impression pour les commandes confirmées
 * Fichier: impression-modals.js
 */

class ImpressionModals {
    constructor() {
        this.currentCommandeId = null;
        this.currentCommandeIdYz = null;
        this.currentClientNom = null;
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupModalListeners();
        });
    }

    setupModalListeners() {
        // Modale de choix d'impression
        const impressionChoiceModal = document.getElementById('impressionChoiceModal');
        if (impressionChoiceModal) {
            impressionChoiceModal.addEventListener('click', (e) => {
                if (e.target === impressionChoiceModal) {
                    this.hideImpressionChoiceModal();
                }
            });
        }

        // Modale de choix de format
        const formatChoiceModal = document.getElementById('formatChoiceModal');
        if (formatChoiceModal) {
            formatChoiceModal.addEventListener('click', (e) => {
                if (e.target === formatChoiceModal) {
                    this.hideFormatChoiceModal();
                }
            });
        }

        // Fermer avec la touche Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideImpressionChoiceModal();
                this.hideFormatChoiceModal();
            }
        });
    }

    /**
     * Afficher la modale de choix d'impression
     * @param {number} commandeId - ID de la commande
     * @param {string} commandeIdYz - ID YZ de la commande
     * @param {string} clientNom - Nom du client
     */
    showImpressionModal(commandeId, commandeIdYz, clientNom) {
        this.currentCommandeId = commandeId;
        this.currentCommandeIdYz = commandeIdYz;
        this.currentClientNom = clientNom;
        
        // Mettre à jour les informations dans la modale
        this.updateImpressionModalInfo();
        
        // Afficher la modale
        const modal = document.getElementById('impressionChoiceModal');
        if (modal) {
            modal.classList.remove('hidden');
            // Animation d'entrée
            modal.querySelector('.animate-fade-in-down').classList.add('animate-fade-in-down');
        }
    }

    /**
     * Fermer la modale de choix d'impression
     */
    hideImpressionChoiceModal() {
        const modal = document.getElementById('impressionChoiceModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * Mettre à jour les informations de la commande dans la modale
     */
    updateImpressionModalInfo() {
        if (this.currentCommandeIdYz) {
            const commandeIdElement = document.getElementById('commandeIdImpression');
            if (commandeIdElement) {
                commandeIdElement.textContent = this.currentCommandeIdYz;
            }
        }
        if (this.currentClientNom) {
            const clientNomElement = document.getElementById('clientNomImpression');
            if (clientNomElement) {
                clientNomElement.textContent = this.currentClientNom;
            }
        }
    }

    /**
     * Afficher les codes-barres des commandes dans une modale
     */
    async imprimerCodesBarresCommandes() {
        this.hideImpressionChoiceModal();
        if (this.currentCommandeIdYz) {
            try {
                // Afficher un indicateur de chargement
                this.showNotification('Chargement des codes-barres...', 'info');
                
                console.log(`🔍 Chargement des codes-barres pour la commande: ${this.currentCommandeIdYz}`);
                
                // Charger le contenu via AJAX
                const response = await fetch(`/Superpreparation/api/codes-barres-commandes/?ids=${this.currentCommandeIdYz}`);
                console.log(`📡 Réponse du serveur: ${response.status} ${response.statusText}`);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('✅ Données reçues:', data);
                    this.showCodesBarresModal(data);
                } else {
                    const errorText = await response.text();
                    console.error('❌ Erreur serveur:', errorText);
                    throw new Error(`Erreur serveur: ${response.status} - ${errorText}`);
                }
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification(`Erreur lors du chargement des codes-barres: ${error.message}`, 'error');
            }
        }
    }

    /**
     * Afficher les étiquettes des articles dans une modale
     */
    async imprimerEtiquettesArticles() {
        this.hideImpressionChoiceModal();
        if (this.currentCommandeIdYz) {
            // Afficher d'abord la modale de choix de format
            this.showFormatChoiceModal();
        }
    }

    /**
     * Afficher la modale de choix de format pour les étiquettes
     */
    showFormatChoiceModal() {
        // Créer ou récupérer la modale de choix de format
        let modal = document.getElementById('formatChoiceModal');
        if (!modal) {
            modal = this.createFormatChoiceModal();
        }
        
        // Afficher la modale
        modal.classList.remove('hidden');
    }

    /**
     * Créer la modale de choix de format
     */
    createFormatChoiceModal() {
        const modal = document.createElement('div');
        modal.id = 'formatChoiceModal';
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center';
        
        modal.innerHTML = `
            <div class="relative p-6 bg-white w-full max-w-md m-auto flex-col flex rounded-xl shadow-2xl animate-fade-in-down">
                <!-- En-tête du modal -->
                <div class="flex justify-between items-center pb-4 border-b border-gray-200 mb-6">
                    <div class="flex items-center">
                        <div class="w-12 h-12 rounded-full flex items-center justify-center mr-4" style="background-color: var(--preparation-light);">
                            <i class="fas fa-tags text-white text-xl"></i>
                        </div>
                        <h3 class="text-2xl font-bold" style="color: var(--preparation-light);">Choisir le format</h3>
                    </div>
                    <button onclick="impressionModals.hideFormatChoiceModal()" class="text-gray-400 hover:text-gray-600 transition-colors">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <!-- Contenu du modal -->
                <div class="py-6">
                    <div class="mb-6">
                        <p class="text-gray-600 mb-6">Choisissez le format d'affichage pour les étiquettes des articles :</p>
                        
                        <div class="space-y-4">
                            <!-- Option QR Codes -->
                            <button onclick="impressionModals.loadEtiquettesWithFormat('qr')" 
                                    class="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 flex items-center space-x-4">
                                <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                                    <i class="fas fa-qrcode text-blue-600 text-xl"></i>
                                </div>
                                <div class="text-left">
                                    <h4 class="font-semibold text-gray-900">QR Codes</h4>
                                    <p class="text-sm text-gray-600">Afficher les QR codes des articles</p>
                                </div>
                            </button>
                            
                            <!-- Option Codes-barres -->
                            <button onclick="impressionModals.loadEtiquettesWithFormat('barcode')" 
                                    class="w-full p-4 border-2 border-gray-200 rounded-lg hover:border-green-500 hover:bg-green-50 transition-all duration-200 flex items-center space-x-4">
                                <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                                    <i class="fas fa-barcode text-green-600 text-xl"></i>
                                </div>
                                <div class="text-left">
                                    <h4 class="font-semibold text-gray-900">Codes-barres</h4>
                                    <p class="text-sm text-gray-600">Afficher les codes-barres des articles</p>
                                </div>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        return modal;
    }

    /**
     * Fermer la modale de choix de format
     */
    hideFormatChoiceModal() {
        const modal = document.getElementById('formatChoiceModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * Charger les étiquettes avec un format spécifique
     */
    async loadEtiquettesWithFormat(format) {
        this.hideFormatChoiceModal();
        
        if (this.currentCommandeIdYz) {
            try {
                // Afficher un indicateur de chargement
                this.showNotification(`Chargement des étiquettes (${format === 'qr' ? 'QR Codes' : 'Codes-barres'})...`, 'info');
                
                console.log(`🔍 Chargement des étiquettes pour la commande: ${this.currentCommandeIdYz} avec format: ${format}`);
                
                // Charger le contenu via AJAX avec le format spécifié
                const response = await fetch(`/Superpreparation/api/etiquettes-articles/?ids=${this.currentCommandeIdYz}&format=${format}`);
                console.log(`📡 Réponse du serveur: ${response.status} ${response.statusText}`);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('✅ Données reçues:', data);
                    this.showEtiquettesArticlesModal(data);
                } else {
                    const errorText = await response.text();
                    console.error('❌ Erreur serveur:', errorText);
                    throw new Error(`Erreur serveur: ${response.status} - ${errorText}`);
                }
            } catch (error) {
                console.error('Erreur:', error);
                this.showNotification(`Erreur lors du chargement des étiquettes: ${error.message}`, 'error');
            }
        }
    }

    /**
     * Afficher la modale des codes-barres des commandes
     */
    showCodesBarresModal(data) {
        // Créer ou récupérer la modale
        let modal = document.getElementById('codesBarresModal');
        if (!modal) {
            modal = this.createCodesBarresModal();
        }
        
        // Mettre à jour le contenu
        const content = modal.querySelector('#codesBarresContent');
        if (content) {
            content.innerHTML = data.html || 'Aucun contenu disponible';
        }
        
        // Afficher la modale
        modal.classList.remove('hidden');
        
        // Initialiser les fonctionnalités d'impression
        this.initializeCodesBarresFeatures();
    }

    /**
     * Afficher la modale des étiquettes des articles
     */
    showEtiquettesArticlesModal(data) {
        // Créer ou récupérer la modale
        let modal = document.getElementById('etiquettesArticlesModal');
        if (!modal) {
            modal = this.createEtiquettesArticlesModal();
        }
        
        // Mettre à jour le contenu
        const content = modal.querySelector('#etiquettesArticlesContent');
        if (content) {
            content.innerHTML = data.html || 'Aucun contenu disponible';
        }
        
        // Afficher la modale
        modal.classList.remove('hidden');
        
        // Initialiser les fonctionnalités d'impression
        this.initializeEtiquettesFeatures();
    }

    /**
     * Créer la modale des codes-barres des commandes
     */
    createCodesBarresModal() {
        const modal = document.createElement('div');
        modal.id = 'codesBarresModal';
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center';
        
        modal.innerHTML = `
            <div class="relative p-6 bg-white w-full max-w-6xl m-auto flex-col flex rounded-xl shadow-2xl animate-fade-in-down">
                <!-- En-tête du modal -->
                <div class="flex justify-between items-center pb-4 border-b border-gray-200 mb-6">
                    <div class="flex items-center">
                        <div class="w-12 h-12 rounded-full flex items-center justify-center mr-4" style="background-color: var(--preparation-light);">
                            <i class="fas fa-barcode text-white text-xl"></i>
                        </div>
                        <h3 class="text-2xl font-bold" style="color: var(--preparation-light);">Codes-barres des Commandes</h3>
                    </div>
                    <button onclick="impressionModals.hideCodesBarresModal()" class="text-gray-400 hover:text-gray-600 transition-colors">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <!-- Contrôles de sélection -->
                <div class="flex justify-between items-center mb-4 p-3 bg-gray-50 rounded-lg">
                    <div class="flex items-center space-x-4">
                        <label class="flex items-center space-x-2">
                            <input type="checkbox" id="selectAllCodesBarres" class="form-checkbox h-4 w-4 text-blue-600 rounded" onchange="impressionModals.toggleSelectAllCodesBarres()">
                            <span class="text-sm font-medium text-gray-700">Sélectionner tout</span>
                        </label>
                        <span id="codesBarresSelectionCount" class="text-sm text-gray-500">0 sélectionné(s)</span>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button onclick="impressionModals.printSelectedCodesBarres()" 
                                class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-all duration-200 flex items-center space-x-1">
                            <i class="fas fa-print text-xs"></i>
                            <span>Imprimer sélection</span>
                        </button>
                        <button onclick="impressionModals.printAllCodesBarres()" 
                                class="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-all duration-200 flex items-center space-x-1">
                            <i class="fas fa-print text-xs"></i>
                            <span>Imprimer tout</span>
                        </button>
                    </div>
                </div>
                
                <!-- Contenu du modal -->
                <div id="codesBarresContent" class="flex-1 overflow-y-auto">
                    <!-- Le contenu sera chargé ici -->
                </div>
                
                <!-- Boutons d'action -->
                <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                    <button onclick="impressionModals.hideCodesBarresModal()" 
                            class="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-all duration-200">
                        Fermer
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        return modal;
    }

    /**
     * Créer la modale des étiquettes des articles
     */
    createEtiquettesArticlesModal() {
        const modal = document.createElement('div');
        modal.id = 'etiquettesArticlesModal';
        modal.className = 'fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center';
        
        modal.innerHTML = `
            <div class="relative p-6 bg-white w-full max-w-6xl m-auto flex-col flex rounded-xl shadow-2xl animate-fade-in-down">
                <!-- En-tête du modal -->
                <div class="flex justify-between items-center pb-4 border-b border-gray-200 mb-6">
                    <div class="flex items-center">
                        <div class="w-12 h-12 rounded-full flex items-center justify-center mr-4" style="background-color: var(--preparation-light);">
                            <i class="fas fa-tags text-white text-xl"></i>
                        </div>
                        <h3 class="text-2xl font-bold" style="color: var(--preparation-light);">Étiquettes des Articles</h3>
                    </div>
                    <button onclick="impressionModals.hideEtiquettesArticlesModal()" class="text-gray-400 hover:text-gray-600 transition-colors">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                </div>
                
                <!-- Contrôles de sélection -->
                <div class="flex justify-between items-center mb-4 p-3 bg-gray-50 rounded-lg">
                    <div class="flex items-center space-x-4">
                        <label class="flex items-center space-x-2">
                            <input type="checkbox" id="selectAllEtiquettes" class="form-checkbox h-4 w-4 text-green-600 rounded" onchange="impressionModals.toggleSelectAllEtiquettes()">
                            <span class="text-sm font-medium text-gray-700">Sélectionner tout</span>
                        </label>
                        <span id="etiquettesSelectionCount" class="text-sm text-gray-500">0 sélectionné(s)</span>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button onclick="impressionModals.printSelectedEtiquettes()" 
                                class="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-all duration-200 flex items-center space-x-1">
                            <i class="fas fa-print text-xs"></i>
                            <span>Imprimer sélection</span>
                        </button>
                        <button onclick="impressionModals.printAllEtiquettes()" 
                                class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-all duration-200 flex items-center space-x-1">
                            <i class="fas fa-print text-xs"></i>
                            <span>Imprimer tout</span>
                        </button>
                    </div>
                </div>
                
                <!-- Contenu du modal -->
                <div id="etiquettesArticlesContent" class="flex-1 overflow-y-auto">
                    <!-- Le contenu sera chargé ici -->
                </div>
                
                <!-- Boutons d'action -->
                <div class="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                    <button onclick="impressionModals.hideEtiquettesArticlesModal()" 
                            class="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-all duration-200">
                        Fermer
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        return modal;
    }

    /**
     * Fermer la modale des codes-barres
     */
    hideCodesBarresModal() {
        const modal = document.getElementById('codesBarresModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * Fermer la modale des étiquettes des articles
     */
    hideEtiquettesArticlesModal() {
        const modal = document.getElementById('etiquettesArticlesModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * Imprimer les codes-barres
     */
    printCodesBarres() {
        const content = document.getElementById('codesBarresContent');
        if (content) {
            const printWindow = window.open('', '_blank');
            printWindow.document.write(`
                <html>
                    <head>
                        <title>Codes-barres des Commandes</title>
                        <style>
                            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                            .commande-labels-container { display: grid; grid-template-columns: repeat(2, 1fr); gap: 5mm; }
                            .commande-label { width: 80mm; height: 50mm; border: 1px solid #ccc; padding: 2mm; text-align: center; }
                            @media print { body { margin: 0; } }
                        </style>
                    </head>
                    <body>
                        ${content.innerHTML}
                    </body>
                </html>
            `);
            printWindow.document.close();
            printWindow.print();
        }
    }

    /**
     * Imprimer les étiquettes des articles
     */
    printEtiquettesArticles() {
        const content = document.getElementById('etiquettesArticlesContent');
        if (content) {
            const printWindow = window.open('', '_blank');
            printWindow.document.write(`
                <html>
                    <head>
                        <title>Étiquettes des Articles</title>
                        <style>
                            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                            .article-labels-container { display: grid; grid-template-columns: repeat(2, 1fr); gap: 5mm; }
                            .article-label { width: 80mm; height: 50mm; border: 1px solid #ccc; padding: 2mm; text-align: center; }
                            @media print { body { margin: 0; } }
                        </style>
                    </head>
                    <body>
                        ${content.innerHTML}
                    </body>
                </html>
            `);
            printWindow.document.close();
            printWindow.print();
        }
    }

    /**
     * Initialiser les fonctionnalités des codes-barres
     */
    initializeCodesBarresFeatures() {
        // Charger les scripts nécessaires si pas déjà fait
        this.loadScript('/static/js/etiquettage/impress_Codes-barres_Articles.js');
    }

    /**
     * Initialiser les fonctionnalités des étiquettes
     */
    initializeEtiquettesFeatures() {
        // Charger les scripts nécessaires si pas déjà fait
        this.loadScript('/static/js/etiquettage/etiquettes-articles-modal.js');
    }

    /**
     * Charger un script dynamiquement
     */
    loadScript(src) {
        if (!document.querySelector(`script[src="${src}"]`)) {
            const script = document.createElement('script');
            script.src = src;
            document.head.appendChild(script);
        }
    }

    /**
     * Basculer la sélection de tous les codes-barres
     */
    toggleSelectAllCodesBarres() {
        const selectAllCheckbox = document.getElementById('selectAllCodesBarres');
        const checkboxes = document.querySelectorAll('#codesBarresContent input[type="checkbox"]');
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
        });
        
        this.updateSelectionCount('codesBarres');
    }

    /**
     * Basculer la sélection de toutes les étiquettes
     */
    toggleSelectAllEtiquettes() {
        const selectAllCheckbox = document.getElementById('selectAllEtiquettes');
        const checkboxes = document.querySelectorAll('#etiquettesArticlesContent input[type="checkbox"]');
        
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
        });
        
        this.updateSelectionCount('etiquettes');
    }

    /**
     * Mettre à jour le compteur de sélection
     */
    updateSelectionCount(type) {
        const containerId = type === 'codesBarres' ? 'codesBarresContent' : 'etiquettesArticlesContent';
        const countId = type === 'codesBarres' ? 'codesBarresSelectionCount' : 'etiquettesSelectionCount';
        
        const checkboxes = document.querySelectorAll(`#${containerId} input[type="checkbox"]`);
        const selectedCount = Array.from(checkboxes).filter(cb => cb.checked).length;
        
        const countElement = document.getElementById(countId);
        if (countElement) {
            countElement.textContent = `${selectedCount} sélectionné(s)`;
        }
    }

    /**
     * Imprimer les codes-barres sélectionnés
     */
    printSelectedCodesBarres() {
        const checkboxes = document.querySelectorAll('#codesBarresContent input[type="checkbox"]:checked');
        if (checkboxes.length === 0) {
            this.showNotification('Aucun code-barres sélectionné', 'warning');
            return;
        }
        
        const selectedLabels = Array.from(checkboxes).map(cb => {
            const labelItem = cb.closest('.commande-label-item');
            return labelItem ? labelItem.querySelector('.commande-label').outerHTML : '';
        }).filter(html => html);
        
        this.printLabels(selectedLabels, 'Codes-barres des Commandes', 'commandes');
    }

    /**
     * Imprimer tous les codes-barres
     */
    printAllCodesBarres() {
        const labels = document.querySelectorAll('#codesBarresContent .commande-label');
        const labelsHtml = Array.from(labels).map(label => label.outerHTML);
        
        this.printLabels(labelsHtml, 'Codes-barres des Commandes', 'commandes');
    }

    /**
     * Imprimer les étiquettes sélectionnées
     */
    printSelectedEtiquettes() {
        const checkboxes = document.querySelectorAll('#etiquettesArticlesContent input[type="checkbox"]:checked');
        if (checkboxes.length === 0) {
            this.showNotification('Aucune étiquette sélectionnée', 'warning');
            return;
        }
        
        const selectedLabels = Array.from(checkboxes).map(cb => {
            const labelItem = cb.closest('.article-label-item');
            return labelItem ? labelItem.querySelector('.article-label').outerHTML : '';
        }).filter(html => html);
        
        this.printLabels(selectedLabels, 'Étiquettes des Articles');
    }

    /**
     * Imprimer toutes les étiquettes
     */
    printAllEtiquettes() {
        const labels = document.querySelectorAll('#etiquettesArticlesContent .article-label');
        const labelsHtml = Array.from(labels).map(label => label.outerHTML);
        
        this.printLabels(labelsHtml, 'Étiquettes des Articles');
    }

    /**
     * Imprimer les labels sélectionnés
     */
    printLabels(labelsHtml, title, type = 'articles') {
        const printWindow = window.open('', '_blank');
        const containerClass = type === 'commandes' ? 'commande-labels-container' : 'article-labels-container';
        const timestamp = new Date().toLocaleString('fr-FR');
        
        // Déterminer le titre de la page selon le type
        let pageTitle = '';
        let pageSubtitle = '';
        
        if (type === 'commandes') {
            pageTitle = 'Codes-barres Code128 - Toutes les commandes';
            pageSubtitle = `Commande: ALL | Date: ${timestamp} | Total: ${labelsHtml.length} article(s)`;
        } else {
            pageTitle = 'QR Codes - Toutes les commandes';
            pageSubtitle = `Commande: ALL | Date: ${timestamp} | Total: ${labelsHtml.length} article(s)`;
        }
        
        printWindow.document.write(`
            <!DOCTYPE html>
            <html lang="fr">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>${pageTitle}</title>
                <style>
                    /* Reset et styles de base */
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }

                    body {
                        font-family: Arial, sans-serif;
                        font-size: 12px;
                        line-height: 1.4;
                        color: #000;
                        background: white;
                    }

                    /* Styles pour l'impression */
                    @media print {
                        @page {
                            size: A4 portrait;
                            margin: 10mm;
                        }

                        body {
                            margin: 0;
                            padding: 0;
                            background: white !important;
                            -webkit-print-color-adjust: exact !important;
                            color-adjust: exact !important;
                            width: 210mm;
                            height: 297mm;
                        }

                        .no-print {
                            display: none !important;
                        }

                        .page-break {
                            page-break-before: always;
                        }

                        .avoid-break {
                            page-break-inside: avoid;
                        }

                        .print-container {
                            width: 190mm; /* 210mm - 20mm de marges */
                            height: 277mm; /* 297mm - 20mm de marges */
                            margin: 0 auto;
                            position: relative;
                            margin-top: 15mm;
                            margin-bottom: 10mm;
                            padding: 10mm;
                            min-height: calc(277mm - 15mm - 10mm);
                        }

                        .print-header {
                            position: fixed;
                            top: 10mm;
                            left: 10mm;
                            right: 10mm;
                            height: 15mm;
                            background: white;
                            z-index: 1000;
                            border-bottom: 2px solid #333;
                        }

                        .print-footer {
                            position: fixed;
                            bottom: 10mm;
                            left: 10mm;
                            right: 10mm;
                            height: 10mm;
                            background: white;
                            z-index: 1000;
                            border-top: 1px solid #ccc;
                        }

                        .labels-grid {
                            padding: 5mm;
                            width: 100%;
                            height: 100%;
                            margin-top: 5mm;
                        }
                    }

                    /* Styles pour l'en-tête et pied de page */
                    .print-header {
                        text-align: center;
                        padding: 3mm;
                        background: white;
                        height: 15mm;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                    }

                    .print-header h1 {
                        font-size: 16px;
                        font-weight: bold;
                        color: #333;
                        margin: 0 0 2mm 0;
                        line-height: 1.2;
                    }

                    .print-header p {
                        font-size: 10px;
                        color: #666;
                        margin: 0;
                        line-height: 1.2;
                    }

                    .print-footer {
                        text-align: center;
                        padding: 2mm;
                        font-size: 8px;
                        color: #666;
                        background: white;
                        height: 10mm;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                    }

                    .print-footer p {
                        margin: 0;
                        line-height: 1.2;
                    }

                    /* Grille des étiquettes */
                    .labels-grid,
                    .article-labels-container,
                    .commande-labels-container {
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 5mm;
                        width: 100%;
                        max-width: 160mm;
                        margin: 0 auto;
                        padding: 5mm;
                        margin-top: 5mm;
                    }

                    /* Étiquette individuelle */
                    .article-label,
                    .commande-label {
                        width: 60mm;
                        height: 40mm;
                        border: 1px solid #000;
                        font-family: Arial, sans-serif;
                        font-size: 8px;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        background: white;
                        page-break-inside: avoid;
                        break-inside: avoid;
                        margin: 0;
                        overflow: hidden;
                        position: relative;
                        padding: 2mm;
                    }

                    .article-label *,
                    .commande-label * {
                        -webkit-print-color-adjust: exact !important;
                        color-adjust: exact !important;
                    }

                    /* Code-barres */
                    .label-barcode {
                        max-width: 100%;
                        max-height: 20mm;
                        object-fit: contain;
                        margin-bottom: 2mm;
                    }

                    /* Référence */
                    .article-reference {
                        font-size: 8px;
                        text-align: center;
                        font-weight: bold;
                        color: #000;
                        word-break: break-word;
                        margin-bottom: 1mm;
                    }

                    /* Variante */
                    .article-variante {
                        font-size: 7px;
                        text-align: center;
                        color: #666;
                    }

                    /* Masquer les checkboxes lors de l'impression */
                    .label-checkbox {
                        display: none !important;
                    }

                    /* Responsive pour l'écran */
                    @media screen {
                        body {
                            background: #f5f5f5;
                            padding: 20px;
                        }

                        .print-container {
                            background: white;
                            padding: 20px;
                            border-radius: 8px;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        }
                    }
                </style>
            </head>
            <body>
                <div class="print-container">
                    <!-- En-tête de page -->
                    <div class="print-header">
                        <h1>${pageTitle}</h1>
                        <p>${pageSubtitle}</p>
                    </div>

                    <!-- Grille des étiquettes -->
                    <div class="${containerClass}">
                        ${labelsHtml.join('')}
                    </div>

                    <!-- Pied de page -->
                    <div class="print-footer">
                        <p>Généré le ${timestamp} - YZ-CMD</p>
                    </div>
                </div>
            </body>
            </html>
        `);
        printWindow.document.close();
        printWindow.print();
    }

    /**
     * Afficher une notification
     * @param {string} message - Message à afficher
     * @param {string} type - Type de notification ('success', 'info', 'warning', 'error')
     */
    showNotification(message, type = 'info') {
        // Supprimer les notifications existantes
        const existingNotifications = document.querySelectorAll('.impression-notification');
        existingNotifications.forEach(notification => notification.remove());

        // Créer la notification
        const notification = document.createElement('div');
        notification.className = `impression-notification fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
        
        // Couleurs selon le type
        const colors = {
            success: 'bg-green-500 text-white',
            info: 'bg-blue-500 text-white',
            warning: 'bg-yellow-500 text-black',
            error: 'bg-red-500 text-white'
        };
        
        notification.className += ` ${colors[type] || colors.info}`;
        
        // Icône selon le type
        const icons = {
            success: 'fas fa-check-circle',
            info: 'fas fa-info-circle',
            warning: 'fas fa-exclamation-triangle',
            error: 'fas fa-times-circle'
        };
        
        notification.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="${icons[type] || icons.info} text-lg"></i>
                <div>
                    <div class="font-medium">${message}</div>
                    <div class="text-sm opacity-90">Impression en cours...</div>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-2 opacity-70 hover:opacity-100">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        
        // Ajouter au DOM
        document.body.appendChild(notification);
        
        // Animation d'entrée
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto-suppression après 4 secondes
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.parentNode.removeChild(notification);
                    }
                }, 300);
            }
        }, 4000);
    }
}

// Initialiser l'instance globale
const impressionModals = new ImpressionModals();

// Fonctions globales pour compatibilité avec les onclick
function showImpressionModal(commandeId, commandeIdYz, clientNom) {
    impressionModals.showImpressionModal(commandeId, commandeIdYz, clientNom);
}

function hideImpressionChoiceModal() {
    impressionModals.hideImpressionChoiceModal();
}

function imprimerCodesBarresCommandes() {
    impressionModals.imprimerCodesBarresCommandes();
}

function imprimerEtiquettesArticles() {
    impressionModals.imprimerEtiquettesArticles();
}

// Fonctions pour les modales de contenu
function hideCodesBarresModal() {
    impressionModals.hideCodesBarresModal();
}

function hideEtiquettesArticlesModal() {
    impressionModals.hideEtiquettesArticlesModal();
}

function printCodesBarres() {
    impressionModals.printCodesBarres();
}

function printEtiquettesArticles() {
    impressionModals.printEtiquettesArticles();
}

// Fonctions pour la modale de choix de format
function hideFormatChoiceModal() {
    impressionModals.hideFormatChoiceModal();
}

function loadEtiquettesWithFormat(format) {
    impressionModals.loadEtiquettesWithFormat(format);
}

// Fonctions pour la sélection et l'impression
function toggleSelectAllCodesBarres() {
    impressionModals.toggleSelectAllCodesBarres();
}

function toggleSelectAllEtiquettes() {
    impressionModals.toggleSelectAllEtiquettes();
}

function updateSelectionCount(type) {
    impressionModals.updateSelectionCount(type);
}

function printSelectedCodesBarres() {
    impressionModals.printSelectedCodesBarres();
}

function printAllCodesBarres() {
    impressionModals.printAllCodesBarres();
}

function printSelectedEtiquettes() {
    impressionModals.printSelectedEtiquettes();
}

function printAllEtiquettes() {
    impressionModals.printAllEtiquettes();
}
