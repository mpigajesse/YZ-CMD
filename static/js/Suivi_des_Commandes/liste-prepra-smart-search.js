/**
 * Système de recherche intelligente pour la page liste_prepa (Suivi Général - Préparation)
 * Permet une recherche avancée et indépendante dans toutes les colonnes
 */

// Système de recherche intelligente pour la liste des préparations
class ListePrepaSmartSearch {
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
            email: '',
            villeClient: '',
            villeRegion: '',
            dateAffectation: '',
            totalMin: '',
            totalMax: '',
            etat: '',
            operateur: ''
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
        
        console.log('🔍 Système de recherche intelligente liste_prepa initialisé');
    }
    
    initFilters() {
        // Écouter les changements dans les filtres avancés
        const filterInputs = [
            'filterIdYz', 'filterNumCmd', 'filterClient', 'filterPhone', 
            'filterEmail', 'filterVilleClient', 'filterVilleRegion', 
            'filterDateAffectation', 'filterTotalMin', 'filterTotalMax',
            'filterEtat', 'filterOperateur'
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
            dateAffectation: this.getInputValue('filterDateAffectation'),
            totalMin: parseFloat(this.getInputValue('filterTotalMin')) || 0,
            totalMax: parseFloat(this.getInputValue('filterTotalMax')) || Infinity,
            etat: this.getInputValue('filterEtat').toLowerCase(),
            operateur: this.getInputValue('filterOperateur').toLowerCase()
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
            const email = row.dataset.email?.toLowerCase() || '';
            const villeClient = row.dataset.villeClient?.toLowerCase() || '';
            const villeRegion = row.dataset.villeRegion?.toLowerCase() || '';
            const dateAffectation = row.dataset.dateAffectation?.toLowerCase() || '';
            const total = parseFloat(row.dataset.total) || 0;
            const etat = row.dataset.etat?.toLowerCase() || '';
            const operateur = row.dataset.operateur?.toLowerCase() || '';
            
            // Recherche intelligente dans tous les champs
            const matches = 
                idYz.includes(searchTerm) ||
                numCmd.includes(searchTerm) ||
                client.includes(searchTerm) ||
                phone.includes(searchTerm) ||
                email.includes(searchTerm) ||
                villeClient.includes(searchTerm) ||
                villeRegion.includes(searchTerm) ||
                dateAffectation.includes(searchTerm) ||
                etat.includes(searchTerm) ||
                operateur.includes(searchTerm) ||
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
        console.log(`🔍 Recherche liste_prepa: "${query}" - ${matchCount} résultat(s)`);
    }
    
    applyAllFilters() {
        let matchCount = 0;
        
        this.rows.forEach(row => {
            const idYz = row.dataset.idYz?.toLowerCase() || '';
            const numCmd = row.dataset.numCmd?.toLowerCase() || '';
            const client = row.dataset.client?.toLowerCase() || '';
            const phone = row.dataset.phone?.toLowerCase() || '';
            const email = row.dataset.email?.toLowerCase() || '';
            const villeClient = row.dataset.villeClient?.toLowerCase() || '';
            const villeRegion = row.dataset.villeRegion?.toLowerCase() || '';
            const dateAffectation = row.dataset.dateAffectation || '';
            const total = parseFloat(row.dataset.total) || 0;
            const etat = row.dataset.etat?.toLowerCase() || '';
            const operateur = row.dataset.operateur?.toLowerCase() || '';
            
            // Conversion de la date pour comparaison
            const dateMatch = this.checkDateFilter(dateAffectation);
            
            // Vérifier tous les filtres
            const matchesFilters = 
                (this.filters.idYz === '' || idYz.includes(this.filters.idYz)) &&
                (this.filters.numCmd === '' || numCmd.includes(this.filters.numCmd)) &&
                (this.filters.client === '' || client.includes(this.filters.client)) &&
                (this.filters.phone === '' || phone.includes(this.filters.phone)) &&
                (this.filters.email === '' || email.includes(this.filters.email)) &&
                (this.filters.villeClient === '' || villeClient.includes(this.filters.villeClient)) &&
                (this.filters.villeRegion === '' || villeRegion.includes(this.filters.villeRegion)) &&
                (this.filters.etat === '' || etat.includes(this.filters.etat)) &&
                (this.filters.operateur === '' || operateur.includes(this.filters.operateur)) &&
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
        console.log(`🎯 Filtres liste_prepa appliqués - ${matchCount} résultat(s)`);
    }
    
    checkDateFilter(dateStr) {
        if (!this.filters.dateAffectation) return true;
        if (!dateStr) return false;
        
        // Conversion du format d/m/Y vers Date pour comparaison
        const [day, month, year] = dateStr.split('/');
        const rowDate = new Date(year, month - 1, day);
        const filterDate = new Date(this.filters.dateAffectation);
        
        // Comparaison simple (même jour)
        return rowDate.toDateString() === filterDate.toDateString();
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
        console.log('🧹 Recherche liste_prepa effacée');
    }
    
    clearFilters() {
        const filterInputs = [
            'filterIdYz', 'filterNumCmd', 'filterClient', 'filterPhone', 
            'filterEmail', 'filterVilleClient', 'filterVilleRegion', 
            'filterDateAffectation', 'filterTotalMin', 'filterTotalMax',
            'filterEtat', 'filterOperateur'
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
            email: '',
            villeClient: '',
            villeRegion: '',
            dateAffectation: '',
            totalMin: 0,
            totalMax: Infinity,
            etat: '',
            operateur: ''
        };
        
        this.showAllRows();
    }
}

// Initialiser la recherche intelligente de la liste des préparations
let listePrepaSmartSearch;

// Fonctions globales pour l'interface
function toggleAdvancedSearch() {
    const advancedSearch = document.getElementById('advancedSearch');
    advancedSearch.classList.toggle('hidden');
    console.log('🔧 Filtres avancés liste_prepa:', advancedSearch.classList.contains('hidden') ? 'fermés' : 'ouverts');
}

function clearSmartSearch() {
    if (listePrepaSmartSearch) {
        listePrepaSmartSearch.searchInput.value = '';
        listePrepaSmartSearch.showAllRows();
        listePrepaSmartSearch.hideResults();
    }
}

function clearAllSearch() {
    if (listePrepaSmartSearch) {
        listePrepaSmartSearch.clearAll();
    }
}

function applyFilters() {
    if (listePrepaSmartSearch) {
        listePrepaSmartSearch.updateFilters();
        document.getElementById('advancedSearch').classList.add('hidden');
    }
}

function clearFilters() {
    if (listePrepaSmartSearch) {
        listePrepaSmartSearch.clearFilters();
    }
}

// Initialiser quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initialisation du système de recherche intelligente liste_prepa...');
    
    // Vérifier que les éléments nécessaires existent
    const requiredElements = ['smartSearch', 'advancedSearch', 'searchResults', 'resultCount'];
    const missingElements = requiredElements.filter(id => !document.getElementById(id));
    
    if (missingElements.length > 0) {
        console.warn('⚠️ Éléments manquants pour la recherche liste_prepa:', missingElements);
        return;
    }
    
    // Vérifier qu'il y a des lignes à rechercher
    const rows = document.querySelectorAll('.commande-row');
    if (rows.length === 0) {
        console.warn('⚠️ Aucune ligne de commande trouvée pour la recherche liste_prepa');
        return;
    }
    
    // Initialiser le système de recherche
    listePrepaSmartSearch = new ListePrepaSmartSearch();
    
    // Ajouter des raccourcis clavier
    document.addEventListener('keydown', function(e) {
        // Ctrl+F pour focus sur la recherche
        if (e.ctrlKey && e.key === 'f') {
            e.preventDefault();
            const searchInput = document.getElementById('smartSearch');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
                console.log('⌨️ Raccourci Ctrl+F activé (liste_prepa)');
            }
        }
        
        // Échap pour effacer la recherche
        if (e.key === 'Escape') {
            clearSmartSearch();
            console.log('⌨️ Raccourci Échap activé (liste_prepa)');
        }
        
        // Entrée pour appliquer les filtres
        if (e.key === 'Enter' && e.target.closest('#advancedSearch')) {
            applyFilters();
            console.log('⌨️ Raccourci Entrée pour appliquer les filtres (liste_prepa)');
        }
    });
    
    console.log('✅ Système de recherche intelligente liste_prepa initialisé avec succès');
    console.log(`📊 ${rows.length} lignes de commande disponibles pour la recherche`);
});

// Fonctions utilitaires pour le debug
window.debugListePrepaSearch = function() {
    if (listePrepaSmartSearch) {
        console.log('🔍 État du système de recherche liste_prepa:');
        console.log('  - Filtres actifs:', listePrepaSmartSearch.filters);
        console.log('  - Lignes totales:', listePrepaSmartSearch.rows.length);
        console.log('  - Lignes visibles:', Array.from(listePrepaSmartSearch.rows).filter(row => row.style.display !== 'none').length);
    } else {
        console.log('❌ Système de recherche liste_prepa non initialisé');
    }
};

// Exporter pour utilisation externe
window.ListePrepaSmartSearch = ListePrepaSmartSearch;
