/**
 * Gestion des filtres KPIs Yoozak
 * Filtres géographiques Maroc + spécialisés chaussures
 */

class KPIFilters {
  constructor() {
    this.filters = {
      periode: '30days',
      region: 'all',
      categorie: 'all',
      zone: 'all',
      pointure: 'all',
      materiau: 'all',
      montantMin: '',
      montantMax: '',
      search: ''
    };

    this.init();
  }

  init() {
    console.log('🎯 Initialisation des filtres Yoozak');
    this.bindFilterEvents();
    this.loadSavedFilters();
  }

  bindFilterEvents() {
    // Filtres principaux
    const filterElements = document.querySelectorAll('[id$="-filter"]');
    filterElements.forEach(element => {
      element.addEventListener('change', (e) => {
        this.updateFilter(e.target.id.replace('-filter', ''), e.target.value);
      });
    });

    // Boutons d'action
    document.getElementById('reset-filters')?.addEventListener('click', () => {
      this.resetAllFilters();
    });

    document.getElementById('refresh-btn')?.addEventListener('click', () => {
      this.refreshData();
    });

    // Filtres avancés toggle
    this.setupAdvancedFiltersToggle();
  }

  setupAdvancedFiltersToggle() {
    const showBtn = document.getElementById('show-advanced');
    const hideBtn = document.getElementById('toggle-advanced');
    const advancedSection = document.getElementById('advanced-filters');
    const showToggle = document.getElementById('show-advanced-toggle');

    showBtn?.addEventListener('click', () => {
      advancedSection?.classList.remove('hidden');
      showToggle?.classList.add('hidden');
    });

    hideBtn?.addEventListener('click', () => {
      advancedSection?.classList.add('hidden');
      showToggle?.classList.remove('hidden');
    });
  }

  updateFilter(filterName, value) {
    this.filters[filterName] = value;
    this.saveFilters();
    this.applyFilters();

    console.log('🎯 Filtre mis à jour:', filterName, '=', value);
  }

  applyFilters() {
    // Émettre un événement pour que les autres composants se mettent à jour
    const event = new CustomEvent('filtersChanged', {
      detail: { filters: this.filters }
    });
    document.dispatchEvent(event);
  }

  resetAllFilters() {
    // Reset vers les valeurs par défaut
    this.filters = {
      periode: '30days',
      region: 'all',
      categorie: 'all',
      zone: 'all',
      pointure: 'all',
      materiau: 'all',
      montantMin: '',
      montantMax: '',
      search: ''
    };

    // Reset visuel des éléments
    this.updateUIFilters();
    this.saveFilters();
    this.applyFilters();

    console.log('🎯 Tous les filtres réinitialisés');
  }

  updateUIFilters() {
    Object.keys(this.filters).forEach(filterName => {
      const element = document.getElementById(filterName + '-filter');
      if (element) {
        element.value = this.filters[filterName];
      }
    });

    // Reset des inputs spéciaux
    document.getElementById('montant-min').value = '';
    document.getElementById('montant-max').value = '';
    document.getElementById('search-filter').value = '';
  }

  saveFilters() {
    try {
      localStorage.setItem('yoozak-kpi-filters', JSON.stringify(this.filters));
    } catch (e) {
      console.warn('Impossible de sauvegarder les filtres:', e);
    }
  }

  loadSavedFilters() {
    try {
      const saved = localStorage.getItem('yoozak-kpi-filters');
      if (saved) {
        this.filters = { ...this.filters, ...JSON.parse(saved) };
        this.updateUIFilters();
      }
    } catch (e) {
      console.warn('Impossible de charger les filtres sauvegardés:', e);
    }
  }

  refreshData() {
    console.log('🔄 Actualisation des données avec filtres:', this.filters);

    // Afficher un loader
    this.showLoader(true);

    // Simuler un appel API
    setTimeout(() => {
      this.showLoader(false);
      this.applyFilters();

      // Afficher notification de succès
      this.showNotification('Données mises à jour', 'success');
    }, 1000);
  }

  showLoader(show) {
    // Logique d'affichage du loader
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
      const icon = refreshBtn.querySelector('i');
      if (show) {
        icon?.classList.add('fa-spin');
        refreshBtn.disabled = true;
      } else {
        icon?.classList.remove('fa-spin');
        refreshBtn.disabled = false;
      }
    }
  }

  showNotification(message, type = 'info') {
    // Créer une notification temporaire
    const notification = document.createElement('div');
    notification.className = `
            fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-white
            ${type === 'success' ? 'bg-green-500' :
        type === 'error' ? 'bg-red-500' : 'bg-blue-500'}
            transform translate-x-full transition-transform duration-300
        `;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Animation d'entrée
    setTimeout(() => {
      notification.classList.remove('translate-x-full');
    }, 100);

    // Suppression automatique
    setTimeout(() => {
      notification.classList.add('translate-x-full');
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
  }

  // Getters pour accès externe
  getCurrentFilters() {
    return { ...this.filters };
  }

  getFilterValue(filterName) {
    return this.filters[filterName];
  }
}

// Export
window.KPIFilters = KPIFilters;
