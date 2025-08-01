// ======================== RECHERCHE SAV EN TEMPS RÉEL ========================

class SavSearch {
    constructor() {
        this.searchTimeout = null;
        this.searchInput = document.getElementById('sav-search-input');
        this.searchBtn = document.getElementById('sav-search-btn');
        this.clearBtn = document.getElementById('sav-clear-btn');
        this.searchResults = document.getElementById('sav-search-results');
        this.resultsContainer = document.getElementById('sav-results-container');
        this.resultsCount = document.getElementById('sav-results-count');
        this.searchLoading = document.getElementById('sav-search-loading');
        
        this.init();
    }
    
    init() {
        if (!this.searchInput) return;
        
        // Recherche en temps réel
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                this.hideSearchResults();
                return;
            }
            
            this.searchTimeout = setTimeout(() => {
                this.performSearch(query);
            }, 300);
        });
        
        // Recherche par bouton
        this.searchBtn.addEventListener('click', () => {
            const query = this.searchInput.value.trim();
            if (query.length >= 2) {
                this.performSearch(query);
            }
        });
        
        // Effacer la recherche
        this.clearBtn.addEventListener('click', () => {
            this.searchInput.value = '';
            this.hideSearchResults();
            this.searchInput.focus();
        });
        
        // Raccourci clavier Ctrl+K
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.searchInput.focus();
            }
        });
    }
    
    // Déterminer la catégorie SAV basée sur le titre de la page
    getSavCategory() {
        const title = document.title || '';
        if (title.includes('Retournées')) return 'retournees';
        if (title.includes('Reportées')) return 'reportees';
        if (title.includes('Partiellement')) return 'livrees-partiellement';
        if (title.includes('Annulées')) return 'annulees';
        if (title.includes('Changement')) return 'livrees-avec-changement';
        if (title.includes('Livrées')) return 'livrees';
        return 'all';
    }
    
    // Fonction de recherche
    performSearch(query) {
        this.showLoading();
        
        const category = this.getSavCategory();
        const url = `/parametre/sav/search/api/?q=${encodeURIComponent(query)}&category=${category}`;
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                this.hideLoading();
                this.displayResults(data);
            })
            .catch(error => {
                console.error('Erreur de recherche:', error);
                this.hideLoading();
                this.showError('Erreur lors de la recherche');
            });
    }
    
    // Afficher les résultats
    displayResults(data) {
        if (data.results.length === 0) {
            this.resultsContainer.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-search text-4xl mb-4"></i>
                    <p class="text-lg font-medium">Aucun résultat trouvé</p>
                    <p class="text-sm">Essayez avec d'autres termes de recherche</p>
                </div>
            `;
        } else {
            this.resultsContainer.innerHTML = data.results.map(commande => `
                <div class="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors cursor-pointer border border-gray-200"
                     onclick="window.location.href='${commande.url}'">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="font-semibold text-gray-900">${commande.id_yz}</span>
                                <span class="text-sm text-gray-500">${commande.num_cmd}</span>
                                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${this.getStatusColor(commande.status)}">
                                    ${commande.status}
                                </span>
                            </div>
                            <div class="text-sm text-gray-600 mb-2">
                                <strong>Client:</strong> ${commande.client.prenom} ${commande.client.nom} - ${commande.client.telephone}
                            </div>
                            <div class="text-sm text-gray-600 mb-2">
                                <strong>Ville:</strong> ${commande.ville.nom} (${commande.ville.region})
                            </div>
                            <div class="text-sm text-gray-600 mb-2">
                                <strong>Articles:</strong> ${commande.articles.map(a => `${a.nom} (${a.quantite}x)`).join(', ')}
                            </div>
                            <div class="text-sm text-gray-600">
                                <strong>Total:</strong> <span class="font-semibold text-green-600">${commande.total.toFixed(2)} DH</span>
                                <span class="ml-4"><strong>Date:</strong> ${commande.date}</span>
                            </div>
                        </div>
                        <div class="ml-4">
                            <i class="fas fa-arrow-right text-gray-400"></i>
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        this.resultsCount.textContent = `${data.results.length} résultat${data.results.length > 1 ? 's' : ''} trouvé${data.results.length > 1 ? 's' : ''}`;
        this.searchResults.classList.remove('hidden');
    }
    
    // Couleurs des statuts
    getStatusColor(status) {
        const colors = {
            'Retournée': 'bg-red-100 text-red-800',
            'Reportée': 'bg-orange-100 text-orange-800',
            'Livrée Partiellement': 'bg-yellow-100 text-yellow-800',
            'Annulée (SAV)': 'bg-gray-100 text-gray-800',
            'Livrée avec Changement': 'bg-blue-100 text-blue-800',
            'Livrée': 'bg-green-100 text-green-800'
        };
        return colors[status] || 'bg-gray-100 text-gray-800';
    }
    
    // Afficher/masquer le loading
    showLoading() {
        this.searchLoading.classList.remove('hidden');
    }
    
    hideLoading() {
        this.searchLoading.classList.add('hidden');
    }
    
    // Masquer les résultats
    hideSearchResults() {
        this.searchResults.classList.add('hidden');
    }
    
    // Afficher une erreur
    showError(message) {
        this.resultsContainer.innerHTML = `
            <div class="text-center py-8 text-red-500">
                <i class="fas fa-exclamation-triangle text-4xl mb-4"></i>
                <p class="text-lg font-medium">${message}</p>
            </div>
        `;
        this.resultsCount.textContent = 'Erreur';
        this.searchResults.classList.remove('hidden');
    }
}

// Initialiser la recherche SAV quand le DOM est chargé
document.addEventListener('DOMContentLoaded', function() {
    new SavSearch();
}); 