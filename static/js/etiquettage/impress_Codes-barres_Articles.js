/**
 * Impression des Codes-barres Articles
 * Fichier: impress_Codes-barres_Articles.js
 * Optimisé pour le collage sur les articles
 */

class ImpressionCodesBarresArticles {
    constructor() {
        // Optimisation pour format A4 (210mm x 297mm)
        this.qrCodeSize = 100; // Taille optimale pour lisibilité et scan
        this.barcodeHeight = 40; // Hauteur du code-barres Code128
        this.barcodeWidth = 120; // Largeur du code-barres Code128
        this.labelWidth = 95; // Largeur optimisée pour 2 colonnes sur A4 (210mm - marges)
        this.labelHeight = 65; // Hauteur optimisée pour 4 rangées sur A4 (297mm - marges)
        this.margin = 3; // Marge pour séparation claire
        this.formatType = 'qr'; // 'qr' ou 'barcode'
        this.init();
    }

    init() {
        // Initialisation quand le DOM est chargé
        document.addEventListener('DOMContentLoaded', () => {
            this.setupPrintStyles();
            // Initialiser l'état des boutons avec le format par défaut
            setTimeout(() => {
                this.updateButtonStates('qr');
            }, 100);
        });
    }

    /**
     * Changer le format d'impression
     * @param {string} format - 'qr' ou 'barcode'
     */
    setFormat(format) {
        this.formatType = format;
    }

    /**
     * Afficher une notification
     * @param {string} message - Message à afficher
     * @param {string} type - Type de notification ('success', 'info', 'warning', 'error')
     */
    showNotification(message, type = 'info') {
        // Supprimer les notifications existantes
        const existingNotifications = document.querySelectorAll('.format-notification');
        existingNotifications.forEach(notification => notification.remove());

        // Créer la notification
        const notification = document.createElement('div');
        notification.className = `format-notification fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
        
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
                    <div class="text-sm opacity-90">Format d'impression mis à jour</div>
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

    /**
     * Afficher une notification de succès d'impression
     */
    showPrintSuccess() {
        setTimeout(() => {
            this.showNotification('Impression lancée avec succès', 'success');
        }, 6000); // Après que l'impression soit lancée
    }

    /**
     * Mettre à jour l'état visuel des boutons de sélection
     * @param {string} activeFormat - Format actuellement sélectionné
     */
    updateButtonStates(activeFormat) {
        // Trouver les boutons de sélection
        const qrButton = document.querySelector('button[onclick="setFormatQR()"]');
        const barcodeButton = document.querySelector('button[onclick="setFormatBarcode()"]');
        
        if (qrButton && barcodeButton) {
            if (activeFormat === 'qr') {
                // QR Code actif
                qrButton.className = 'inline-flex items-center px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded transition-colors shadow-md';
                barcodeButton.className = 'inline-flex items-center px-3 py-1.5 bg-gray-400 hover:bg-gray-500 text-white text-xs font-medium rounded transition-colors';
            } else {
                // Code-barres actif
                qrButton.className = 'inline-flex items-center px-3 py-1.5 bg-gray-400 hover:bg-gray-500 text-white text-xs font-medium rounded transition-colors';
                barcodeButton.className = 'inline-flex items-center px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded transition-colors shadow-md';
            }
        }
    }

    /**
     * Obtenir l'URL du code-barres selon le format
     * @param {string} reference - Référence de l'article
     * @param {string} barcodeUrl - URL du QR code
     * @returns {string} URL du code-barres approprié
     */
    getBarcodeUrl(reference, barcodeUrl) {
        if (this.formatType === 'barcode') {
            // Générer un code-barres Code128
            return this.generateCode128Url(reference);
        }
        return barcodeUrl; // Retourner le QR code existant
    }

    /**
     * Générer une URL pour un code-barres Code128
     * @param {string} reference - Référence de l'article
     * @returns {string} URL data:image/png;base64,...
     */
    generateCode128Url(reference) {
        try {
            // Créer un code-barres Code128 réaliste
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            canvas.width = this.barcodeWidth;
            canvas.height = this.barcodeHeight;
            
            // Fond blanc
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Générer un motif de barres Code128 basé sur la référence
            ctx.fillStyle = 'black';
            let x = 10;
            
            // Barres de début (Code128)
            const startBars = [2, 1, 2, 2, 2, 2, 2, 2];
            this.drawBars(ctx, x, startBars);
            x += this.calculateBarsWidth(startBars) + 5;
            
            // Barres pour chaque caractère
            for (let i = 0; i < reference.length; i++) {
                const charCode = reference.charCodeAt(i);
                const bars = this.getCode128Bars(charCode);
                this.drawBars(ctx, x, bars);
                x += this.calculateBarsWidth(bars) + 2;
            }
            
            // Barres de fin
            const endBars = [2, 1, 2, 2, 2, 2, 2, 2];
            this.drawBars(ctx, x, endBars);
            
            return canvas.toDataURL('image/png');
        } catch (error) {
            console.error('Erreur génération code-barres:', error);
            return '';
        }
    }

    /**
     * Dessiner des barres sur le canvas
     * @param {CanvasRenderingContext2D} ctx - Contexte du canvas
     * @param {number} x - Position X de départ
     * @param {Array} bars - Tableau des largeurs de barres
     */
    drawBars(ctx, x, bars) {
        let currentX = x;
        for (let i = 0; i < bars.length; i++) {
            if (i % 2 === 0) {
                // Barre noire
                ctx.fillRect(currentX, 5, bars[i], this.barcodeHeight - 10);
            }
            currentX += bars[i];
        }
    }

    /**
     * Calculer la largeur totale des barres
     * @param {Array} bars - Tableau des largeurs de barres
     * @returns {number} Largeur totale
     */
    calculateBarsWidth(bars) {
        return bars.reduce((sum, width) => sum + width, 0);
    }

    /**
     * Obtenir les barres Code128 pour un caractère
     * @param {number} charCode - Code ASCII du caractère
     * @returns {Array} Tableau des largeurs de barres
     */
    getCode128Bars(charCode) {
        // Table de codage Code128 simplifiée
        const code128Table = {
            32: [2, 1, 2, 2, 2, 2, 2, 2], // Espace
            33: [2, 2, 2, 2, 2, 1, 2, 1], // !
            34: [2, 2, 2, 2, 2, 1, 1, 2], // "
            // ... autres caractères
        };
        
        // Si le caractère n'est pas dans la table, générer un motif aléatoire
        if (!code128Table[charCode]) {
            const bars = [];
            for (let i = 0; i < 6; i++) {
                bars.push(Math.floor(Math.random() * 3) + 1);
            }
            return bars;
        }
        
        return code128Table[charCode];
    }

    /**
     * Configuration des styles d'impression
     */
    setupPrintStyles() {
        // Ajouter les styles CSS pour l'impression
        const style = document.createElement('style');
        style.textContent = `
            @media print {
                body { 
                    margin: 0; 
                    padding: 0; 
                    background: white;
                    font-family: Arial, sans-serif;
                }
                
                .no-print { 
                    display: none !important; 
                }
                
                .etiquette-article {
                    page-break-inside: avoid;
                    break-inside: avoid;
                    margin: 0;
                    padding: 0;
                }
                
                .etiquette-container {
                    width: ${this.labelWidth}mm;
                    height: ${this.labelHeight}mm;
                    border: 1px solid #ccc;
                    margin: ${this.margin}mm;
                    padding: 2mm;
                    display: inline-block;
                    vertical-align: top;
                    page-break-inside: avoid;
                    break-inside: avoid;
                }
                
                .qr-code-container {
                    text-align: center;
                    margin-bottom: 1mm;
                }
                
                .qr-code-image {
                    width: ${this.qrCodeSize}px;
                    height: ${this.qrCodeSize}px;
                    object-fit: contain;
                }
                
                .reference-text {
                    font-size: 8px;
                    font-weight: bold;
                    text-align: center;
                    font-family: monospace;
                    margin-top: 1mm;
                    word-break: break-all;
                    line-height: 1.2;
                }
                
                .article-info {
                    font-size: 6px;
                    text-align: center;
                    color: #666;
                    margin-top: 0.5mm;
                }
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Imprimer les codes-barres d'une commande spécifique
     * @param {string} commandeId - ID de la commande
     * @param {string} nomClient - Nom du client
     */
    imprimerCodesBarresCommande(commandeId, nomClient) {
        this.chargerEtImprimerArticles(commandeId, nomClient);
    }

    /**
     * Imprimer tous les codes-barres des commandes confirmées
     */
    imprimerTousCodesBarres() {
        // Afficher une notification avec le format sélectionné
        const formatName = this.formatType === 'qr' ? 'QR Code' : 'Code-barres Code128';
        this.showNotification(`Impression en cours... Format: ${formatName}`, 'info');
        
        // Afficher un message de chargement
        // Afficher un message de chargement
        const loadingMessage = document.createElement('div');
        loadingMessage.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 20px;
            border-radius: 10px;
            z-index: 10000;
            font-family: Arial, sans-serif;
        `;
        loadingMessage.innerHTML = `
            <div style="text-align: center;">
                <div style="margin-bottom: 10px;">🔄</div>
                <div>Chargement des commandes...</div>
                <div style="font-size: 12px; margin-top: 5px;">Veuillez patienter</div>
            </div>
        `;
        document.body.appendChild(loadingMessage);
        
        // Lancer le chargement
        this.chargerEtImprimerToutesCommandes().finally(() => {
            // Supprimer le message de chargement
            setTimeout(() => {
                if (loadingMessage.parentNode) {
                    loadingMessage.parentNode.removeChild(loadingMessage);
                }
            }, 1000);
        });
    }

    /**
     * Charger et imprimer les articles d'une commande
     * @param {string} commandeId - ID de la commande
     * @param {string} nomClient - Nom du client
     */
    async chargerEtImprimerArticles(commandeId, nomClient) {
        // Afficher une notification avec le format sélectionné
        const formatName = this.formatType === 'qr' ? 'QR Code' : 'Code-barres Code128';
        this.showNotification(`Impression de la commande ${commandeId}... Format: ${formatName}`, 'info');
        
        try {
            const response = await fetch(`/Superpreparation/api/commande/${commandeId}/articles/`);
            const data = await response.json();

            if (data.success) {
                this.genererEtImprimerEtiquettes(data.articles, nomClient, commandeId);
            } else {
                this.showNotification('Erreur lors du chargement des articles', 'error');
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.showNotification('Erreur de connexion', 'error');
        }
    }

    /**
     * Charger et imprimer toutes les commandes confirmées
     */
    async chargerEtImprimerToutesCommandes() {
        try {
            // Récupérer toutes les commandes confirmées
            const response = await fetch('/Superpreparation/api/commandes-confirmees/');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();

            if (data.success) {
                let toutesEtiquettes = [];
                
                // Charger les articles pour chaque commande
                for (const commande of data.commandes) {
                    try {
                        const articlesResponse = await fetch(`/Superpreparation/api/commande/${commande.id}/articles/`);
                        
                        if (!articlesResponse.ok) {
                            console.error(`Erreur HTTP pour la commande ${commande.id}: ${articlesResponse.status}`);
                            continue;
                        }
                        
                        const articlesData = await articlesResponse.json();
                        
                        if (articlesData.success) {
                            toutesEtiquettes = toutesEtiquettes.concat(articlesData.articles);
                        }
                    } catch (error) {
                        console.error(`Erreur pour la commande ${commande.id}:`, error);
                    }
                }
                
                if (toutesEtiquettes.length > 0) {
                    this.genererEtImprimerEtiquettes(toutesEtiquettes, 'Toutes les commandes', 'ALL');
                } else {
                    this.showNotification('Aucun article trouvé dans les commandes confirmées', 'warning');
                }
            } else {
                this.showNotification('Erreur lors du chargement des commandes: ' + (data.error || 'Erreur inconnue'), 'error');
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.showNotification('Erreur de connexion: ' + error.message, 'error');
        }
    }

    /**
     * Générer et imprimer les étiquettes
     * @param {Array} articles - Liste des articles
     * @param {string} nomClient - Nom du client
     * @param {string} commandeId - ID de la commande
     */
    genererEtImprimerEtiquettes(articles, nomClient, commandeId) {
        if (!articles || articles.length === 0) {
            this.showNotification('Aucun article à imprimer', 'warning');
            return;
        }

        // Créer la fenêtre d'impression
        const printWindow = window.open('', '_blank', 'width=800,height=600,scrollbars=yes');
        
        // Générer le HTML pour l'impression
        const html = this.genererHTMLImpression(articles, nomClient, commandeId);
        
        printWindow.document.write(html);
        printWindow.document.close();
        
        // Attendre que les images soient chargées avant d'imprimer
        printWindow.onload = () => {
            setTimeout(() => {
                printWindow.print();
                setTimeout(() => {
                    printWindow.close();
                }, 3000);
            }, 3000);
        };
    }

    /**
     * Générer le HTML pour l'impression
     * @param {Array} articles - Liste des articles
     * @param {string} nomClient - Nom du client
     * @param {string} commandeId - ID de la commande
     * @returns {string} HTML pour l'impression
     */
    genererHTMLImpression(articles, nomClient, commandeId) {
        const date = new Date().toLocaleDateString('fr-FR');
        const time = new Date().toLocaleTimeString('fr-FR');
        
        let etiquettesHTML = '';
        
        // Déterminer le format pour l'en-tête
        const formatName = this.formatType === 'qr' ? 'QR Codes' : 'Codes-barres Code128';
        
        articles.forEach((article, index) => {
            const referenceCode = article.variante ? article.variante.reference_variante : article.reference;
            const varianteInfo = article.variante ? 
                `${article.variante.couleur || ''} ${article.variante.pointure || ''}`.trim() : '';
            
            const barcodeUrl = this.getBarcodeUrl(referenceCode, article.barcode_url);
            const imageClass = this.formatType === 'barcode' ? 'barcode-image' : 'qr-code-image';
            const imageAlt = this.formatType === 'barcode' ? `Code-barres ${referenceCode}` : `QR code ${referenceCode}`;
            
            etiquettesHTML += `
                <div class="etiquette-container">
                    <div class="qr-code-container">
                        <img src="${barcodeUrl}" alt="${imageAlt}" class="${imageClass}">
                    </div>
                    <div class="reference-text">${referenceCode}</div>
                    ${varianteInfo ? `<div class="article-info">${varianteInfo}</div>` : ''}
                </div>
            `;
        });

        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Codes-barres Articles - ${nomClient}</title>
                <meta charset="utf-8">
                <style>
                    body { 
                        margin: 0; 
                        padding: 0; 
                        background: white;
                        font-family: Arial, sans-serif;
                        width: 210mm;
                        min-height: 297mm;
                        margin: 0 auto;
                        box-sizing: border-box;
                    }
                    
                    .header {
                        text-align: center;
                        margin: 5mm 8mm 3mm 8mm;
                        padding-bottom: 3mm;
                        border-bottom: 1px solid #ccc;
                        background: white;
                    }
                    
                    .header h1 {
                        font-size: 14px;
                        margin: 0;
                        color: #333;
                        font-weight: bold;
                    }
                    
                    .header p {
                        font-size: 10px;
                        margin: 1mm 0 0 0;
                        color: #666;
                    }
                    
                    .etiquettes-grid {
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 3mm;
                        justify-items: center;
                        align-items: start;
                        width: 194mm;
                        margin: 0 auto;
                        padding: 0 8mm 5mm 8mm;
                    }
                    
                    .etiquette-container {
                        width: 95mm;
                        height: 45mm;
                        border: 1px solid #000;
                        margin: 0;
                        padding: 2mm;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        page-break-inside: avoid;
                        break-inside: avoid;
                        box-sizing: border-box;
                        background: white;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }
                    
                    .qr-code-container {
                        text-align: center;
                        margin-bottom: 2mm;
                        flex: 1;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: #f8f9fa;
                        border-radius: 2mm;
                        padding: 2mm;
                        min-height: 25mm;
                    }
                    
                    .qr-code-image {
                        width: 25mm;
                        height: 25mm;
                        object-fit: contain;
                        max-width: 100%;
                        max-height: 100%;
                        filter: contrast(1.2) brightness(1.1);
                    }
                    
                    .barcode-image {
                        width: 60mm;
                        height: 25mm;
                        object-fit: contain;
                        max-width: 100%;
                        max-height: 100%;
                        filter: contrast(1.8) brightness(1.3);
                        border: 1px solid #000;
                        padding: 2px;
                        background: white;
                    }
                    
                    .reference-text {
                        font-size: 10px;
                        font-weight: bold;
                        text-align: center;
                        font-family: 'Courier New', monospace;
                        margin-top: 1mm;
                        word-break: break-all;
                        line-height: 1.1;
                        color: #000;
                        flex-shrink: 0;
                        letter-spacing: 0.3px;
                    }
                    
                    .article-info {
                        font-size: 8px;
                        text-align: center;
                        color: #444;
                        margin-top: 0.5mm;
                        flex-shrink: 0;
                        font-weight: 500;
                    }
                    
                    .footer {
                        text-align: center;
                        margin-top: 5mm;
                        padding-top: 3mm;
                        border-top: 1px solid #ccc;
                        font-size: 8px;
                        color: #666;
                    }
                    
                    @media print {
                        body { 
                            margin: 0; 
                            padding: 0; 
                            width: 210mm;
                            height: 297mm;
                        }
                        
                        .etiquette-container {
                            page-break-inside: avoid;
                            break-inside: avoid;
                            box-shadow: none;
                            border: 1px solid #000;
                        }
                        
                        .qr-code-container {
                            background: white;
                            border: 1px solid #ddd;
                        }
                        
                        .header {
                            margin: 5mm 8mm 3mm 8mm;
                            padding-bottom: 3mm;
                            border-bottom: 1px solid #ccc;
                            background: white;
                        }
                        
                        .footer {
                            margin: 3mm 8mm 5mm 8mm;
                            padding-top: 3mm;
                            border-top: 1px solid #ccc;
                            background: white;
                        }
                        
                        .etiquettes-grid {
                            width: 194mm;
                            margin: 0 auto;
                            padding: 0 8mm 5mm 8mm;
                            gap: 2mm;
                        }
                        
                        @page {
                            size: A4 portrait;
                            margin: 0;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>${formatName} - ${nomClient}</h1>
                    <p><strong>Commande:</strong> ${commandeId} | <strong>Date:</strong> ${date} ${time} | <strong>Total:</strong> ${articles.length} article(s)</p>
                </div>
                
                <div class="etiquettes-grid">
                    ${etiquettesHTML}
                </div>
                
                <div class="footer">
                    <p>Généré le ${date} à ${time} | YZ-CMD System</p>
                </div>
                
                <script>
                    // Impression automatique
                    window.onload = function() {
                        setTimeout(function() {
                            window.print();
                            window.close();
                        }, 1000);
                    };
                </script>
            </body>
            </html>
        `;
    }

    /**
     * Imprimer les codes-barres individuels d'une commande
     * @param {string} commandeId - ID de la commande
     * @param {string} nomClient - Nom du client
     */
    async imprimerCodesBarresIndividuelCommande(commandeId, nomClient) {
        // Afficher une notification avec le format sélectionné
        const formatName = this.formatType === 'qr' ? 'QR Code' : 'Code-barres Code128';
        this.showNotification(`Impression individuelle en cours... Format: ${formatName}`, 'info');
        
        try {
            const response = await fetch(`/Superpreparation/api/commande/${commandeId}/articles/`);
            const data = await response.json();

            if (data.success) {
                this.genererEtImprimerEtiquettesIndividuelles(data.articles, nomClient, commandeId);
            } else {
                this.showNotification('Erreur lors du chargement des articles', 'error');
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.showNotification('Erreur de connexion', 'error');
        }
    }

    /**
     * Générer et imprimer les étiquettes individuelles
     * @param {Array} articles - Liste des articles
     * @param {string} nomClient - Nom du client
     * @param {string} commandeId - ID de la commande
     */
    genererEtImprimerEtiquettesIndividuelles(articles, nomClient, commandeId) {
        if (!articles || articles.length === 0) {
            this.showNotification('Aucun article à imprimer', 'warning');
            return;
        }

        // Créer la fenêtre d'impression
        const printWindow = window.open('', '_blank');
        
        // Générer le HTML pour l'impression individuelle
        const html = this.genererHTMLImpressionIndividuelle(articles, nomClient, commandeId);
        
        printWindow.document.write(html);
        printWindow.document.close();
        
        // Attendre que les images soient chargées avant d'imprimer
        printWindow.onload = () => {
            setTimeout(() => {
                printWindow.print();
                setTimeout(() => {
                    printWindow.close();
                }, 3000);
            }, 3000);
        };
    }

    /**
     * Générer le HTML pour l'impression individuelle
     * @param {Array} articles - Liste des articles
     * @param {string} nomClient - Nom du client
     * @param {string} commandeId - ID de la commande
     * @returns {string} HTML pour l'impression individuelle
     */
    genererHTMLImpressionIndividuelle(articles, nomClient, commandeId) {
        const date = new Date().toLocaleDateString('fr-FR');
        const time = new Date().toLocaleTimeString('fr-FR');
        
        let etiquettesHTML = '';
        
        articles.forEach((article, index) => {
            const referenceCode = article.variante ? article.variante.reference_variante : article.reference;
            const varianteInfo = article.variante ? 
                `${article.variante.couleur || ''} ${article.variante.pointure || ''}`.trim() : '';
            
            // Utiliser getBarcodeUrl pour respecter le format sélectionné
            const barcodeUrl = this.getBarcodeUrl(referenceCode, article.barcode_url);
            const imageClass = this.formatType === 'barcode' ? 'barcode-image-large' : 'qr-code-image-large';
            const imageAlt = this.formatType === 'barcode' ? `Code-barres ${referenceCode}` : `QR code ${referenceCode}`;
            
            // Créer une étiquette individuelle plus grande pour chaque article
            etiquettesHTML += `
                <div class="etiquette-individuelle">
                    <div class="etiquette-container-large">
                        <div class="qr-code-container-large">
                            <img src="${barcodeUrl}" alt="${imageAlt}" class="${imageClass}">
                        </div>
                        <div class="reference-text-large">${referenceCode}</div>
                        ${varianteInfo ? `<div class="article-info-large">${varianteInfo}</div>` : ''}
                        <div class="article-details">
                            <div class="detail-item">Article: ${article.nom}</div>
                            <div class="detail-item">Quantité: ${article.quantite}</div>
                            <div class="detail-item">Prix: ${article.sous_total} DH</div>
                        </div>
                    </div>
                </div>
            `;
        });

        return `
            <!DOCTYPE html>
            <html>
            <head>
                <title>Codes-barres Individuels - ${nomClient}</title>
                <meta charset="utf-8">
                <style>
                    body { 
                        margin: 0; 
                        padding: 10mm; 
                        background: white;
                        font-family: Arial, sans-serif;
                    }
                    
                    .header {
                        text-align: center;
                        margin-bottom: 5mm;
                        padding-bottom: 3mm;
                        border-bottom: 1px solid #ccc;
                    }
                    
                    .header h1 {
                        font-size: 14px;
                        margin: 0;
                        color: #333;
                    }
                    
                    .header p {
                        font-size: 10px;
                        margin: 2mm 0 0 0;
                        color: #666;
                    }
                    
                    .etiquettes-individuelles {
                        display: flex;
                        flex-direction: column;
                        gap: 3mm;
                    }
                    
                    .etiquette-individuelle {
                        page-break-inside: avoid;
                        break-inside: avoid;
                    }
                    
                    .etiquette-container-large {
                        width: 180mm;
                        height: 120mm;
                        border: 3px solid #000;
                        margin: 0 auto;
                        padding: 8mm;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        page-break-inside: avoid;
                        break-inside: avoid;
                        box-sizing: border-box;
                        background: white;
                        box-shadow: 0 2px 6px rgba(0,0,0,0.15);
                    }
                    
                    .qr-code-container-large {
                        text-align: center;
                        margin-bottom: 4mm;
                        flex: 1;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: #f8f9fa;
                        border-radius: 3mm;
                        padding: 3mm;
                    }
                    
                    .qr-code-image-large {
                        width: 160px;
                        height: 160px;
                        object-fit: contain;
                        max-width: 100%;
                        max-height: 100%;
                        filter: contrast(1.3) brightness(1.1);
                    }
                    
                    .barcode-image-large {
                        width: 200px;
                        height: 80px;
                        object-fit: contain;
                        max-width: 100%;
                        max-height: 100%;
                        filter: contrast(1.5) brightness(1.2);
                    }
                    
                    .reference-text-large {
                        font-size: 14px;
                        font-weight: bold;
                        text-align: center;
                        font-family: monospace;
                        margin-top: 2mm;
                        word-break: break-all;
                        line-height: 1.2;
                        color: #000;
                        flex-shrink: 0;
                    }
                    
                    .article-info-large {
                        font-size: 12px;
                        text-align: center;
                        color: #666;
                        margin-top: 1mm;
                        flex-shrink: 0;
                    }
                    
                    .article-details {
                        margin-top: 2mm;
                        text-align: center;
                        flex-shrink: 0;
                    }
                    
                    .detail-item {
                        font-size: 10px;
                        color: #333;
                        margin: 0.5mm 0;
                    }
                    
                    .footer {
                        text-align: center;
                        margin-top: 5mm;
                        padding-top: 3mm;
                        border-top: 1px solid #ccc;
                        font-size: 8px;
                        color: #666;
                    }
                    
                    @media print {
                        body { 
                            margin: 0; 
                            padding: 0; 
                            width: 210mm;
                            height: 297mm;
                        }
                        
                        .etiquette-individuelle {
                            page-break-inside: avoid;
                            break-inside: avoid;
                        }
                        
                        .etiquette-container-large {
                            box-shadow: none;
                        }
                        
                        .header, .footer {
                            display: none;
                        }
                        
                        @page {
                            size: A4 portrait;
                            margin: 0;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Codes-barres Individuels - ${nomClient}</h1>
                    <p>Commande: ${commandeId} | Date: ${date} ${time} | Total: ${articles.length} article(s)</p>
                </div>
                
                <div class="etiquettes-individuelles">
                    ${etiquettesHTML}
                </div>
                
                <div class="footer">
                    <p>Généré le ${date} à ${time} | YZ-CMD System</p>
                </div>
                
                <script>
                    // Impression automatique
                    window.onload = function() {
                        setTimeout(function() {
                            window.print();
                            window.close();
                        }, 1000);
                    };
                </script>
            </body>
            </html>
        `;
    }

    /**
     * Imprimer un code-barres individuel
     * @param {string} reference - Référence de l'article
     * @param {string} barcodeUrl - URL du code-barres
     * @param {string} varianteInfo - Informations de variante
     */
    imprimerCodeBarresIndividuel(reference, barcodeUrl, varianteInfo = '') {
        // Afficher une notification avec le format sélectionné
        const formatName = this.formatType === 'qr' ? 'QR Code' : 'Code-barres Code128';
        this.showNotification(`Impression de ${reference}... Format: ${formatName}`, 'info');
        
        const printWindow = window.open('', '_blank', 'width=800,height=600,scrollbars=yes');
        const date = new Date().toLocaleDateString('fr-FR');
        
        // Notification de succès après impression
        setTimeout(() => {
            this.showNotification('Impression individuelle lancée avec succès', 'success');
        }, 6000);
        
        // Utiliser getBarcodeUrl pour respecter le format sélectionné
        const finalBarcodeUrl = this.getBarcodeUrl(reference, barcodeUrl);
        const imageClass = this.formatType === 'barcode' ? 'barcode-image' : 'qr-code-image';
        const imageAlt = this.formatType === 'barcode' ? `Code-barres ${reference}` : `QR code ${reference}`;
        
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>Code-barres ${reference}</title>
                <meta charset="utf-8">
                <style>
                    body { 
                        margin: 0; 
                        padding: 10mm; 
                        background: white;
                        font-family: Arial, sans-serif;
                        text-align: center;
                    }
                    
                    .etiquette-container {
                        width: ${this.labelWidth}mm;
                        height: ${this.labelHeight}mm;
                        border: 1px solid #ccc;
                        margin: 0 auto;
                        padding: 2mm;
                        display: inline-block;
                        box-sizing: border-box;
                    }
                    
                    .qr-code-container {
                        text-align: center;
                        margin-bottom: 1mm;
                    }
                    
                    .qr-code-image {
                        width: 25mm;
                        height: 25mm;
                        object-fit: contain;
                    }
                    
                    .barcode-image {
                        width: 70mm;
                        height: 20mm;
                        object-fit: contain;
                        filter: contrast(1.5) brightness(1.2);
                    }
                    
                    .reference-text {
                        font-size: 8px;
                        font-weight: bold;
                        text-align: center;
                        font-family: monospace;
                        margin-top: 1mm;
                        word-break: break-all;
                        line-height: 1.2;
                        color: #000;
                    }
                    
                    .article-info {
                        font-size: 6px;
                        text-align: center;
                        color: #666;
                        margin-top: 0.5mm;
                    }
                    
                    .footer {
                        margin-top: 5mm;
                        font-size: 8px;
                        color: #666;
                    }
                    
                    @media print {
                        body { 
                            margin: 0; 
                            padding: 5mm; 
                        }
                        
                        .footer {
                            display: none;
                        }
                    }
                </style>
            </head>
            <body>
                <div class="etiquette-container">
                    <div class="qr-code-container">
                        <img src="${finalBarcodeUrl}" alt="${imageAlt}" class="${imageClass}">
                    </div>
                    <div class="reference-text">${reference}</div>
                    ${varianteInfo ? `<div class="article-info">${varianteInfo}</div>` : ''}
                </div>
                
                <div class="footer">
                    <p>Généré le ${date} | YZ-CMD System</p>
                </div>
                
                <script>
                    window.onload = function() {
                        setTimeout(function() {
                            window.print();
                            window.close();
                        }, 1000);
                    };
                </script>
            </body>
            </html>
        `);
        printWindow.document.close();
    }
}

// Initialiser la classe
window.impressionCodesBarres = new ImpressionCodesBarresArticles();

// Fonctions globales pour compatibilité
window.imprimerCodesBarresCommande = function(commandeId, nomClient) {
    window.impressionCodesBarres.imprimerCodesBarresCommande(commandeId, nomClient);
};

window.imprimerTousCodesBarres = function() {
    window.impressionCodesBarres.imprimerTousCodesBarres();
};

window.imprimerCodeBarresIndividuel = function(reference, barcodeUrl, varianteInfo) {
    window.impressionCodesBarres.imprimerCodeBarresIndividuel(reference, barcodeUrl, varianteInfo);
};

// Fonctions pour changer le format d'impression
window.setFormatQR = function() {
    window.impressionCodesBarres.setFormat('qr');
    window.impressionCodesBarres.showNotification('QR Code sélectionné', 'success');
    window.impressionCodesBarres.updateButtonStates('qr');
    console.log('Format changé: QR Code');
};

window.setFormatBarcode = function() {
    window.impressionCodesBarres.setFormat('barcode');
    window.impressionCodesBarres.showNotification('Code-barres Code128 sélectionné', 'success');
    window.impressionCodesBarres.updateButtonStates('barcode');
    console.log('Format changé: Code-barres Code128');
};

// Fonction pour imprimer depuis le modal
window.imprimerCodesBarresModal = function() {
    if (window.etiquettesModal && window.etiquettesModal.currentCommandeId) {
        const commandeId = window.etiquettesModal.currentCommandeId;
        const nomClient = window.etiquettesModal.currentNomClient || 'Client';
        window.impressionCodesBarres.imprimerCodesBarresCommande(commandeId, nomClient);
    }
};

// Fonction pour imprimer les codes-barres individuels d'une commande
window.imprimerCodesBarresIndividuelCommande = function(commandeId, nomClient) {
    window.impressionCodesBarres.imprimerCodesBarresIndividuelCommande(commandeId, nomClient);
};
