
class VariantesManager {
    constructor() {
        this.variantesCount = 0;
        this.variantes = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateVariantesDisplay();
    }

    bindEvents() {
        // Fermer le modal en cliquant à l'extérieur
        const modal = document.getElementById('varianteModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeVarianteModal();
                }
            });
        }
        
        // Écouter les changements dans le modal pour mettre à jour l'aperçu de la référence
        const couleurSelect = document.getElementById('modal_couleur');
        const pointureSelect = document.getElementById('modal_pointure');
        
        if (couleurSelect) {
            couleurSelect.addEventListener('change', () => this.updateReferencePreview());
        }
        
        if (pointureSelect) {
            pointureSelect.addEventListener('change', () => this.updateReferencePreview());
        }
    }

    openVarianteModal() {
        const modal = document.getElementById('varianteModal');
        if (modal) {
            modal.classList.remove('hidden');
            // Réinitialiser le formulaire
            const form = document.getElementById('varianteForm');
            if (form) {
                form.reset();
            }
            // Mettre à jour l'aperçu de la référence
            this.updateReferencePreview();
        }
    }

    closeVarianteModal() {
        const modal = document.getElementById('varianteModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    addVariante() {
        const couleurSelect = document.getElementById('modal_couleur');
        const pointureSelect = document.getElementById('modal_pointure');
        const quantiteInput = document.getElementById('modal_quantite');

        if (!couleurSelect || !pointureSelect || !quantiteInput) {
            console.error('Éléments du formulaire non trouvés');
            return;
        }

        const couleur = couleurSelect.value;
        const pointure = pointureSelect.value;
        const quantite = quantiteInput.value || 0;

        // Vérifier qu'au moins une couleur ou une pointure est sélectionnée
        if (!couleur && !pointure) {
            this.showAlert('Veuillez sélectionner au moins une couleur ou une pointure.', 'warning');
            return;
        }

        // Créer l'objet variante
        const variante = {
            id: this.variantesCount++,
            couleur: couleur,
            pointure: pointure,
            quantite: quantite,
            couleur_nom: couleur ? couleurSelect.options[couleurSelect.selectedIndex].text : '',
            pointure_nom: pointure ? pointureSelect.options[pointureSelect.selectedIndex].text : ''
        };

        // Vérifier si cette combinaison existe déjà
        const exists = this.variantes.some(v => 
            v.couleur === variante.couleur && 
            v.pointure === variante.pointure
        );

        if (exists) {
            this.showAlert('Cette combinaison couleur/pointure existe déjà.', 'error');
            return;
        }

        this.variantes.push(variante);
        this.updateVariantesDisplay();
        this.closeVarianteModal();

        // Les variantes seront envoyées via AJAX, pas besoin de champs cachés

        // Message de succès
        this.showAlert('Variante ajoutée avec succès !', 'success');
    }

    removeVariante(id) {
        this.variantes = this.variantes.filter(v => v.id !== id);
        this.updateVariantesDisplay();

        // Avec AJAX, pas besoin de supprimer les champs cachés

        // Message de confirmation
        this.showAlert('Variante supprimée avec succès !', 'success');
    }

    updateVariantesDisplay() {
        const container = document.getElementById('variantesContainer');
        if (!container) return;

        if (this.variantes.length === 0) {
            container.innerHTML = `
                <div class="variantes-empty-state">
                    <i class="fas fa-tags"></i>
                    <p class="text-sm text-gray-600 italic">Aucune variante ajoutée pour le moment. Cliquez sur "Ajouter une variante" pour en créer.</p>
                </div>
            `;
            return;
        }

        let html = '<div class="space-y-3">';
        this.variantes.forEach(variante => {
            // Générer la référence pour l'affichage
            const referenceVariante = this.genererReferenceVariante(variante);
            
            // Debug: afficher la référence dans la console
            console.log('Variante:', variante);
            console.log('Référence générée:', referenceVariante);
            
            html += `
                <div class="variante-item flex items-center justify-between bg-white p-3 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-all">
                    <div class="flex items-center space-x-4">
                        <div class="flex items-center space-x-2">
                            <i class="fas fa-tags text-[#66cccc]"></i>
                            <span class="text-sm font-medium" style="color: #023535;">
                                ${variante.couleur_nom || 'Aucune couleur'} / ${variante.pointure_nom || 'Aucune pointure'}
                            </span>
                        </div>
                        <div class="flex items-center space-x-2">
                            <i class="fas fa-boxes text-[#66cccc]"></i>
                            <span class="quantite-badge">Quantité: ${variante.quantite}</span>
                        </div>
                        <div class="flex items-center space-x-2">
                            <i class="fas fa-barcode text-[#66cccc]"></i>
                            <span class="variante-reference">
                                ${referenceVariante || 'Référence non générée'}
                            </span>
                        </div>
                    </div>
                    <button type="button" onclick="variantesManager.removeVariante(${variante.id})" 
                            class="text-red-500 hover:text-red-700 p-2 rounded-full hover:bg-red-50 transition-colors"
                            title="Supprimer cette variante">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
        });
        html += '</div>';

        container.innerHTML = html;
    }

    addHiddenFields(variante) {
        const form = document.getElementById('articleForm');
        if (!form) return;

        // Générer la référence de la variante
        const referenceVariante = this.genererReferenceVariante(variante);

        // Ajouter les champs cachés pour cette variante
        const fields = [
            { name: `variante_${variante.id}_couleur`, value: variante.couleur },
            { name: `variante_${variante.id}_pointure`, value: variante.pointure },
            { name: `variante_${variante.id}_quantite`, value: variante.quantite },
            { name: `variante_${variante.id}_reference`, value: referenceVariante }
        ];

        fields.forEach(field => {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = field.name;
            input.value = field.value;
            form.appendChild(input);
        });
    }

    removeHiddenFields(varianteId) {
        const form = document.getElementById('articleForm');
        if (!form) return;

        const fields = form.querySelectorAll(`[name^="variante_${varianteId}_"]`);
        fields.forEach(field => field.remove());
    }

    showAlert(message, type = 'info') {
        // Créer une notification toast
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full toast-notification`;
        
        // Couleurs selon le type
        const colors = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            warning: 'bg-yellow-500 text-white',
            info: 'bg-blue-500 text-white'
        };
        
        toast.className += ` ${colors[type] || colors.info}`;
        
        toast.innerHTML = `
            <div class="flex items-center space-x-2">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Animation d'entrée
        setTimeout(() => {
            toast.classList.remove('translate-x-full');
        }, 100);
        
        // Auto-suppression après 3 secondes
        setTimeout(() => {
            toast.classList.add('hiding');
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }

    // Méthode pour récupérer toutes les variantes (utile pour la validation)
    getVariantes() {
        return this.variantes;
    }

    // Méthode pour vider toutes les variantes
    clearVariantes() {
        this.variantes = [];
        this.variantesCount = 0;
        this.updateVariantesDisplay();
        
        // Supprimer tous les champs cachés
        const form = document.getElementById('articleForm');
        if (form) {
            const fields = form.querySelectorAll('[name^="variante_"]');
            fields.forEach(field => field.remove());
        }
    }

    // Méthode pour afficher un résumé des variantes
    showVariantesSummary() {
        if (this.variantes.length === 0) {
            return "Aucune variante ajoutée";
        }
        
        let summary = `Résumé des ${this.variantes.length} variante(s) :\n\n`;
        this.variantes.forEach((variante, index) => {
            const couleur = variante.couleur_nom || 'Aucune couleur';
            const pointure = variante.pointure_nom || 'Aucune pointure';
            const quantite = variante.quantite;
            const reference = this.genererReferenceVariante(variante);
            
            summary += `${index + 1}. ${couleur} / ${pointure}\n`;
            summary += `   Quantité: ${quantite}\n`;
            summary += `   Référence: ${reference}\n\n`;
        });
        
        return summary;
    }

    // Méthode pour soumettre le formulaire avec AJAX
    async submitFormWithAjax(form) {
        try {
            // Afficher un indicateur de chargement
            this.showLoadingIndicator(true);
            
            // 1. Créer d'abord l'article
            const formData = new FormData(form);
            
            const articleResponse = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const articleResult = await articleResponse.json();
            
            if (!articleResult.success) {
                throw new Error(articleResult.error || 'Erreur lors de la création de l\'article');
            }
            
            this.showAlert('Article créé avec succès !', 'success');
            
            // 2. Créer les variantes si il y en a
            if (this.variantes.length > 0) {
                const variantesData = this.variantes.map(variante => ({
                    couleur_id: variante.couleur || null,
                    pointure_id: variante.pointure || null,
                    quantite: parseInt(variante.quantite) || 0,
                    reference: this.genererReferenceVariante(variante)
                }));
                
                const variantesResponse = await fetch('/Superpreparation/stock/variantes/creer-ajax/', {
                    method: 'POST',
                    body: JSON.stringify({
                        article_id: articleResult.article_id,
                        variantes: variantesData
                    }),
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': this.getCSRFToken()
                    }
                });
                
                const variantesResult = await variantesResponse.json();
                
                if (variantesResult.success) {
                    this.showAlert(`${variantesResult.nombre_crees} variante(s) créée(s) avec succès !`, 'success');
                    
                    // Afficher les erreurs s'il y en a
                    if (variantesResult.erreurs && variantesResult.erreurs.length > 0) {
                        variantesResult.erreurs.forEach(erreur => {
                            this.showAlert(erreur, 'warning');
                        });
                    }
                } else {
                    throw new Error(variantesResult.error || 'Erreur lors de la création des variantes');
                }
            }
            
            // 3. Rediriger vers la liste des articles après un délai
            setTimeout(() => {
                window.location.href = '/article/';
            }, 2000);
            
        } catch (error) {
            console.error('Erreur:', error);
            this.showAlert(`Erreur: ${error.message}`, 'error');
        } finally {
            this.showLoadingIndicator(false);
        }
    }

    // Méthode pour créer les variantes via AJAX en mode modification
    async createVariantesForModification(articleId) {
        try {
            if (this.variantes.length === 0) {
                return { success: true, message: 'Aucune variante à créer' };
            }

            const variantesData = this.variantes.map(variante => ({
                couleur_id: variante.couleur || null,
                pointure_id: variante.pointure || null,
                quantite: parseInt(variante.quantite) || 0,
                reference: this.genererReferenceVariante(variante)
            }));
            
            const response = await fetch('/Superpreparation/stock/variantes/creer-ajax/', {
                method: 'POST',
                body: JSON.stringify({
                    article_id: articleId,
                    variantes: variantesData
                }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert(`${result.nombre_crees} variante(s) créée(s) avec succès !`, 'success');
                
                // Afficher les erreurs s'il y en a
                if (result.erreurs && result.erreurs.length > 0) {
                    result.erreurs.forEach(erreur => {
                        this.showAlert(erreur, 'warning');
                    });
                }
                
                return result;
            } else {
                throw new Error(result.error || 'Erreur lors de la création des variantes');
            }
            
        } catch (error) {
            console.error('Erreur lors de la création des variantes:', error);
            this.showAlert(`Erreur: ${error.message}`, 'error');
            return { success: false, error: error.message };
        }
    }

    // Méthode pour obtenir le token CSRF
    getCSRFToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        return tokenElement ? tokenElement.value : '';
    }

    // Méthode pour afficher/masquer l'indicateur de chargement
    showLoadingIndicator(show) {
        const submitButton = document.querySelector('button[type="submit"]');
        if (submitButton) {
            if (show) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Création en cours...';
            } else {
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="fas fa-plus mr-2"></i>Créer l\'Article';
            }
        }
    }

    // Méthode pour valider le formulaire avant soumission
    validateForm() {
        if (this.variantes.length === 0) {
            this.showAlert('Veuillez ajouter au moins une variante pour cet article.', 'warning');
            return false;
        }
        
        // Vérifier que chaque variante a au moins une couleur ou une pointure
        for (let variante of this.variantes) {
            if (!variante.couleur && !variante.pointure) {
                this.showAlert('Chaque variante doit avoir au moins une couleur ou une pointure.', 'error');
                return false;
            }
        }
        
        // Afficher un résumé des variantes
        const summary = this.showVariantesSummary();
        console.log('Résumé des variantes:', summary);
        
        return true;
    }

    genererReferenceVariante(variante) {
        // Debug: afficher les paramètres d'entrée
        console.log('genererReferenceVariante appelée avec:', variante);
        
        // Récupérer les valeurs du formulaire principal
        const categorieSelect = document.getElementById('id_categorie');
        const genreSelect = document.getElementById('id_genre');
        const modeleInput = document.getElementById('id_modele');
        
        console.log('Éléments trouvés:', {
            categorieSelect: !!categorieSelect,
            genreSelect: !!genreSelect,
            modeleInput: !!modeleInput
        });
        
        if (!categorieSelect || !genreSelect || !modeleInput) {
            console.log('Éléments manquants, retour vide');
            return '';
        }

        const categorie = categorieSelect.options[categorieSelect.selectedIndex]?.text || '';
        const genre = genreSelect.options[genreSelect.selectedIndex]?.text || '';
        const modele = modeleInput.value || '';

        console.log('Valeurs récupérées:', { categorie, genre, modele });

        if (!categorie || !genre || !modele) {
            console.log('Valeurs manquantes, retour vide');
            return '';
        }

        // Nettoyer les valeurs pour éviter les caractères spéciaux
        const categorieClean = categorie.replace(/[éèàç\s]/g, (match) => {
            const replacements = { 'é': 'e', 'è': 'e', 'à': 'a', 'ç': 'c', ' ': '-' };
            return replacements[match] || match;
        }).toUpperCase();

        const genreClean = genre.replace(/[éèàç\s]/g, (match) => {
            const replacements = { 'é': 'e', 'è': 'e', 'à': 'a', 'ç': 'c', ' ': '-' };
            return replacements[match] || match;
        }).toUpperCase();

        // Générer la référence de l'article
        const referenceArticle = `${categorieClean}-${genreClean}-YZ-${modele}`;
        console.log('Référence article:', referenceArticle);

        // Générer la référence de la variante
        let referenceVariante = referenceArticle;
        
        if (variante.couleur_nom) {
            const couleurClean = variante.couleur_nom.replace(/[éèàç\s]/g, (match) => {
                const replacements = { 'é': 'e', 'è': 'e', 'à': 'a', 'ç': 'c', ' ': '-' };
                return replacements[match] || match;
            }).toUpperCase();
            referenceVariante += `-${couleurClean}`;
            console.log('Couleur ajoutée:', couleurClean);
        }
        
        if (variante.pointure_nom) {
            const pointureClean = variante.pointure_nom.replace(/[éèàç\s]/g, (match) => {
                const replacements = { 'é': 'e', 'è': 'e', 'à': 'a', 'ç': 'c', ' ': '-' };
                return replacements[match] || match;
            }).toUpperCase();
            referenceVariante += `-${pointureClean}`;
            console.log('Pointure ajoutée:', pointureClean);
        }

        console.log('Référence finale:', referenceVariante);
        return referenceVariante;
    }

    updateReferencePreview() {
        const couleurSelect = document.getElementById('modal_couleur');
        const pointureSelect = document.getElementById('modal_pointure');
        const referencePreview = document.getElementById('referencePreview');
        const referencePreviewText = document.getElementById('referencePreviewText');

        if (!couleurSelect || !pointureSelect || !referencePreview || !referencePreviewText) {
            return;
        }

        const couleur = couleurSelect.value;
        const pointure = pointureSelect.value;

        // Créer un objet variante temporaire pour générer la référence
        const varianteTemp = {
            couleur_nom: couleur ? couleurSelect.options[couleurSelect.selectedIndex].text : '',
            pointure_nom: pointure ? pointureSelect.options[pointureSelect.selectedIndex].text : ''
        };

        const referenceVariante = this.genererReferenceVariante(varianteTemp);

        if (referenceVariante && (couleur || pointure)) {
            referencePreviewText.textContent = referenceVariante;
            referencePreview.classList.remove('hidden');
        } else {
            referencePreview.classList.add('hidden');
        }
    }
}

// Initialiser le gestionnaire de variantes quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    window.variantesManager = new VariantesManager();
    
    // Ajouter la gestion AJAX au formulaire principal
    const form = document.getElementById('articleForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault(); // Empêcher la soumission normale
            
            if (window.variantesManager && !window.variantesManager.validateForm()) {
                return false;
            }
            
            // Soumettre via AJAX
            window.variantesManager.submitFormWithAjax(form);
        });
    }
    
    // Écouter les changements dans le formulaire principal pour mettre à jour l'aperçu de la référence
    const categorieSelect = document.getElementById('id_categorie');
    const genreSelect = document.getElementById('id_genre');
    const modeleInput = document.getElementById('id_modele');
    
    if (categorieSelect) {
        categorieSelect.addEventListener('change', () => {
            if (window.variantesManager) {
                window.variantesManager.updateReferencePreview();
            }
        });
    }
    
    if (genreSelect) {
        genreSelect.addEventListener('change', () => {
            if (window.variantesManager) {
                window.variantesManager.updateReferencePreview();
            }
        });
    }
    
    if (modeleInput) {
        modeleInput.addEventListener('input', () => {
            if (window.variantesManager) {
                window.variantesManager.updateReferencePreview();
            }
        });
    }
});

// Fonctions globales pour la compatibilité avec les onclick
function openVarianteModal() {
    if (window.variantesManager) {
        window.variantesManager.openVarianteModal();
    }
}

function closeVarianteModal() {
    if (window.variantesManager) {
        window.variantesManager.closeVarianteModal();
    }
}

function addVariante() {
    if (window.variantesManager) {
        window.variantesManager.addVariante();
    }
}
