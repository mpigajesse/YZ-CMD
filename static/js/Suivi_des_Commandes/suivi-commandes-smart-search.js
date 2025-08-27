/**
 * Système de recherche intelligente générique pour toutes les pages de suivi des commandes
 * Adaptable pour : Suivi Confirmées, Suivi À Imprimer, Suivi En Préparation, Suivi Retournées, Suivi Livrées Partiellement
 */

// Système de recherche intelligente générique pour le suivi des commandes
class SuiviCommandesSmartSearch {
    constructor(config = {}) {
        this.pageType = config.pageType || 'generic'; // confirmées, a_imprimer, en_preparation, retournées, livrees_partiellement
        this.searchInput = document.getElementById('smartSearch');
        this.advancedSearch = document.getElementById('advancedSearch');
        this.resultsDiv = document.getElementById('searchResults');
        this.resultCount = document.getElementById('resultCount');
        this.rows = document.querySelectorAll('.commande-row');
        
        // Configuration des filtres selon le type de page
        this.filters = this.getDefaultFilters();
        this.filterConfig = this.getFilterConfig();
        
        this.init();
    }
    
    getDefaultFilters() {
        return {
            idYz: '',
            numCmd: '',
            client: '',
            phone: '',
            email: '',
            villeClient: '',
            villeRegion: '',
            adresse: '',
            dateCommande: '',
            dateConfirmation: '',
            dateAffectation: '',
            datePreparation: '',
            dateLivraison: '',
            totalMin: '',
            totalMax: '',
            etat: '',
            operateur: '',
            statut: ''
        };
    }
    
    getFilterConfig() {
        const configs = {
            confirmées: {
                title: 'Suivi des Commandes Confirmées',
                filters: ['idYz', 'numCmd', 'client', 'phone', 'email', 'villeClient', 'villeRegion', 'dateConfirmation', 'totalMin', 'totalMax', 'operateur'],
                dateField: 'dateConfirmation',
                dateLabel: 'Date Confirmation'
            },
            a_imprimer: {
                title: 'Suivi des Commandes À Imprimer',
                filters: ['idYz', 'numCmd', 'client', 'phone', 'email', 'villeClient', 'villeRegion', 'dateAffectation', 'totalMin', 'totalMax', 'operateur'],
                dateField: 'dateAffectation',
                dateLabel: 'Date Affectation'
            },
            en_preparation: {
                title: 'Suivi des Commandes En Préparation',
                filters: ['idYz', 'numCmd', 'client', 'phone', 'email', 'villeClient', 'villeRegion', 'datePreparation', 'totalMin', 'totalMax', 'operateur'],
                dateField: 'datePreparation',
                dateLabel: 'Date Préparation'
            },
            retournées: {
                title: 'Suivi des Commandes Retournées',
                filters: ['idYz', 'numCmd', 'client', 'phone', 'email', 'villeClient', 'villeRegion', 'dateLivraison', 'totalMin', 'totalMax', 'operateur', 'statut'],
                dateField: 'dateLivraison',
                dateLabel: 'Date Retour'
            },
            livrees_partiellement: {
                title: 'Suivi des Commandes Livrées Partiellement',
                filters: ['idYz', 'numCmd', 'client', 'phone', 'email', 'villeClient', 'villeRegion', 'dateLivraison', 'totalMin', 'totalMax', 'operateur', 'statut'],
                dateField: 'dateLivraison',
                dateLabel: 'Date Livraison'
            },
            generic: {
                title: 'Suivi des Commandes',
                filters: ['idYz', 'numCmd', 'client', 'phone', 'email', 'villeClient', 'villeRegion', 'dateCommande', 'totalMin', 'totalMax', 'etat', 'operateur'],
                dateField: 'dateCommande',
                dateLabel: 'Date Commande'
            }
        };
        
        return configs[this.pageType] || configs.generic;
    }
    
    init() {
        // Recherche en temps réel
        if (this.searchInput) {
            this.searchInput.addEventListener('input', (e) => {
                this.performSmartSearch(e.target.value);
            });
        }
        
        // Fermer les filtres avancés en cliquant à l'extérieur
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#advancedSearch') && !e.target.closest('[onclick*="toggleAdvancedSearch"]')) {
                if (this.advancedSearch) {
                    this.advancedSearch.classList.add('hidden');
                }
            }
        });
        
        // Initialiser les filtres
        this.initFilters();
        
        console.log(`🔍 Système de recherche intelligente ${this.pageType} initialisé`);
    }
    
    initFilters() {
        // Écouter les changements dans les filtres avancés
        const filterInputs = [
            'filterIdYz', 'filterNumCmd', 'filterClient', 'filterPhone', 
            'filterEmail', 'filterVilleClient', 'filterVilleRegion', 'filterAdresse',
            'filterDateCommande', 'filterDateConfirmation', 'filterDateAffectation',
            'filterDatePreparation', 'filterDateLivraison', 'filterTotalMin', 
            'filterTotalMax', 'filterEtat', 'filterOperateur', 'filterStatut'
        ];
        
        filterInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('input', () => {
                    this.updateFilters();
                });
            }
        });
    }
    
    updateFilters() {
        this.filters = {
            idYz: this.getInputValue('filterIdYz').toLowerCase(),
            numCmd: this.getInputValue('filterNumCmd').toLowerCase(),
            client: this.getInputValue('filterClient').toLowerCase(),
            phone: this.getInputValue('filterPhone').toLowerCase(),
            email: this.getInputValue('filterEmail').toLowerCase(),
            villeClient: this.getInputValue('filterVilleClient').toLowerCase(),
            villeRegion: this.getInputValue('filterVilleRegion').toLowerCase(),
            adresse: this.getInputValue('filterAdresse').toLowerCase(),
            dateCommande: this.getInputValue('filterDateCommande'),
            dateConfirmation: this.getInputValue('filterDateConfirmation'),
            dateAffectation: this.getInputValue('filterDateAffectation'),
            datePreparation: this.getInputValue('filterDatePreparation'),
            dateLivraison: this.getInputValue('filterDateLivraison'),
            totalMin: parseFloat(this.getInputValue('filterTotalMin')) || 0,
            totalMax: parseFloat(this.getInputValue('filterTotalMax')) || Infinity,
            etat: this.getInputValue('filterEtat').toLowerCase(),
            operateur: this.getInputValue('filterOperateur').toLowerCase(),
            statut: this.getInputValue('filterStatut').toLowerCase()
        };
        
        this.applyAllFilters();
    }
    
    getInputValue(id) {
        const element = document.getElementById(id);
        return element ? element.value : '';
    }
    
    performSmartSearch(query) {
        if (!query.trim()) {
            this.showAllRows();
            this.hideResults();
            return;
        }
        
        const searchTerm = query.toLowerCase();
        let matchCount = 0;
        
        this.rows.forEach(row => {
            const matches = this.checkRowMatch(row, searchTerm);
            
            if (matches) {
                row.style.display = '';
                row.classList.add('bg-yellow-50');
                matchCount++;
            } else {
                row.style.display = 'none';
                row.classList.remove('bg-yellow-50');
            }
        });
        
        this.showResults(matchCount);
        console.log(`🔍 Recherche ${this.pageType}: "${query}" - ${matchCount} résultat(s)`);
    }
    
    checkRowMatch(row, searchTerm) {
        const fields = [
            'idYz', 'numCmd', 'client', 'phone', 'email', 'villeClient', 
            'villeRegion', 'adresse', 'dateCommande', 'dateConfirmation',
            'dateAffectation', 'datePreparation', 'dateLivraison', 'etat', 
            'operateur', 'statut'
        ];
        
        for (const field of fields) {
            const value = row.dataset[field]?.toLowerCase() || '';
            if (value.includes(searchTerm)) {
                return true;
            }
        }
        
        // Vérifier aussi le total
        const total = parseFloat(row.dataset.total) || 0;
        if (total.toString().includes(searchTerm)) {
            return true;
        }
        
        return false;
    }
    
    applyAllFilters() {
        let matchCount = 0;
        
        this.rows.forEach(row => {
            const matchesFilters = this.checkRowFilters(row);
            
            if (matchesFilters) {
                row.style.display = '';
                row.classList.add('bg-blue-50');
                matchCount++;
            } else {
                row.style.display = 'none';
                row.classList.remove('bg-blue-50');
            }
        });
        
        this.showResults(matchCount);
        console.log(`🎯 Filtres ${this.pageType} appliqués - ${matchCount} résultat(s)`);
    }
    
    checkRowFilters(row) {
        // Vérifier tous les filtres actifs
        for (const [filterKey, filterValue] of Object.entries(this.filters)) {
            if (filterValue === '' || filterValue === 0 || filterValue === Infinity) {
                continue; // Filtre vide, on passe
            }
            
            const rowValue = row.dataset[filterKey];
            
            if (filterKey === 'totalMin' || filterKey === 'totalMax') {
                const total = parseFloat(row.dataset.total) || 0;
                if (filterKey === 'totalMin' && total < filterValue) return false;
                if (filterKey === 'totalMax' && total > filterValue) return false;
            } else if (filterKey.includes('date') && filterValue) {
                if (!this.checkDateFilter(rowValue, filterValue)) return false;
            } else {
                const rowValueLower = rowValue?.toLowerCase() || '';
                if (!rowValueLower.includes(filterValue.toLowerCase())) return false;
            }
        }
        
        return true;
    }
    
    checkDateFilter(dateStr, filterDate) {
        if (!dateStr) return false;
        
        // Conversion du format d/m/Y vers Date pour comparaison
        const [day, month, year] = dateStr.split('/');
        const rowDate = new Date(year, month - 1, day);
        const filterDateObj = new Date(filterDate);
        
        // Comparaison simple (même jour)
        return rowDate.toDateString() === filterDateObj.toDateString();
    }
    
    showAllRows() {
        this.rows.forEach(row => {
            row.style.display = '';
            row.classList.remove('bg-yellow-50', 'bg-blue-50');
        });
    }
    
    showResults(count) {
        if (this.resultCount) {
            this.resultCount.textContent = count;
        }
        if (this.resultsDiv) {
            this.resultsDiv.classList.remove('hidden');
        }
    }
    
    hideResults() {
        if (this.resultsDiv) {
            this.resultsDiv.classList.add('hidden');
        }
    }
    
    clearAll() {
        if (this.searchInput) {
            this.searchInput.value = '';
        }
        this.showAllRows();
        this.hideResults();
        this.clearFilters();
        console.log(`🧹 Recherche ${this.pageType} effacée`);
    }
    
    clearFilters() {
        const filterInputs = [
            'filterIdYz', 'filterNumCmd', 'filterClient', 'filterPhone', 
            'filterEmail', 'filterVilleClient', 'filterVilleRegion', 'filterAdresse',
            'filterDateCommande', 'filterDateConfirmation', 'filterDateAffectation',
            'filterDatePreparation', 'filterDateLivraison', 'filterTotalMin', 
            'filterTotalMax', 'filterEtat', 'filterOperateur', 'filterStatut'
        ];
        
        filterInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) input.value = '';
        });
        
        this.filters = this.getDefaultFilters();
        this.showAllRows();
    }
}

// Variables globales
let suiviCommandesSmartSearch;

// Fonctions globales pour l'interface
function toggleAdvancedSearch() {
    const advancedSearch = document.getElementById('advancedSearch');
    if (advancedSearch) {
        advancedSearch.classList.toggle('hidden');
        console.log('🔧 Filtres avancés:', advancedSearch.classList.contains('hidden') ? 'fermés' : 'ouverts');
    }
}

function clearSmartSearch() {
    if (suiviCommandesSmartSearch) {
        suiviCommandesSmartSearch.searchInput.value = '';
        suiviCommandesSmartSearch.showAllRows();
        suiviCommandesSmartSearch.hideResults();
    }
}

function clearAllSearch() {
    if (suiviCommandesSmartSearch) {
        suiviCommandesSmartSearch.clearAll();
    }
}

function applyFilters() {
    if (suiviCommandesSmartSearch) {
        suiviCommandesSmartSearch.updateFilters();
        const advancedSearch = document.getElementById('advancedSearch');
        if (advancedSearch) {
            advancedSearch.classList.add('hidden');
        }
    }
}

function clearFilters() {
    if (suiviCommandesSmartSearch) {
        suiviCommandesSmartSearch.clearFilters();
    }
}

// Fonction d'initialisation générique
function initSuiviCommandesSearch(pageType = 'generic') {
    console.log(`🚀 Initialisation du système de recherche intelligente ${pageType}...`);
    
    // Vérifier que les éléments nécessaires existent
    const requiredElements = ['smartSearch', 'advancedSearch', 'searchResults', 'resultCount'];
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    
    if (missingElements.length > 0) {
        console.warn('⚠️ Éléments manquants pour la recherche:', missingElements);
        return;
    }
    
    // Vérifier qu'il y a des lignes à rechercher
    const rows = document.querySelectorAll('.commande-row');
    if (rows.length === 0) {
        console.warn('⚠️ Aucune ligne de commande trouvée pour la recherche');
        return;
    }
    
    // Initialiser le système de recherche
    suiviCommandesSmartSearch = new SuiviCommandesSmartSearch({ pageType });
    
    // Ajouter des raccourcis clavier
    document.addEventListener('keydown', function(e) {
        // Ctrl+F pour focus sur la recherche
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.getElementById('smartSearch');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
                console.log('⌨️ Raccourci Ctrl+F activé');
            }
        }
        
        // Échap pour effacer la recherche
        if (e.key === 'Escape') {
            clearSmartSearch();
            console.log('⌨️ Raccourci Échap activé');
        }
        
        // Entrée pour appliquer les filtres
        if (e.key === 'Enter' && e.target.closest('#advancedSearch')) {
            applyFilters();
            console.log('⌨️ Raccourci Entrée pour appliquer les filtres');
        }
    });
    
    console.log(`✅ Système de recherche intelligente ${pageType} initialisé avec succès`);
    console.log(`📊 ${rows.length} lignes de commande disponibles pour la recherche`);
}

// Initialiser quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    // Détecter automatiquement le type de page basé sur l'URL ou le titre
    let pageType = 'generic';
    
    if (window.location.pathname.includes('confirmees')) {
        pageType = 'confirmées';
    } else if (window.location.pathname.includes('a_imprimer')) {
        pageType = 'a_imprimer';
    } else if (window.location.pathname.includes('en_preparation')) {
        pageType = 'en_preparation';
    } else if (window.location.pathname.includes('retournees')) {
        pageType = 'retournées';
    } else if (window.location.pathname.includes('livrees_partiellement')) {
        pageType = 'livrees_partiellement';
    }
    
    initSuiviCommandesSearch(pageType);
});

// Fonctions utilitaires pour le debug
window.debugSuiviCommandesSearch = function() {
    if (suiviCommandesSmartSearch) {
        console.log('🔍 État du système de recherche:');
        console.log('  - Type de page:', suiviCommandesSmartSearch.pageType);
        console.log('  - Filtres actifs:', suiviCommandesSmartSearch.filters);
        console.log('  - Lignes totales:', suiviCommandesSmartSearch.rows.length);
        console.log('  - Lignes visibles:', Array.from(suiviCommandesSmartSearch.rows).filter(row => row.style.display !== 'none').length);
    } else {
        console.log('❌ Système de recherche non initialisé');
    }
};

// Exporter pour utilisation externe
window.SuiviCommandesSmartSearch = SuiviCommandesSmartSearch;
window.initSuiviCommandesSearch = initSuiviCommandesSearch;
