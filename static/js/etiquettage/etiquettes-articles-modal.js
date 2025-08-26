/**
 * Gestion du modal des articles pour les étiquettes
 * Fichier: etiquettes-articles-modal.js
 */

class EtiquettesArticlesModal {
    constructor() {
        this.modal = null;
        this.modalContainer = null;
        this.modalTitle = null;
        this.modalSubtitle = null;
        this.modalContent = null;
        this.articlesCount = null;
        this.modalTimestamp = null;
        this.currentCommandeId = null;
        this.currentNomClient = null;
        this.formatType = 'qr'; // Format par défaut: QR Code
        this.init();
    }

    init() {
        // Initialisation quand le DOM est chargé
        document.addEventListener('DOMContentLoaded', () => {
            this.setupModal();
            this.setupPrintFunctionality();
        });
    }

    setupModal() {
        // Récupérer les éléments du modal
        this.modal = document.getElementById('modalArticles');
        this.modalTitle = document.getElementById('modalTitle');
        this.modalContent = document.getElementById('modalContent');

        // Ajouter les event listeners pour fermer le modal
        this.setupModalCloseListeners();
    }

    setupModalCloseListeners() {
        // Fermer en cliquant sur le bouton X
        const closeButton = this.modal?.querySelector('button[onclick="fermerModalArticles()"]');
        if (closeButton) {
            closeButton.addEventListener('click', () => this.fermerModal());
        }

        // Fermer en cliquant à l'extérieur du modal
        this.modal?.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.fermerModal();
            }
        });

        // Fermer avec la touche Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !this.modal?.classList.contains('hidden')) {
                this.fermerModal();
            }
        });
    }

    setupPrintFunctionality() {
        // Vérifier s'il y a un paramètre 'ids' dans l'URL pour l'impression automatique
        const urlParams = new URLSearchParams(window.location.search);
        const ids = urlParams.get('ids');

        if (ids) {
            // Lance la boîte de dialogue d'impression dès que la page est chargée
            window.print();
        }
    }

    /**
     * Changer le format d'affichage (QR Code ou Code-barres)
     * @param {string} format - 'qr' ou 'barcode'
     */
    setFormat(format) {
        console.log('Changement de format vers:', format);
        this.formatType = format;
        this.updateFormatButtons();
        this.refreshArticlesDisplay();
    }

    /**
     * Mettre à jour l'état visuel des boutons de format
     */
    updateFormatButtons() {
        const qrButton = document.getElementById('modalQrButton');
        const barcodeButton = document.getElementById('modalBarcodeButton');
        
        console.log('Mise à jour des boutons:', { qrButton, barcodeButton, formatType: this.formatType });
        
        if (qrButton && barcodeButton) {
            if (this.formatType === 'qr') {
                qrButton.classList.remove('bg-gray-500', 'hover:bg-gray-600');
                qrButton.classList.add('bg-blue-600', 'hover:bg-blue-700');
                barcodeButton.classList.remove('bg-blue-600', 'hover:bg-blue-700');
                barcodeButton.classList.add('bg-gray-500', 'hover:bg-gray-600');
                console.log('Format QR activé');
            } else {
                barcodeButton.classList.remove('bg-gray-500', 'hover:bg-gray-600');
                barcodeButton.classList.add('bg-blue-600', 'hover:bg-blue-700');
                qrButton.classList.remove('bg-blue-600', 'hover:bg-blue-700');
                qrButton.classList.add('bg-gray-500', 'hover:bg-gray-600');
                console.log('Format Barcode activé');
            }
        } else {
            console.log('Boutons non trouvés');
        }
    }

    /**
     * Rafraîchir l'affichage des articles avec le nouveau format
     */
    refreshArticlesDisplay() {
        console.log('🔄 Rafraîchissement de l\'affichage...');
        
        // Mettre à jour les images existantes sans recharger depuis le serveur
        const images = this.modalContent.querySelectorAll('img[alt*="QR code"], img[alt*="Code-barres"]');
        console.log('📸 Images trouvées:', images.length);
        
        images.forEach((img, index) => {
            console.log(`🖼️ Image ${index + 1}:`, {
                alt: img.alt,
                src: img.src.substring(0, 50) + '...',
                originalUrl: img.getAttribute('data-original-url')
            });
            
            const reference = img.alt.split(' ').pop(); // Extraire la référence
            const originalUrl = img.getAttribute('data-original-url') || img.src;
            
            console.log(`📝 Référence extraite: ${reference}`);
            
            // Mettre à jour l'URL selon le format
            const newUrl = this.getBarcodeUrl(reference, originalUrl);
            console.log(`🔄 Nouvelle URL: ${newUrl.substring(0, 50)}...`);
            
            img.src = newUrl;
            
            // Mettre à jour l'alt et le style selon le format
            if (this.formatType === 'qr') {
                img.alt = `QR code ${reference}`;
                img.style.height = '120px';
                img.style.width = '120px';
                console.log(`✅ Image ${index + 1} mise à jour vers QR Code`);
            } else {
                img.alt = `Code-barres ${reference}`;
                img.style.height = '80px';
                img.style.width = '200px';
                console.log(`✅ Image ${index + 1} mise à jour vers Code-barres`);
            }
        });
        
        // Mettre à jour les textes et icônes
        this.updateModalTexts();
        console.log('🎨 Textes et icônes mis à jour');
    }

    /**
     * Mettre à jour les textes et icônes dans le modal
     */
    updateModalTexts() {
        console.log('🎨 Mise à jour des textes et icônes...');
        
        // Mettre à jour les titres des sections
        const titles = this.modalContent.querySelectorAll('.text-sm.font-semibold.text-gray-700');
        console.log('📝 Titres trouvés:', titles.length);
        
        titles.forEach((title, index) => {
            if (title.textContent.includes('Code-barres pour scan') || title.textContent.includes('QR Code pour scan')) {
                const newText = `${this.formatType === 'qr' ? 'QR Code' : 'Code-barres'} pour scan`;
                title.textContent = newText;
                console.log(`📝 Titre ${index + 1} mis à jour: "${newText}"`);
            }
        });
        
        // Mettre à jour les icônes
        const icons = this.modalContent.querySelectorAll('.fas.fa-barcode, .fas.fa-qrcode');
        console.log('🔍 Icônes trouvées:', icons.length);
        
        icons.forEach((icon, index) => {
            if (this.formatType === 'qr') {
                icon.className = 'fas fa-qrcode text-blue-600 mr-2';
                console.log(`🔍 Icône ${index + 1} mise à jour vers QR Code`);
            } else {
                icon.className = 'fas fa-barcode text-blue-600 mr-2';
                console.log(`🔍 Icône ${index + 1} mise à jour vers Code-barres`);
            }
        });
    }

    /**
     * Générer l'URL du code-barres selon le format sélectionné
     * @param {string} reference - Référence de l'article
     * @param {string} defaultUrl - URL par défaut
     * @returns {string} URL du code-barres
     */
    getBarcodeUrl(reference, defaultUrl) {
        console.log('getBarcodeUrl appelé:', { reference, defaultUrl, formatType: this.formatType });
        if (this.formatType === 'qr') {
            console.log('Retour URL QR:', defaultUrl);
            return defaultUrl; // Utiliser l'URL QR code existante
        } else {
            console.log('Génération Code128 pour:', reference);
            // Générer un code-barres Code128 côté client
            return this.generateCode128Barcode(reference);
        }
    }

    /**
     * Créer une abréviation intelligente pour les références longues
     * @param {string} reference - Référence originale
     * @returns {string} Abréviation intelligente
     */
    createSmartAbbreviation(reference) {
        const parts = reference.split('-');
        
        // Si on a au moins 3 parties, créer une abréviation intelligente
        if (parts.length >= 3) {
            const category = parts[0]; // BOT, MULE, etc.
            const gender = parts[1];   // FEM, MEN, etc.
            const model = parts[2];    // YZ3010, YZ1121, etc.
            
            // Prendre les 3 premiers caractères de chaque partie importante
            const catShort = category.substring(0, 3);
            const genShort = gender.substring(0, 2);
            const modShort = model.substring(0, 4);
            
            // Ajouter la taille si elle existe (dernière partie)
            let size = '';
            if (parts.length > 3) {
                const lastPart = parts[parts.length - 1];
                // Extraire les chiffres de la taille
                const sizeMatch = lastPart.match(/\d+/);
                if (sizeMatch) {
                    size = sizeMatch[0];
                }
            }
            
            // Créer l'abréviation
            let abbreviation = `${catShort}-${genShort}-${modShort}`;
            if (size) {
                abbreviation += `-${size}`;
            }
            
            return abbreviation;
        }
        
        // Fallback: prendre les premiers caractères de chaque mot
        return reference.split('-').map(part => part.substring(0, 3)).join('-').substring(0, 15);
    }

    /**
     * Analyser et optimiser une référence pour l'encodage Code128
     * @param {string} reference - Référence originale
     * @returns {object} Objet avec référence optimisée et métadonnées
     */
    analyzeAndOptimizeReference(reference) {
        const originalRef = String(reference).trim();
        const length = originalRef.length;
        
        // Analyse de la référence
        const analysis = {
            original: originalRef,
            length: length,
            hasSpecialChars: /[^A-Za-z0-9\-_\.\/\s]/.test(originalRef),
            hasSpaces: originalRef.includes(' '),
            hasHyphens: originalRef.includes('-'),
            isTooLong: length > 20, // Limite pour un bon scan
            optimized: originalRef,
            strategy: 'direct',
            hash: null
        };
        
        console.log('🔍 Analyse de la référence:', analysis);
        
        // Stratégie 1: Référence courte et simple (≤20 caractères)
        if (length <= 20 && !analysis.hasSpecialChars) {
            analysis.strategy = 'direct';
            analysis.optimized = originalRef;
            console.log('✅ Stratégie: Encodage direct');
            return analysis;
        }
        
        // Stratégie 2: Référence longue ou avec caractères spéciaux
        if (length > 20 || analysis.hasSpecialChars) {
            // Créer une abréviation intelligente
            const abbreviation = this.createSmartAbbreviation(originalRef);
            analysis.strategy = 'abbreviation';
            analysis.optimized = abbreviation;
            analysis.abbreviation = abbreviation;
            console.log('🔄 Stratégie: Abréviation intelligente', analysis.optimized);
            return analysis;
        }
        
        // Stratégie 3: Nettoyer et raccourcir
        let cleaned = originalRef
            .replace(/[^A-Za-z0-9\-_\.\/\s]/g, '') // Supprimer caractères spéciaux
            .replace(/\s+/g, ' ')                  // Normaliser espaces
            .trim();
        
        if (cleaned.length <= 20) {
            analysis.strategy = 'cleaned';
            analysis.optimized = cleaned;
            console.log('🧹 Stratégie: Nettoyage', analysis.optimized);
            return analysis;
        }
        
        // Stratégie 4: Fallback vers abréviation
        const abbreviation = this.createSmartAbbreviation(cleaned);
        analysis.strategy = 'abbreviation_fallback';
        analysis.optimized = abbreviation;
        analysis.abbreviation = abbreviation;
        console.log('🔄 Stratégie: Abréviation fallback', analysis.optimized);
        return analysis;
    }

    /**
     * Générer un code-barres Code128 côté client avec optimisation intelligente
     * @param {string} text - Texte à encoder
     * @returns {string} URL data du code-barres
     */
    generateCode128Barcode(text) {
        // Créer un canvas temporaire avec des dimensions optimisées
        const canvas = document.createElement('canvas');
        canvas.width = 400;
        canvas.height = 120;
        
        try {
            // Analyser et optimiser la référence
            const analysis = this.analyzeAndOptimizeReference(text);
            const textToEncode = analysis.optimized;
            
            console.log('🔍 Texte optimisé pour Code128:', textToEncode);
            console.log('📊 Stratégie utilisée:', analysis.strategy);
            
            // Configuration optimisée selon la stratégie
            const config = {
                format: "CODE128B",  // Toujours CODE128B pour alphanumérique
                width: 3,
                height: 80,
                displayValue: true,
                fontSize: 14,
                margin: 15,
                background: "#ffffff",
                lineColor: "#000000",
                fontOptions: "bold",
                textMargin: 8,
                textAlign: "center",
                valid: function(valid) {
                    if (!valid) {
                        console.warn('⚠️ Code128 invalide pour:', textToEncode);
                    } else {
                        console.log('✅ Code128 valide pour:', textToEncode);
                        console.log('🔍 Mode d\'encodage: CODE128B (alphanumérique)');
                        console.log('📊 Stratégie:', analysis.strategy);
                    }
                }
            };
            
            // Générer le code-barres
            JsBarcode(canvas, textToEncode, config);
            
            // Si on utilise une abréviation, stocker la correspondance
            if (analysis.abbreviation) {
                if (!this.abbreviationMapping) {
                    this.abbreviationMapping = {};
                }
                this.abbreviationMapping[analysis.abbreviation] = analysis.original;
                console.log('🔗 Abréviation mappée:', analysis.abbreviation, '→', analysis.original);
            }
            
            console.log('✅ Code128 généré avec succès pour:', textToEncode);
            return canvas.toDataURL();
            
        } catch (error) {
            console.error('❌ Erreur lors de la génération du code-barres:', error);
            
            // Fallback: générer un code-barres simple amélioré
            const ctx = canvas.getContext('2d');
            
            // Fond blanc
            ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Texte en noir et gras
            ctx.fillStyle = 'black';
            ctx.font = 'bold 18px monospace';
            ctx.textAlign = 'center';
            ctx.fillText(text, canvas.width / 2, canvas.height / 2);
            
            return canvas.toDataURL();
        }
    }

    /**
     * Récupérer la référence originale à partir d'une abréviation scannée
     * @param {string} scannedCode - Code scanné (abréviation ou référence directe)
     * @returns {string} Référence originale
     */
    getOriginalReference(scannedCode) {
        if (!scannedCode) return null;
        
        // Vérifier si c'est une abréviation connue
        const original = this.abbreviationMapping ? this.abbreviationMapping[scannedCode] : null;
        
        if (original) {
            console.log('🔍 Abréviation trouvée:', scannedCode, '→', original);
            return original;
        }
        
        // Si c'est une référence directe
        console.log('🔍 Référence directe:', scannedCode);
        return scannedCode;
    }

    /**
     * Afficher les informations de mapping des abréviations
     */
    showAbbreviationMapping() {
        if (!this.abbreviationMapping || Object.keys(this.abbreviationMapping).length === 0) {
            console.log('📋 Aucune abréviation mappée');
            return;
        }
        
        console.log('📋 Mapping des abréviations:');
        Object.entries(this.abbreviationMapping).forEach(([abbreviation, original]) => {
            console.log(`  ${abbreviation} → ${original}`);
        });
    }





    /**
     * Afficher le modal des articles
     * @param {string} commandeId - ID de la commande
     * @param {string} nomClient - Nom du client
     */
    afficherModal(commandeId, nomClient) {
        if (!this.modal || !this.modalTitle || !this.modalContent) {
            console.error('Éléments du modal non trouvés');
            return;
        }

        // Sauvegarder les informations actuelles
        this.currentCommandeId = commandeId;
        this.currentNomClient = nomClient;

        // Mettre à jour le titre et sous-titre
        this.modalTitle.textContent = `Commande ${commandeId}`;
        if (this.modalSubtitle) {
            this.modalSubtitle.textContent = `Client: ${nomClient}`;
        }
        
        // Mettre à jour le timestamp
        this.updateTimestamp();
        
        // Afficher le modal avec animation
        this.modal.classList.remove('hidden');
        if (this.modalContainer) {
            this.modalContainer.classList.add('show');
        }
        
        // Initialiser les boutons de format
        this.updateFormatButtons();
        
        // Afficher le loader
        this.afficherLoader();
        
        // Charger les articles via AJAX
        this.chargerArticles(commandeId);
    }

    /**
     * Charger les articles d'une commande via API
     * @param {string} commandeId - ID de la commande
     */
    async chargerArticles(commandeId) {
        try {
            const response = await fetch(`/Superpreparation/api/commande/${commandeId}/articles/`);
            const data = await response.json();

            if (data.success) {
                this.afficherArticles(data.articles);
            } else {
                this.afficherErreur('Erreur lors du chargement des articles');
            }
        } catch (error) {
            console.error('Erreur:', error);
            this.afficherErreur('Erreur de connexion');
        }
    }

    /**
     * Afficher les articles dans le modal avec disposition horizontale
     * @param {Array} articles - Liste des articles
     */
    afficherArticles(articles) {
        if (!articles || articles.length === 0) {
            this.modalContent.innerHTML = `
                <div class="flex flex-col items-center justify-center py-12">
                    <div class="bg-gray-100 p-6 rounded-full mb-4">
                        <i class="fas fa-box-open text-4xl text-gray-400"></i>
                    </div>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">Aucun article trouvé</h3>
                    <p class="text-gray-500 text-center">Cette commande ne contient aucun article</p>
                </div>
            `;
            if (this.articlesCount) {
                this.articlesCount.textContent = '0 article';
            }
            return;
        }

        // Mettre à jour le compteur d'articles
        if (this.articlesCount) {
            this.articlesCount.textContent = `${articles.length} article${articles.length > 1 ? 's' : ''}`;
        }

        // Disposition horizontale avec grille responsive
        let html = '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">';
        
        articles.forEach((article, index) => {
            html += this.genererHTMLArticle(article, index);
        });
        
        html += '</div>';
        this.modalContent.innerHTML = html;
        
        // Mettre à jour le timestamp
        this.updateTimestamp();
    }

    /**
     * Générer le HTML pour un article avec une meilleure UX
     * @param {Object} article - Données de l'article
     * @param {number} index - Index de l'article
     * @returns {string} HTML de l'article
     */
    genererHTMLArticle(article, index) {
        const varianteHTML = article.variante ? this.genererHTMLVariante(article.variante) : '';
        const referenceCode = article.variante ? article.variante.reference_variante : article.reference;
        
        return `
            <div class="article-card bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden" data-article-index="${index}">
                <!-- En-tête avec référence et badge -->
                <div class="bg-gray-100 px-4 py-3 flex justify-between items-center">
                    <div class="flex items-center space-x-2">
                        <span class="font-medium text-gray-700">${article.reference}</span>
                        <span class="bg-blue-500 text-white text-xs px-2 py-1 rounded-full">${article.quantite} var.</span>
                    </div>
                    <div class="w-8 h-8 bg-gray-300 rounded flex items-center justify-center">
                        <i class="fas fa-image text-gray-500 text-sm"></i>
                    </div>
                </div>

                <!-- Titre de l'article -->
                <div class="bg-gray-800 text-white px-4 py-3 text-center">
                    <h4 class="font-semibold text-sm">${article.nom}</h4>
                </div>

                <!-- Détails principaux -->
                <div class="p-4 space-y-3">
                    <div class="grid grid-cols-2 gap-2 text-sm text-center">
                        <div><span class="text-gray-600">Référence:</span> <span class="font-medium">${article.reference}</span></div>
                        <div><span class="text-gray-600">Prix:</span> <span class="font-medium text-green-600">${article.sous_total} DH</span></div>
                        <div><span class="text-gray-600">Quantité:</span> <span class="font-medium">${article.quantite}</span></div>
                        <div><span class="text-gray-600">Article:</span> <span class="font-medium">${index + 1}</span></div>
                    </div>

                    <!-- Variante intégrée -->
                    <div class="text-center">
                        ${varianteHTML}
                    </div>

                    <!-- Code-barres mis en valeur -->
                    <div class="mt-4 text-center">
                        <div class="flex items-center justify-center mb-2">
                            <i class="${this.formatType === 'qr' ? 'fas fa-qrcode' : 'fas fa-barcode'} text-blue-600 mr-2"></i>
                            <span class="text-sm font-semibold text-gray-700">${this.formatType === 'qr' ? 'QR Code' : 'Code-barres'} pour scan</span>
                        </div>
                        
                        <!-- Container du code centré et très lisible -->
                        <div class="bg-white p-6 rounded border border-gray-200 inline-block mx-auto">
                            <img src="${this.getBarcodeUrl(referenceCode, article.barcode_url)}" 
                                 alt="${this.formatType === 'qr' ? 'QR code' : 'Code-barres'} ${referenceCode}" 
                                 data-original-url="${article.barcode_url}"
                                 style="${this.formatType === 'qr' ? 'height: 120px; width: 120px;' : 'height: 80px; width: 200px;'} object-fit: contain;">
                        </div>
                    </div>

                    <!-- Actions centrées -->
                    <div class="flex justify-center space-x-2 mt-4">
                        <button onclick="copierReference('${referenceCode}')" 
                                class="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1.5 rounded transition-colors shadow-sm"
                                title="Copier la référence">
                            <i class="fas fa-copy mr-1"></i>Copier
                        </button>
                        <button onclick="imprimerCodeBarresAvecFormat('${referenceCode}', '${article.barcode_url}', '${article.variante ? (article.variante.couleur || '') + ' ' + (article.variante.pointure || '') : ''}')" 
                                class="bg-green-600 hover:bg-green-700 text-white text-xs px-3 py-1.5 rounded transition-colors shadow-sm"
                                title="Imprimer le code-barres">
                            <i class="fas fa-print mr-1"></i>Imprimer
                        </button>
                        <button onclick="agrandirCodeBarresAvecFormat('${referenceCode}', '${article.barcode_url}')" 
                                class="bg-purple-600 hover:bg-purple-700 text-white text-xs px-3 py-1.5 rounded transition-colors shadow-sm"
                                title="Voir en grand">
                            <i class="fas fa-search-plus mr-1"></i>Agrandir
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Générer le HTML pour une variante adaptée au nouveau design
     * @param {Object} variante - Données de la variante
     * @returns {string} HTML de la variante
     */
    genererHTMLVariante(variante) {
        const couleurHTML = variante.couleur ? `
            <div class="flex items-center space-x-1">
                <i class="fas fa-palette text-purple-500 text-xs"></i>
                <span class="text-xs text-gray-600">${variante.couleur}</span>
            </div>
        ` : '';
        
        const pointureHTML = variante.pointure ? `
            <div class="flex items-center space-x-1">
                <i class="fas fa-shoe-prints text-purple-500 text-xs"></i>
                <span class="text-xs text-gray-600">${variante.pointure}</span>
            </div>
        ` : '';

        return `
            <div class="bg-purple-50 rounded p-2 border border-purple-200 inline-block">
                <div class="text-xs font-medium text-purple-700 mb-1 text-center">Réf. Variante</div>
                <div class="font-mono text-xs text-purple-800 mb-2 text-center">${variante.reference_variante}</div>
                <div class="flex justify-center space-x-3">
                    ${couleurHTML}
                    ${pointureHTML}
                </div>
            </div>
        `;
    }

    /**
     * Afficher une erreur dans le modal
     * @param {string} message - Message d'erreur
     */
    afficherErreur(message) {
        this.modalContent.innerHTML = `
            <div class="text-center text-red-600">
                <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                <p>${message}</p>
            </div>
        `;
    }

    /**
     * Afficher le loader
     */
    afficherLoader() {
        this.modalContent.innerHTML = `
            <div class="flex flex-col items-center justify-center py-12">
                <div class="relative">
                    <div class="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                    <div class="absolute inset-0 flex items-center justify-center">
                        <i class="fas fa-shopping-cart text-blue-600 text-xl"></i>
                    </div>
                </div>
                <p class="mt-4 text-gray-600 font-medium">Chargement des articles...</p>
                <p class="text-sm text-gray-500">Veuillez patienter</p>
            </div>
        `;
    }

    /**
     * Mettre à jour le timestamp
     */
    updateTimestamp() {
        if (this.modalTimestamp) {
            const now = new Date();
            const timeString = now.toLocaleTimeString('fr-FR', { 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
            });
            this.modalTimestamp.textContent = `Dernière mise à jour: ${timeString}`;
        }
    }

    /**
     * Fermer le modal avec animation
     */
    fermerModal() {
        if (this.modalContainer) {
            this.modalContainer.classList.remove('show');
            setTimeout(() => {
                this.modal?.classList.add('hidden');
            }, 300);
        } else {
            this.modal?.classList.add('hidden');
        }
    }
}

// Fonctions globales pour compatibilité avec les onclick
window.afficherModalArticles = function(commandeId, nomClient) {
    if (window.etiquettesModal) {
        window.etiquettesModal.afficherModal(commandeId, nomClient);
    }
};

window.fermerModalArticles = function() {
    if (window.etiquettesModal) {
        window.etiquettesModal.fermerModal();
    }
};

// Initialiser le modal quand le script est chargé
window.etiquettesModal = new EtiquettesArticlesModal();

// Fonctions d'impression
// Fonction supprimée - maintenant gérée depuis "Suivi des Commandes Confirmées"
// window.imprimerEtiquettesCommande = function(commandeId) {
//     // Rediriger vers la page d'impression avec l'ID de la commande
//     window.open(`/Superpreparation/etiquettes-articles/?ids=${commandeId}`, '_blank');
// };

window.imprimerToutesEtiquettes = function() {
    window.print();
};

// Nouvelles fonctions pour le modal amélioré
window.imprimerModalArticles = function() {
    if (window.etiquettesModal && window.etiquettesModal.currentCommandeId) {
        window.imprimerEtiquettesCommande(window.etiquettesModal.currentCommandeId);
    }
};

window.exporterModalArticles = function() {
    // Fonction pour exporter les données (à implémenter)
    alert('Fonction d\'export à implémenter');
};

window.actualiserModalArticles = function() {
    if (window.etiquettesModal && window.etiquettesModal.currentCommandeId) {
        window.etiquettesModal.afficherLoader();
        window.etiquettesModal.chargerArticles(window.etiquettesModal.currentCommandeId);
    }
};

window.copierReference = function(reference) {
    navigator.clipboard.writeText(reference).then(() => {
        // Afficher une notification de succès
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-4 py-2 rounded-md shadow-lg z-50';
        notification.innerHTML = `<i class="fas fa-check mr-2"></i>Référence copiée: ${reference}`;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }).catch(err => {
        console.error('Erreur lors de la copie:', err);
    });
};

window.imprimerCodeBarres = function(reference, barcodeUrl) {
    // Utiliser le format sélectionné dans le modal
    const formatType = window.etiquettesModal ? window.etiquettesModal.formatType : 'qr';
    const finalBarcodeUrl = window.etiquettesModal ? window.etiquettesModal.getBarcodeUrl(reference, barcodeUrl) : barcodeUrl;
    const formatName = formatType === 'qr' ? 'QR Code' : 'Code-barres';
    
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>${formatName} ${reference}</title>
            <style>
                body { 
                    margin: 0; 
                    padding: 20px; 
                    font-family: Arial, sans-serif; 
                    background: white;
                }
                .barcode-container { 
                    text-align: center; 
                    padding: 20px;
                }
                .barcode-image { 
                    max-width: 100%; 
                    height: auto; 
                    border: 2px solid #000;
                    padding: 15px;
                    background: white;
                    border-radius: 6px;
                    filter: contrast(1.8) brightness(1.3);
                }
                .reference { 
                    font-size: 18px; 
                    font-weight: bold; 
                    margin-top: 15px;
                    font-family: monospace;
                }
                @media print {
                    body { padding: 0; }
                    .barcode-container { page-break-inside: avoid; }
                }
            </style>
        </head>
        <body>
            <div class="barcode-container">
                <img src="${finalBarcodeUrl}" alt="${formatName} ${reference}" class="barcode-image">
                <div class="reference">${reference}</div>
            </div>
            <script>window.onload = function() { window.print(); }</script>
        </body>
        </html>
    `);
    printWindow.document.close();
};

window.agrandirCodeBarres = function(reference, barcodeUrl) {
    console.log('🔍 agrandirCodeBarres appelé:', { reference, barcodeUrl });
    
    // Utiliser le format sélectionné dans le modal
    const formatType = modalArticles ? modalArticles.formatType : 'qr';
    const finalBarcodeUrl = modalArticles ? modalArticles.getBarcodeUrl(reference, barcodeUrl) : barcodeUrl;
    const formatName = formatType === 'qr' ? 'QR Code' : 'Code-barres';
    const formatIcon = formatType === 'qr' ? 'fas fa-qrcode' : 'fas fa-barcode';
    
    console.log('🔍 Format détecté dans agrandirCodeBarres:', formatType);
    console.log('🔍 URL finale dans agrandirCodeBarres:', finalBarcodeUrl.substring(0, 50) + '...');
    console.log('🔍 Format name:', formatName);
    
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 backdrop-blur-sm';
    modal.innerHTML = `
        <div class="bg-white rounded-xl p-4 max-w-sm mx-4 shadow-xl border border-gray-200">
            <!-- En-tête compact -->
            <div class="flex justify-between items-center mb-3">
                <div class="flex items-center">
                    <div class="bg-blue-600 text-white p-2 rounded-full mr-3">
                        <i class="${formatIcon} text-sm"></i>
                    </div>
                    <div>
                        <h3 class="text-lg font-bold text-gray-900">${formatName}</h3>
                        <p class="text-xs text-gray-600">Référence: ${reference}</p>
                    </div>
                </div>
                <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700 p-2 rounded-full hover:bg-gray-100 transition-colors">
                    <i class="fas fa-times text-sm"></i>
                </button>
            </div>
            
            <!-- Contenu principal compact -->
            <div class="text-center">
                <!-- Container du code compact -->
                <div class="bg-gray-50 p-3 rounded-lg border border-blue-200 mb-3">
                    <img src="${finalBarcodeUrl}" alt="${formatName} ${reference}" 
                         style="max-width: 100%; height: auto; min-height: 100px; border: 2px solid #000; padding: 15px; background: white; border-radius: 6px; filter: contrast(1.8) brightness(1.3);">
                </div>
                
                <!-- Référence compact -->
                <div class="bg-blue-50 p-2 rounded-lg border border-blue-200 mb-3">
                    <div class="flex items-center justify-center">
                        <i class="fas fa-tag text-blue-600 mr-1 text-xs"></i>
                        <div class="text-sm font-mono font-bold text-blue-900">${reference}</div>
                    </div>
                </div>
            </div>
            
            <!-- Actions compact -->
            <div class="flex justify-center space-x-2">
                <button onclick="window.imprimerCodeBarres('${reference}', '${finalBarcodeUrl}')" 
                        class="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 shadow-md hover:shadow-lg">
                    <i class="fas fa-print mr-1"></i>Imprimer
                </button>
                <button onclick="window.copierReference('${reference}')" 
                        class="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 shadow-md hover:shadow-lg">
                    <i class="fas fa-copy mr-1"></i>Copier
                </button>
                <button onclick="this.closest('.fixed').remove()" 
                        class="bg-gray-500 hover:bg-gray-600 text-white px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 shadow-md hover:shadow-lg">
                    <i class="fas fa-times mr-1"></i>Fermer
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Fermer en cliquant à l'extérieur
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            modal.remove();
        }
    });
};

// Initialisation de l'instance
const modalArticles = new EtiquettesArticlesModal();

// Fonctions globales pour l'interface
function afficherModalArticles(commandeId, nomClient) {
    modalArticles.afficherModal(commandeId, nomClient);
}

function fermerModalArticles() {
    modalArticles.fermerModal();
}

function actualiserModalArticles() {
    modalArticles.actualiserModal();
}

function imprimerCodesBarresModal() {
    modalArticles.imprimerCodesBarres();
}

function copierReference(reference) {
    modalArticles.copierReference(reference);
}

function agrandirCodeBarres(reference, barcodeUrl) {
    modalArticles.agrandirCodeBarres(reference, barcodeUrl);
}

// Nouvelles fonctions qui récupèrent le format actuel
function agrandirCodeBarresAvecFormat(reference, barcodeUrl) {
    console.log('🔍 agrandirCodeBarresAvecFormat appelé:', { reference, barcodeUrl });
    console.log('🔍 modalArticles:', modalArticles);
    
    const formatType = modalArticles ? modalArticles.formatType : 'qr';
    console.log('🔍 Format détecté:', formatType);
    
    const finalBarcodeUrl = modalArticles ? modalArticles.getBarcodeUrl(reference, barcodeUrl) : barcodeUrl;
    console.log('🔍 URL finale:', finalBarcodeUrl.substring(0, 50) + '...');
    
    agrandirCodeBarres(reference, finalBarcodeUrl);
}

function imprimerCodeBarresAvecFormat(reference, barcodeUrl, varianteInfo) {
    console.log('🖨️ imprimerCodeBarresAvecFormat appelé:', { reference, barcodeUrl, varianteInfo });
    console.log('🖨️ modalArticles:', modalArticles);
    
    const formatType = modalArticles ? modalArticles.formatType : 'qr';
    console.log('🖨️ Format détecté:', formatType);
    
    const finalBarcodeUrl = modalArticles ? modalArticles.getBarcodeUrl(reference, barcodeUrl) : barcodeUrl;
    console.log('🖨️ URL finale:', finalBarcodeUrl.substring(0, 50) + '...');
    
    imprimerCodeBarresIndividuel(reference, finalBarcodeUrl, varianteInfo);
}

// Fonctions globales pour le basculement de format
function setFormatQR() {
    console.log('setFormatQR appelé');
    if (modalArticles) {
        modalArticles.setFormat('qr');
    } else {
        console.error('modalArticles non défini');
    }
}

function setFormatBarcode() {
    console.log('setFormatBarcode appelé');
    if (modalArticles) {
        modalArticles.setFormat('barcode');
    } else {
        console.error('modalArticles non défini');
    }
}

// Fonction de test pour vérifier le contenu des codes-barres
function testCodeBarres(reference) {
    console.log('🧪 Test du code-barres pour:', reference);
    
    if (modalArticles) {
        // Test avec différents formats
        const formats = ['CODE128', 'CODE128A', 'CODE128B', 'CODE128C'];
        
        formats.forEach(format => {
            console.log(`🧪 Test avec format ${format}:`);
            try {
                const canvas = document.createElement('canvas');
                canvas.width = 400;
                canvas.height = 120;
                
                JsBarcode(canvas, reference, {
                    format: format,
                    width: 3,
                    height: 80,
                    displayValue: true,
                    fontSize: 14,
                    margin: 15,
                    background: "#ffffff",
                    lineColor: "#000000",
                    fontOptions: "bold",
                    textMargin: 8,
                    valid: function(valid) {
                        console.log(`  ✅ ${format} valide:`, valid);
                    }
                });
                
                console.log(`  ✅ ${format} généré avec succès`);
            } catch (error) {
                console.error(`  ❌ ${format} erreur:`, error.message);
            }
        });
        
        const testUrl = modalArticles.generateCode128Barcode(reference);
        console.log('🧪 URL générée:', testUrl.substring(0, 100) + '...');
        
        // Créer une image temporaire pour vérifier
        const img = new Image();
        img.onload = function() {
            console.log('🧪 Image chargée avec succès');
            console.log('🧪 Dimensions:', img.width, 'x', img.height);
        };
        img.onerror = function() {
            console.error('🧪 Erreur lors du chargement de l\'image');
        };
        img.src = testUrl;
    } else {
        console.error('modalArticles non défini');
    }
}

// Fonction pour tester l'encodage spécifique
function testEncoding(reference) {
    console.log('🔍 Test d\'encodage pour:', reference);
    
    const canvas = document.createElement('canvas');
    canvas.width = 400;
    canvas.height = 120;
    
    // Test avec CODE128B (format recommandé pour alphanumérique)
    JsBarcode(canvas, reference, {
        format: "CODE128B",
        width: 3,
        height: 80,
        displayValue: true,
        fontSize: 14,
        margin: 15,
        background: "#ffffff",
        lineColor: "#000000",
        fontOptions: "bold",
        textMargin: 8,
        textAlign: "center",
        valid: function(valid) {
            console.log('✅ Code128B valide:', valid);
            if (valid) {
                console.log('📝 Texte encodé:', reference);
                console.log('🔍 Longueur:', reference.length);
                console.log('🔤 Caractères:', reference.split('').join(', '));
            }
        }
    });
    
    // Créer un lien de téléchargement pour tester
    const link = document.createElement('a');
    link.download = `test_${reference.replace(/[^a-zA-Z0-9]/g, '_')}.png`;
    link.href = canvas.toDataURL();
    link.textContent = `Télécharger ${reference}`;
    link.style.display = 'block';
    link.style.margin = '10px';
    link.style.padding = '10px';
    link.style.backgroundColor = '#007bff';
    link.style.color = 'white';
    link.style.textDecoration = 'none';
    link.style.borderRadius = '5px';
    
    document.body.appendChild(link);
    console.log('📥 Lien de téléchargement créé pour tester le scan');
}

// Fonction pour comparer les références qui fonctionnent vs celles qui ne fonctionnent pas
function compareReferences() {
    console.log('🔍 Comparaison des références');
    
    const workingRef = "TEST-123-ABC";  // Fonctionne
    const failingRefs = [
        "BOT-FEM-YZ3010-Standard-37",
        "MULE-FEM-YZ1121-Beige-36",
        "BOT-FEM-YZ3010-Standard-40"
    ];
    
    console.log('✅ Référence qui fonctionne:', workingRef);
    console.log('  - Longueur:', workingRef.length);
    console.log('  - Caractères:', workingRef.split('').join(', '));
    
    failingRefs.forEach(ref => {
        console.log('❌ Référence qui ne fonctionne pas:', ref);
        console.log('  - Longueur:', ref.length);
        console.log('  - Caractères:', ref.split('').join(', '));
        
        // Créer un code-barres pour chaque référence
        const canvas = document.createElement('canvas');
        canvas.width = 400;
        canvas.height = 120;
        
        JsBarcode(canvas, ref, {
            format: "CODE128B",
            width: 3,
            height: 80,
            displayValue: true,
            fontSize: 14,
            margin: 15,
            background: "#ffffff",
            lineColor: "#000000",
            fontOptions: "bold",
            textMargin: 8,
            textAlign: "center"
        });
        
        // Créer un lien de téléchargement
        const link = document.createElement('a');
        link.download = `compare_${ref.replace(/[^a-zA-Z0-9]/g, '_')}.png`;
        link.href = canvas.toDataURL();
        link.textContent = `Télécharger ${ref}`;
        link.style.display = 'block';
        link.style.margin = '5px';
        link.style.padding = '5px';
        link.style.backgroundColor = '#dc3545';
        link.style.color = 'white';
        link.style.textDecoration = 'none';
        link.style.borderRadius = '3px';
        
        document.body.appendChild(link);
    });
    
    console.log('📥 Liens de téléchargement créés pour comparaison');
}

// Fonction pour tester le scan (à utiliser dans la console)
window.testCodeBarres = testCodeBarres;

// Fonctions globales pour la nouvelle solution intelligente
window.testSmartEncoding = function(reference) {
    console.log('🧠 Test de l\'encodage intelligent pour:', reference);
    
    if (modalArticles) {
        const analysis = modalArticles.analyzeAndOptimizeReference(reference);
        console.log('📊 Analyse complète:', analysis);
        
        // Générer le code-barres
        const barcodeUrl = modalArticles.generateCode128Barcode(reference);
        
        // Créer un lien de téléchargement
        const link = document.createElement('a');
        link.download = `smart_${reference.replace(/[^a-zA-Z0-9]/g, '_')}.png`;
        link.href = barcodeUrl;
        link.textContent = `Télécharger ${analysis.optimized}`;
        link.style.display = 'block';
        link.style.margin = '10px';
        link.style.padding = '10px';
        link.style.backgroundColor = '#28a745';
        link.style.color = 'white';
        link.style.textDecoration = 'none';
        link.style.borderRadius = '5px';
        
        document.body.appendChild(link);
        
        // Afficher le mapping si nécessaire
        if (analysis.abbreviation) {
            modalArticles.showAbbreviationMapping();
        }
        
        return analysis;
    } else {
        console.error('modalArticles non défini');
    }
};

window.resolveScannedCode = function(scannedCode) {
    console.log('🔍 Résolution du code scanné:', scannedCode);
    
    if (modalArticles) {
        const original = modalArticles.getOriginalReference(scannedCode);
        console.log('✅ Référence originale:', original);
        return original;
    } else {
        console.error('modalArticles non défini');
    }
};

window.showAllMappings = function() {
    if (modalArticles) {
        modalArticles.showAbbreviationMapping();
    } else {
        console.error('modalArticles non défini');
    }
};
