/**
 * Système de recherche intelligente pour les codes-barres des commandes
 * Permet une recherche avancée et indépendante dans toutes les colonnes
 */

// Système de recherche intelligente pour les commandes
class CommandsSmartSearch {
    constructor() {
        this.searchInput = document.getElementById('smartSearch');
        this.advancedSearch = document.getElementById('advancedSearch');
        this.resultsDiv = document.getElementById('searchResults');
        this.resultCount = document.getElementById('resultCount');
        this.rows = document.querySelectorAll('.commande-row');
        this.filters = {
            idYz: '',
            numCmd: '',
            client: '',
            phone: '',
            villeClient: '',
            villeRegion: '',
            adresse: '',
            totalMin: '',
            totalMax: '',
            dateMin: '',
            dateMax: ''
        };
        
        this.init();
    }
    
    init() {
        // Recherche en temps réel
        this.searchInput.addEventListener('input', (e) => {
            this.performSmartSearch(e.target.value);
        });
        
        // Fermer les filtres avancés en cliquant à l'extérieur
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#advancedSearch') && !e.target.closest('[onclick*="toggleAdvancedSearch"]')) {
                this.advancedSearch.classList.add('hidden');
            }
        });
        
        // Initialiser les filtres
        this.initFilters();
        
        console.log('🔍 Système de recherche intelligente des commandes initialisé');
    }
    
    initFilters() {
        // Écouter les changements dans les filtres avancés
        const filterInputs = [
            'filterIdYz', 'filterNumCmd', 'filterClient', 'filterPhone', 
            'filterVilleClient', 'filterVilleRegion', 'filterAdresse', 
            'filterTotalMin', 'filterTotalMax', 'filterDateMin', 'filterDateMax'
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
            villeClient: this.getInputValue('filterVilleClient').toLowerCase(),
            villeRegion: this.getInputValue('filterVilleRegion').toLowerCase(),
            adresse: this.getInputValue('filterAdresse').toLowerCase(),
            totalMin: parseFloat(this.getInputValue('filterTotalMin')) || 0,
            totalMax: parseFloat(this.getInputValue('filterTotalMax')) || Infinity,
            dateMin: this.getInputValue('filterDateMin'),
            dateMax: this.getInputValue('filterDateMax')
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
            const idYz = row.dataset.idYz?.toLowerCase() || '';
            const numCmd = row.dataset.numCmd?.toLowerCase() || '';
            const client = row.dataset.client?.toLowerCase() || '';
            const phone = row.dataset.phone?.toLowerCase() || '';
            const villeClient = row.dataset.villeClient?.toLowerCase() || '';
            const villeRegion = row.dataset.villeRegion?.toLowerCase() || '';
            const adresse = row.dataset.adresse?.toLowerCase() || '';
            const total = parseFloat(row.dataset.total) || 0;
            const date = row.dataset.date?.toLowerCase() || '';
            
            // Recherche intelligente dans tous les champs
            const matches = 
                idYz.includes(searchTerm) ||
                numCmd.includes(searchTerm) ||
                client.includes(searchTerm) ||
                phone.includes(searchTerm) ||
                villeClient.includes(searchTerm) ||
                villeRegion.includes(searchTerm) ||
                adresse.includes(searchTerm) ||
                date.includes(searchTerm) ||
                total.toString().includes(searchTerm);
            
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
        console.log(`🔍 Recherche commandes: "${query}" - ${matchCount} résultat(s)`);
    }
    
    applyAllFilters() {
        let matchCount = 0;
        
        this.rows.forEach(row => {
            const idYz = row.dataset.idYz?.toLowerCase() || '';
            const numCmd = row.dataset.numCmd?.toLowerCase() || '';
            const client = row.dataset.client?.toLowerCase() || '';
            const phone = row.dataset.phone?.toLowerCase() || '';
            const villeClient = row.dataset.villeClient?.toLowerCase() || '';
            const villeRegion = row.dataset.villeRegion?.toLowerCase() || '';
            const adresse = row.dataset.adresse?.toLowerCase() || '';
            const total = parseFloat(row.dataset.total) || 0;
            const dateStr = row.dataset.date || '';
            
            // Conversion de la date pour comparaison
            const dateMatch = this.checkDateFilter(dateStr);
            
            // Vérifier tous les filtres
            const matchesFilters = 
                (this.filters.idYz === '' || idYz.includes(this.filters.idYz)) &&
                (this.filters.numCmd === '' || numCmd.includes(this.filters.numCmd)) &&
                (this.filters.client === '' || client.includes(this.filters.client)) &&
                (this.filters.phone === '' || phone.includes(this.filters.phone)) &&
                (this.filters.villeClient === '' || villeClient.includes(this.filters.villeClient)) &&
                (this.filters.villeRegion === '' || villeRegion.includes(this.filters.villeRegion)) &&
                (this.filters.adresse === '' || adresse.includes(this.filters.adresse)) &&
                total >= this.filters.totalMin &&
                total <= this.filters.totalMax &&
                dateMatch;
            
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
        console.log(`🎯 Filtres commandes appliqués - ${matchCount} résultat(s)`);
    }
    
    checkDateFilter(dateStr) {
        if (!this.filters.dateMin && !this.filters.dateMax) return true;
        if (!dateStr) return false;
        
        // Conversion du format d/m/Y vers Date pour comparaison
        const [day, month, year] = dateStr.split('/');
        const rowDate = new Date(year, month - 1, day);
        
        let matches = true;
        
        if (this.filters.dateMin) {
            const minDate = new Date(this.filters.dateMin);
            matches = matches && (rowDate >= minDate);
        }
        
        if (this.filters.dateMax) {
            const maxDate = new Date(this.filters.dateMax);
            matches = matches && (rowDate <= maxDate);
        }
        
        return matches;
    }
    
    showAllRows() {
        this.rows.forEach(row => {
            row.style.display = '';
            row.classList.remove('bg-yellow-50', 'bg-blue-50');
        });
    }
    
    showResults(count) {
        this.resultCount.textContent = count;
        this.resultsDiv.classList.remove('hidden');
    }
    
    hideResults() {
        this.resultsDiv.classList.add('hidden');
    }
    
    clearAll() {
        this.searchInput.value = '';
        this.showAllRows();
        this.hideResults();
        this.clearFilters();
        console.log('🧹 Recherche commandes effacée');
    }
    
    clearFilters() {
        const filterInputs = [
            'filterIdYz', 'filterNumCmd', 'filterClient', 'filterPhone', 
            'filterVilleClient', 'filterVilleRegion', 'filterAdresse', 
            'filterTotalMin', 'filterTotalMax', 'filterDateMin', 'filterDateMax'
        ];
        
        filterInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) input.value = '';
        });
        
        this.filters = {
            idYz: '',
            numCmd: '',
            client: '',
            phone: '',
            villeClient: '',
            villeRegion: '',
            adresse: '',
            totalMin: 0,
            totalMax: Infinity,
            dateMin: '',
            dateMax: ''
        };
        
        this.showAllRows();
    }
}

// Initialiser la recherche intelligente des commandes
let commandsSmartSearch;

// Fonctions globales pour l'interface
function toggleAdvancedSearch() {
    const advancedSearch = document.getElementById('advancedSearch');
    advancedSearch.classList.toggle('hidden');
    console.log('🔧 Filtres avancés commandes:', advancedSearch.classList.contains('hidden') ? 'fermés' : 'ouverts');
}

function clearSmartSearch() {
    if (commandsSmartSearch) {
        commandsSmartSearch.searchInput.value = '';
        commandsSmartSearch.showAllRows();
        commandsSmartSearch.hideResults();
    }
}

function clearAllSearch() {
    if (commandsSmartSearch) {
        commandsSmartSearch.clearAll();
    }
}

function applyFilters() {
    if (commandsSmartSearch) {
        commandsSmartSearch.updateFilters();
        document.getElementById('advancedSearch').classList.add('hidden');
    }
}

function clearFilters() {
    if (commandsSmartSearch) {
        commandsSmartSearch.clearFilters();
    }
}

// Initialiser quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initialisation du système de recherche intelligente des commandes...');
    
    // Vérifier que les éléments nécessaires existent
    const requiredElements = ['smartSearch', 'advancedSearch', 'searchResults', 'resultCount'];
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    
    if (missingElements.length > 0) {
        console.warn('⚠️ Éléments manquants pour la recherche commandes:', missingElements);
        return;
    }
    
    // Vérifier qu'il y a des lignes à rechercher
    const rows = document.querySelectorAll('.commande-row');
    if (rows.length === 0) {
        console.warn('⚠️ Aucune ligne de commande trouvée pour la recherche');
        return;
    }
    
    // Initialiser le système de recherche
    commandsSmartSearch = new CommandsSmartSearch();
    
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
    
    console.log('✅ Système de recherche intelligente des commandes initialisé avec succès');
    console.log(`📊 ${rows.length} lignes de commande disponibles pour la recherche`);
});

// Fonctions utilitaires pour le debug
window.debugCommandsSearch = function() {
    if (commandsSmartSearch) {
        console.log('🔍 État du système de recherche des commandes:');
        console.log('  - Filtres actifs:', commandsSmartSearch.filters);
        console.log('  - Lignes totales:', commandsSmartSearch.rows.length);
        console.log('  - Lignes visibles:', Array.from(commandsSmartSearch.rows).filter(row => row.style.display !== 'none').length);
    } else {
        console.log('❌ Système de recherche des commandes non initialisé');
    }
};

// Exporter pour utilisation externe
window.CommandsSmartSearch = CommandsSmartSearch;
