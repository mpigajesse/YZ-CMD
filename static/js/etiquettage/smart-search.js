/**
 * Système de recherche intelligente pour les étiquettes d'articles
 * Permet une recherche avancée et indépendante dans toutes les colonnes
 */

// Système de recherche intelligente
class SmartSearch {
    constructor() {
        this.searchInput = document.getElementById('smartSearch');
        this.advancedSearch = document.getElementById('advancedSearch');
        this.resultsDiv = document.getElementById('searchResults');
        this.resultCount = document.getElementById('resultCount');
        this.rows = document.querySelectorAll('.commande-row');
        this.filters = {
            id: '',
            client: '',
            phone: '',
            city: '',
            totalMin: '',
            totalMax: ''
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
        
        console.log('🔍 Système de recherche intelligente initialisé');
    }
    
    initFilters() {
        // Écouter les changements dans les filtres avancés
        const filterInputs = ['filterId', 'filterClient', 'filterPhone', 'filterCity', 'filterTotalMin', 'filterTotalMax'];
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
            id: document.getElementById('filterId').value.toLowerCase(),
            client: document.getElementById('filterClient').value.toLowerCase(),
            phone: document.getElementById('filterPhone').value.toLowerCase(),
            city: document.getElementById('filterCity').value.toLowerCase(),
            totalMin: parseFloat(document.getElementById('filterTotalMin').value) || 0,
            totalMax: parseFloat(document.getElementById('filterTotalMax').value) || Infinity
        };
        
        this.applyAllFilters();
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
            const id = row.dataset.id.toLowerCase();
            const client = row.dataset.client.toLowerCase();
            const phone = row.dataset.phone.toLowerCase();
            const city = row.dataset.city.toLowerCase();
            const total = parseFloat(row.dataset.total);
            const date = row.dataset.date.toLowerCase();
            
            // Recherche intelligente dans tous les champs
            const matches = 
                id.includes(searchTerm) ||
                client.includes(searchTerm) ||
                phone.includes(searchTerm) ||
                city.includes(searchTerm) ||
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
        console.log(`🔍 Recherche: "${query}" - ${matchCount} résultat(s)`);
    }
    
    applyAllFilters() {
        let matchCount = 0;
        
        this.rows.forEach(row => {
            const id = row.dataset.id.toLowerCase();
            const client = row.dataset.client.toLowerCase();
            const phone = row.dataset.phone.toLowerCase();
            const city = row.dataset.city.toLowerCase();
            const total = parseFloat(row.dataset.total);
            
            // Vérifier tous les filtres
            const matchesFilters = 
                (this.filters.id === '' || id.includes(this.filters.id)) &&
                (this.filters.client === '' || client.includes(this.filters.client)) &&
                (this.filters.phone === '' || phone.includes(this.filters.phone)) &&
                (this.filters.city === '' || city.includes(this.filters.city)) &&
                total >= this.filters.totalMin &&
                total <= this.filters.totalMax;
            
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
        console.log(`🎯 Filtres appliqués - ${matchCount} résultat(s)`);
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
        console.log('🧹 Recherche effacée');
    }
    
    clearFilters() {
        const filterInputs = ['filterId', 'filterClient', 'filterPhone', 'filterCity', 'filterTotalMin', 'filterTotalMax'];
        filterInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) input.value = '';
        });
        
        this.filters = {
            id: '',
            client: '',
            phone: '',
            city: '',
            totalMin: 0,
            totalMax: Infinity
        };
        
        this.showAllRows();
    }
}

// Initialiser la recherche intelligente
let smartSearch;

// Fonctions globales pour l'interface
function toggleAdvancedSearch() {
    const advancedSearch = document.getElementById('advancedSearch');
    advancedSearch.classList.toggle('hidden');
    console.log('🔧 Filtres avancés:', advancedSearch.classList.contains('hidden') ? 'fermés' : 'ouverts');
}

function clearSmartSearch() {
    if (smartSearch) {
        smartSearch.searchInput.value = '';
        smartSearch.showAllRows();
        smartSearch.hideResults();
    }
}

function clearAllSearch() {
    if (smartSearch) {
        smartSearch.clearAll();
    }
}

function applyFilters() {
    if (smartSearch) {
        smartSearch.updateFilters();
        document.getElementById('advancedSearch').classList.add('hidden');
    }
}

function clearFilters() {
    if (smartSearch) {
        smartSearch.clearFilters();
    }
}

// Initialiser quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initialisation du système de recherche intelligente...');
    
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
    smartSearch = new SmartSearch();
    
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
    
    console.log('✅ Système de recherche intelligente initialisé avec succès');
    console.log(`📊 ${rows.length} lignes de commande disponibles pour la recherche`);
});

// Fonctions utilitaires pour le debug
window.debugSearch = function() {
    if (smartSearch) {
        console.log('🔍 État du système de recherche:');
        console.log('  - Filtres actifs:', smartSearch.filters);
        console.log('  - Lignes totales:', smartSearch.rows.length);
        console.log('  - Lignes visibles:', Array.from(smartSearch.rows).filter(row => row.style.display !== 'none').length);
    } else {
        console.log('❌ Système de recherche non initialisé');
    }
};

// Exporter pour utilisation externe
window.SmartSearch = SmartSearch;
