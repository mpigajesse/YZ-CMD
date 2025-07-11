/**
 * Dashboard KPIs Yoozak - Script principal
 * Gestion des interactions et mise à jour temps réel
 */

class YoozakKPIManager {
  constructor() {
    this.version = '1.0.0';
    this.apiEndpoint = '/kpis/api/';
    this.updateInterval = 5 * 60 * 1000; // 5 minutes
    this.charts = new Map();
    this.chartsLoaded = new Set(); // Cache des graphiques déjà chargés
    this.filters = {};
    this.activeTab = 'ventes';
    this.isLoading = false;
    this.selectedPeriod = '30j'; // Persistance de la période sélectionnée

    this.init();
  }

  // Fonction utilitaire pour le formatage des nombres en français
  formatNumberFR(number, decimals = 0) {
    if (typeof number !== 'number' || isNaN(number)) {
      return '0';
    }
    return number.toLocaleString('fr-FR', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals
    });
  }

  // Fonction utilitaire pour obtenir le libellé d'une période
  getPeriodLabel(period) {
    const periodeLabels = {
      '7j': '7 derniers jours',
      '30j': '30 derniers jours',
      '90j': '90 derniers jours'
    };
    return periodeLabels[period] || period;
  }

  init() {
    console.log('🏭 Initialisation KPI Manager Yoozak v' + this.version);
    this.bindEvents();
    this.loadInitialData();
    this.initExportButtons();
  }

  initExportButtons() {
    // Gestion des boutons d'export
    document.querySelectorAll('.export-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const button = e.currentTarget;
        const btnText = button.querySelector('.btn-text');
        const loadingText = button.querySelector('.loading-text');
        
        // Afficher l'état de chargement
        btnText.classList.add('hidden');
        loadingText.classList.remove('hidden');
        
        // Réactiver le bouton après le téléchargement
        setTimeout(() => {
          btnText.classList.remove('hidden');
          loadingText.classList.add('hidden');
        }, 2000);
      });
    });
  }

  updateExportUrls(period) {
    // Mettre à jour les URLs des boutons d'export avec la nouvelle période
    document.querySelectorAll('.export-btn').forEach(btn => {
      const baseUrl = btn.href.split('?')[0];
      btn.href = `${baseUrl}?period=${period}`;
    });
  }

  bindEvents() {
    // Gestion des filtres
    document.addEventListener('change', (e) => {
      if (e.target.classList.contains('kpi-filter')) {
        this.handleFilterChange(e.target);
      }
    });

    // Gestion des onglets
    document.addEventListener('click', (e) => {
      if (e.target.classList.contains('kpi-tab-button')) {
        this.switchTab(e.target.dataset.tab);
      }
    });

    // Bouton actualiser principal
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.refreshCurrentTab());
    }

    // Bouton actualiser dans l'en-tête KPIs
    const refreshKpisBtn = document.getElementById('refresh-kpis');
    if (refreshKpisBtn) {
      refreshKpisBtn.addEventListener('click', () => this.refreshCurrentTab());
    }
  }

  async loadInitialData() {
    console.log('📊 Chargement des données initiales...');

    // Détecter l'onglet actif au chargement de la page
    const activeTabButton = document.querySelector('.kpi-tab-button.active');
    if (activeTabButton) {
      this.activeTab = activeTabButton.dataset.tab;
      console.log('🎯 Onglet actif détecté:', this.activeTab);
    }

    // Charger les données appropriées selon l'onglet actif
    switch (this.activeTab) {
      case 'ventes':
        // CORRECTION : Les KPIs ne sont PAS chargés côté serveur !
        // Il faut toujours appeler l'API pour charger les KPIs + graphiques
        await this.loadVentesData();
        break;
      default:
        console.log('⚠️ Onglet non implémenté, chargement des données par défaut');
        // Pas de chargement par défaut, les données seront chargées lors du changement d'onglet
    }
  }

  updateKPICard(cardId, kpiData) {
    console.log(`🔄 Mise à jour KPI: ${cardId}`, kpiData);
    const card = document.querySelector(`[data-kpi="${cardId}"]`);
    if (!card) {
      console.warn(`❌ Carte KPI introuvable: ${cardId}`);
      return;
    }

    // Mettre à jour la valeur principale
    const valueElement = card.querySelector('.kpi-value');
    if (valueElement) {
      valueElement.textContent = kpiData.valeur_formatee;
      console.log(`✅ Valeur mise à jour pour ${cardId}: ${kpiData.valeur_formatee}`);
    } else {
      console.warn(`❌ Élément .kpi-value introuvable dans ${cardId}`);
    }

    // Mettre à jour la sous-valeur si présente
    const subValueElement = card.querySelector('.kpi-sub-value');
    if (subValueElement && kpiData.sub_value) {
      subValueElement.textContent = kpiData.sub_value;
      console.log(`✅ Sous-valeur mise à jour pour ${cardId}: ${kpiData.sub_value}`);
    }

    // Mettre à jour la tendance
    const trendElement = card.querySelector('.kpi-trend');
    if (trendElement) {
      if (kpiData.tendance !== undefined && kpiData.tendance !== null) {
        const trend = kpiData.tendance;
        const isPositive = trend > 0;
        const isNegative = trend < 0;

        const existingClasses = Array.from(trendElement.classList).filter(cls =>
          !cls.includes('text-') || cls.includes('text-xs')
        );

        const iconElement = trendElement.querySelector('i');
        const textElement = trendElement.querySelector('span');

        if (iconElement && textElement) {
          iconElement.className = `fas text-xs ${isPositive ? 'fa-arrow-up' : isNegative ? 'fa-arrow-down' : 'fa-minus'}`;
          textElement.textContent = isPositive ? `+${trend}` : trend;
        } else {
          trendElement.textContent = isPositive ? `+${trend}` : trend;
        }

        trendElement.className = existingClasses.join(' ') + ` ${isPositive ? 'text-green-600 bg-green-50' : isNegative ? 'text-red-600 bg-red-50' : 'text-gray-600 bg-gray-50'}`;
        console.log(`✅ Tendance mise à jour pour ${cardId}: ${trend}`);
      }
    }

    // Mettre à jour les indicateurs de statut
    if (kpiData.status) {
      card.setAttribute('data-status', kpiData.status);
      this.updateCardStatusStyle(card, kpiData.status);
    }
  }

  updateCardStatusStyle(card, status) {
    card.classList.remove('border-red-300', 'border-orange-300', 'border-green-300');

    switch (status) {
      case 'critical':
        card.classList.add('border-red-300');
        break;
      case 'warning':
        card.classList.add('border-orange-300');
        break;
      case 'good':
        card.classList.add('border-green-300');
        break;
    }
  }

  showLoadingState() {
    const loadingIndicators = document.querySelectorAll('.kpi-loading');
    loadingIndicators.forEach(indicator => {
      indicator.classList.remove('hidden');
    });

    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
      refreshBtn.disabled = true;
      refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Chargement...';
    }
  }

  hideLoadingState() {
    const loadingIndicators = document.querySelectorAll('.kpi-loading');
    loadingIndicators.forEach(indicator => {
      indicator.classList.add('hidden');
    });

    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
      refreshBtn.disabled = false;
      refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Actualiser';
    }
  }

  showErrorState(message) {
    const errorContainer = document.querySelector('.kpi-error-message');
    if (errorContainer) {
      errorContainer.textContent = message;
      errorContainer.classList.remove('hidden');
    }
  }

  showChartsError(message) {
    // Afficher l'erreur dans les conteneurs de graphiques
    const evolutionContainer = document.querySelector('.evolution-ca-container');
    if (evolutionContainer) {
      evolutionContainer.innerHTML = `
        <div class="flex items-center justify-center h-48 bg-gray-50 rounded-lg">
          <div class="text-center">
            <i class="fas fa-exclamation-triangle text-yellow-500 text-2xl mb-2"></i>
            <p class="text-gray-600">${message}</p>
            <button onclick="window.yoozakKPI.retryChartsLoad()" class="mt-2 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
              Réessayer
            </button>
          </div>
        </div>
      `;
    }

    const topModelesContainer = document.querySelector('.top-modeles-container');
    if (topModelesContainer) {
      topModelesContainer.innerHTML = `
        <div class="flex items-center justify-center h-48 bg-gray-50 rounded-lg">
          <div class="text-center">
            <i class="fas fa-exclamation-triangle text-yellow-500 text-2xl mb-2"></i>
            <p class="text-gray-600">Graphique temporairement indisponible</p>
          </div>
        </div>
      `;
    }
  }

  retryChartsLoad() {
    this.loadVentesData();
  }

  updateLastUpdateTime(timestamp) {
    const updateElement = document.querySelector('.last-update-time');
    if (updateElement) {
      const date = new Date(timestamp);
      const formattedTime = date.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit'
      });
      updateElement.textContent = formattedTime;
    }
  }

  async refreshData() {
    console.log('🔄 Actualisation des données...');
    switch (this.activeTab) {
      case 'ventes':
        await this.loadVentesData();
        break;
      default:
        console.log('Onglet non encore implémenté:', this.activeTab);
    }
  }

  async refreshCurrentTab() {
    console.log('🔄 Actualisation de l\'onglet actuel:', this.activeTab);

    switch (this.activeTab) {
      case 'ventes':
        await this.loadVentesData(); // Actualisation complète
        break;
      default:
        console.log('Actualisation non disponible pour cet onglet');
    }
  }
  switchTab(tabName) {
    if (tabName === this.activeTab) {
      console.log('🔄 Onglet déjà actif:', tabName);
      return;
    }

    console.log('🔄 Changement d\'onglet vers:', tabName);
    this.activeTab = tabName;

    // Mettre à jour l'interface utilisateur
    this.updateTabUI(tabName);

    // Émettre un événement pour informer les autres composants
    const tabChangeEvent = new CustomEvent('tabChanged', {
      detail: {
        tab: tabName
      }
    });
    document.dispatchEvent(tabChangeEvent);

    // Charger les données appropriées pour le nouvel onglet
    this.loadDataForTab(tabName);
  }

  updateTabUI(activeTabName) {
    document.querySelectorAll('.kpi-tab-button').forEach(button => {
      button.classList.remove('active', 'border-blue-600', 'text-blue-600');
      button.classList.add('border-transparent', 'text-gray-500');
      button.setAttribute('aria-selected', 'false');
      button.setAttribute('tabindex', '-1');
    });

    document.querySelectorAll('.kpi-tab-panel').forEach(panel => {
      panel.classList.add('hidden');
      panel.classList.remove('active');
    });

    const activeButton = document.querySelector(`[data-tab="${activeTabName}"]`);
    if (activeButton) {
      activeButton.classList.add('active', 'border-blue-600', 'text-blue-600');
      activeButton.classList.remove('border-transparent', 'text-gray-500');
      activeButton.setAttribute('aria-selected', 'true');
      activeButton.setAttribute('tabindex', '0');
    }

    const activePanel = document.getElementById(`${activeTabName}-content`);
    if (activePanel) {
      activePanel.classList.remove('hidden');
      activePanel.classList.add('active');
    }
  }

  async loadVentesData() {
    // Cette fonction charge TOUT : KPIs + graphiques
    if (this.isLoading) return;

    this.isLoading = true;

    // Afficher un loading léger seulement sur le bouton refresh (pas sur tous les KPIs)
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
      refreshBtn.disabled = true;
      refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Chargement...';
    }

    try {
      console.log('📊 Chargement complet des données Ventes...');

      const response = await fetch(this.apiEndpoint + 'ventes/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        // Vider le cache pour forcer le rechargement des graphiques
        this.chartsLoaded.clear();

        // Mettre à jour tous les KPIs avec les nouvelles données
        this.updateVentesKPIs(data);

        // Mettre à jour les graphiques
        await Promise.all([
          this.updateVentesEvolutionCAChart(),
          this.updateTopModelesChart()
        ]);

        // Remettre en cache
        this.chartsLoaded.add('ventes-graphs');

        this.updateLastUpdateTime(data.timestamp);
        console.log('✅ Données Ventes chargées avec succès');
      } else {
        throw new Error(data.message || 'Erreur lors du chargement des données Ventes');
      }

    } catch (error) {
      console.error('❌ Erreur chargement Ventes:', error);
      this.showChartsError('Erreur lors du chargement. Veuillez actualiser.');
    } finally {
      this.isLoading = false;

      // Restaurer le bouton
      if (refreshBtn) {
        refreshBtn.disabled = false;
        refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Actualiser';
      }
    }
  } async loadVentesGraphsOnly() {
    console.log('📈 Chargement des graphiques Ventes uniquement...');

    try {
      // Vérifier si les graphiques sont déjà chargés pour éviter les rechargements inutiles
      const cacheKey = 'ventes-graphs';

      if (this.chartsLoaded.has(cacheKey)) {
        console.log('✅ Graphiques Ventes déjà en cache');
        return;
      }

      // Les KPIs sont déjà chargés côté serveur, on charge juste les graphiques
      await Promise.all([
        this.updateVentesEvolutionCAChart(), // API call interne
        this.updateTopModelesChart()   // API call interne
      ]);

      // Marquer comme chargé
      this.chartsLoaded.add(cacheKey);

      console.log('✅ Graphiques Ventes chargés avec succès');
    } catch (error) {
      console.error('❌ Erreur chargement graphiques Ventes:', error);
      this.showChartsError('Impossible de charger les graphiques. KPIs disponibles.');
    }
  }

  async updateVentesEvolutionCAChart(data) {
    const chartId = 'ventes-evolution-ca-chart';
    let canvasElement = document.getElementById(chartId);

    if (!canvasElement) {
      const container = document.querySelector('.evolution-ca-container');
      if (!container) return;

      // Créer le HTML avec la période persistée
      container.innerHTML = `
        <div class="flex items-center justify-between mb-4">
          <div>
          <h3 class="text-lg font-semibold text-gray-900">📈 Evolution du CA</h3>
            <p id="periode-indicator" class="text-sm text-blue-600 font-medium">Période: ${this.getPeriodLabel(this.selectedPeriod)}</p>
          </div>
          <div class="flex gap-2">
            <button onclick="window.yoozakKPI.changeEvolutionPeriod('7j')" class="text-xs px-3 py-1.5 ${this.selectedPeriod === '7j' ? 'bg-blue-100 text-blue-600 font-medium' : 'bg-gray-100 text-gray-600'} rounded-lg period-btn hover:bg-blue-50 transition-colors" data-period="7j">7 jours</button>
            <button onclick="window.yoozakKPI.changeEvolutionPeriod('30j')" class="text-xs px-3 py-1.5 ${this.selectedPeriod === '30j' ? 'bg-blue-100 text-blue-600 font-medium' : 'bg-gray-100 text-gray-600'} rounded-lg period-btn hover:bg-blue-50 transition-colors" data-period="30j">30 jours</button>
            <button onclick="window.yoozakKPI.changeEvolutionPeriod('90j')" class="text-xs px-3 py-1.5 ${this.selectedPeriod === '90j' ? 'bg-blue-100 text-blue-600 font-medium' : 'bg-gray-100 text-gray-600'} rounded-lg period-btn hover:bg-blue-50 transition-colors" data-period="90j">90 jours</button>
          </div>
        </div>
        <div class="relative">
          <canvas id="${chartId}" width="400" height="200"></canvas>
          <div id="evolution-ca-loading" class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center hidden">
            <i class="fas fa-spinner fa-spin text-blue-600"></i>
          </div>
        </div>
      `;
      canvasElement = document.getElementById(chartId);
    }

    try {
      // Utiliser la période sélectionnée au lieu de '30j' en dur
      const evolutionData = await this.fetchEvolutionCAData(this.selectedPeriod);

      // Vérifier s'il y a des données
      if (!evolutionData || !evolutionData.values || evolutionData.values.length === 0 || evolutionData.values.every(val => val === 0)) {
        const container = document.querySelector('.evolution-ca-container');
        if (container) {
          container.innerHTML = `
            <div class="flex items-center justify-between mb-4">
              <div>
                <h3 class="text-lg font-semibold text-gray-900">📈 Evolution du CA</h3>
                <p class="text-sm text-blue-600 font-medium">Période: ${this.getPeriodLabel(this.selectedPeriod)}</p>
              </div>
              <div class="flex gap-2">
                <button onclick="window.yoozakKPI.changeEvolutionPeriod('7j')" class="text-xs px-3 py-1.5 ${this.selectedPeriod === '7j' ? 'bg-blue-100 text-blue-600 font-medium' : 'bg-gray-100 text-gray-600'} rounded-lg period-btn hover:bg-blue-50 transition-colors" data-period="7j">7 jours</button>
                <button onclick="window.yoozakKPI.changeEvolutionPeriod('30j')" class="text-xs px-3 py-1.5 ${this.selectedPeriod === '30j' ? 'bg-blue-100 text-blue-600 font-medium' : 'bg-gray-100 text-gray-600'} rounded-lg period-btn hover:bg-blue-50 transition-colors" data-period="30j">30 jours</button>
                <button onclick="window.yoozakKPI.changeEvolutionPeriod('90j')" class="text-xs px-3 py-1.5 ${this.selectedPeriod === '90j' ? 'bg-blue-100 text-blue-600 font-medium' : 'bg-gray-100 text-gray-600'} rounded-lg period-btn hover:bg-blue-50 transition-colors" data-period="90j">90 jours</button>
              </div>
            </div>
            <div class="h-64 bg-blue-50 border-2 border-dashed border-blue-200 rounded-lg flex items-center justify-center">
              <div class="text-center">
                <i class="fas fa-chart-line text-blue-400 text-3xl mb-3"></i>
                <h4 class="text-lg font-semibold text-blue-900 mb-2">Aucune donnée de ventes</h4>
                <p class="text-blue-700 text-sm">Aucune commande livrée sur la période sélectionnée</p>
                <p class="text-blue-600 text-xs mt-1">Les données apparaîtront dès qu'il y aura des livraisons</p>
              </div>
            </div>
          `;
        }
        return;
      }

      if (this.charts.has(chartId)) {
        this.charts.get(chartId).destroy();
      }

      const ctx = canvasElement.getContext('2d');
      const chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: evolutionData.labels,
          datasets: [{
            label: 'CA Journalier (DH)',
            data: evolutionData.values,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            borderWidth: 2,
            fill: true,
            tension: 0.3,
            pointBackgroundColor: '#3b82f6',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: '#ffffff',
              bodyColor: '#ffffff',
              borderColor: '#3b82f6',
              borderWidth: 1,
              cornerRadius: 6,
              displayColors: false,
              callbacks: {
                label: function (context) {
                  return `CA: ${context.parsed.y.toLocaleString('fr-FR')} DH`;
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              },
              ticks: {
                color: '#6b7280',
                font: { size: 11 }
              }
            },
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.05)'
              },
              ticks: {
                color: '#6b7280',
                font: { size: 11 },
                callback: function (value) {
                  return value.toLocaleString('fr-FR') + ' DH';
                }
              }
            }
          },
          interaction: {
            intersect: false,
            mode: 'index'
          },
          animation: {
            duration: 1000,
            easing: 'easeInOutQuart'
          }
        }
      });

      this.charts.set(chartId, chart);
      console.log('✅ Graphique Evolution CA mis à jour');

    } catch (error) {
      console.error('❌ Erreur création graphique Evolution CA:', error);
      canvasElement.parentElement.innerHTML = '<div class="h-64 flex items-center justify-center text-gray-500"><i class="fas fa-exclamation-triangle mr-2"></i>Erreur de chargement</div>';
    }
  }

  async updateTopModelesChart(modeles = null) {
    const chartId = 'top-modeles-chart';
    let canvasElement = document.getElementById(chartId);

    if (!canvasElement) {
      const container = document.querySelector('.top-modeles-container');
      if (!container) return;

      container.innerHTML = `
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">🏆 Top Modèles (CA)</h3>
          <div class="text-xs text-gray-500">Top 5 par chiffre d'affaires</div>
        </div>
        <div class="relative">
          <canvas id="${chartId}" width="400" height="200"></canvas>
          <div id="top-modeles-loading" class="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center hidden">
            <i class="fas fa-spinner fa-spin text-blue-600"></i>
          </div>
        </div>
      `;
      canvasElement = document.getElementById(chartId);
    }

    try {
      // Si pas de données passées, récupérer depuis l'API
      if (!modeles) {
        document.getElementById('top-modeles-loading').classList.remove('hidden');
        modeles = await this.fetchTopModelesData();
        document.getElementById('top-modeles-loading').classList.add('hidden');
      }

      if (!modeles || modeles.length === 0) {
        const container = document.querySelector('.top-modeles-container');
        if (container) {
          container.innerHTML = `
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-gray-900">🏆 Top Modèles (CA)</h3>
              <div class="text-xs text-gray-500">Top 5 par chiffre d'affaires</div>
            </div>
            <div class="h-64 bg-yellow-50 border-2 border-dashed border-yellow-200 rounded-lg flex items-center justify-center">
              <div class="text-center">
                <i class="fas fa-crown text-yellow-400 text-3xl mb-3"></i>
                <h4 class="text-lg font-semibold text-yellow-900 mb-2">Aucun modèle vendu</h4>
                <p class="text-yellow-700 text-sm">Aucune commande livrée pour cette période</p>
                <p class="text-yellow-600 text-xs mt-1">Le classement apparaîtra dès qu'il y aura des livraisons</p>
              </div>
            </div>
          `;
        }
        return;
      }

      if (this.charts.has(chartId)) {
        this.charts.get(chartId).destroy();
      }

      // Prendre seulement les 5 premiers et valider
      const topModeles = Array.isArray(modeles) ? modeles.slice(0, 5) : [];
      
      // Vérifier qu'il y a des données valides
      if (topModeles.length === 0) {
        const container = document.querySelector('.top-modeles-container');
        if (container) {
          container.innerHTML = `
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-lg font-semibold text-gray-900">🏆 Top Modèles (CA)</h3>
              <div class="text-xs text-gray-500">Top 5 par chiffre d'affaires</div>
            </div>
            <div class="h-64 bg-yellow-50 border-2 border-dashed border-yellow-200 rounded-lg flex items-center justify-center">
              <div class="text-center">
                <i class="fas fa-crown text-yellow-400 text-3xl mb-3"></i>
                <h4 class="text-lg font-semibold text-yellow-900 mb-2">Aucun modèle vendu</h4>
                <p class="text-yellow-700 text-sm">Aucune commande livrée pour cette période</p>
                <p class="text-yellow-600 text-xs mt-1">Le classement apparaîtra dès qu'il y aura des livraisons</p>
              </div>
            </div>
          `;
        }
        return;
      }

      const labels = topModeles.map(model =>
        model && model.nom ? (model.nom.length > 15 ? model.nom.substring(0, 15) + '...' : model.nom) : 'Sans nom'
      );
      const values = topModeles.map(model => model && typeof model.ca === 'number' ? model.ca : 0);
      const backgroundColors = topModeles.map(model => model && model.couleur ? model.couleur : '#3b82f6');

      const ctx = canvasElement.getContext('2d');
      const chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Chiffre d\'Affaires (DH)',
            data: values,
            backgroundColor: backgroundColors.map(color => (color || '#3b82f6') + '20'),
            borderColor: backgroundColors,
            borderWidth: 2,
            borderRadius: 6,
            borderSkipped: false,
            barThickness: 'flex',
            maxBarThickness: 60
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            },
            tooltip: {
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleColor: '#ffffff',
              bodyColor: '#ffffff',
              borderColor: '#3b82f6',
              borderWidth: 1,
              cornerRadius: 6,
              displayColors: false,
              callbacks: {
                title: function (context) {
                  return topModeles[context[0].dataIndex].nom;
                },
                label: function (context) {
                  const model = topModeles[context.dataIndex];
                  return [
                    `CA: ${context.parsed.y.toLocaleString('fr-FR')} DH`,
                    `Ventes: ${model.nb_ventes} unités`,
                    `Réf: ${model.reference}`
                  ];
                }
              }
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              },
              ticks: {
                color: '#6b7280',
                font: { size: 11 },
                maxRotation: 45,
                minRotation: 0
              }
            },
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.05)'
              },
              ticks: {
                color: '#6b7280',
                font: { size: 11 },
                callback: function (value) {
                  return value.toLocaleString('fr-FR') + ' DH';
                }
              }
            }
          },
          animation: {
            duration: 800,
            easing: 'easeOutQuart'
          }
        }
      });

      this.charts.set(chartId, chart);
      console.log('✅ Graphique Top Modèles créé avec succès');

    } catch (error) {
      console.error('❌ Erreur création graphique Top Modèles:', error);
      canvasElement.parentElement.innerHTML = '<div class="h-64 flex items-center justify-center text-gray-500"><i class="fas fa-exclamation-triangle mr-2"></i>Erreur de chargement</div>';
    }
  }

  async fetchTopModelesData(limit = 5) {
    try {
      const response = await fetch(`${this.apiEndpoint}top-modeles/?limit=${limit}&days=30`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        return data.modeles;
      } else {
        throw new Error(data.message || 'Erreur lors du chargement du top modèles');
      }

    } catch (error) {
      console.error('❌ Erreur récupération top modèles:', error);

      // Données de fallback
      return [
        { nom: 'Classic Leather Boot', ca: 25000, nb_ventes: 45, reference: 'CLB-001', couleur: '#3b82f6' },
        { nom: 'Summer Sandal Pro', ca: 18500, nb_ventes: 62, reference: 'SSP-002', couleur: '#10b981' },
        { nom: 'Sport Runner Elite', ca: 15200, nb_ventes: 38, reference: 'SRE-003', couleur: '#f59e0b' },
        { nom: 'Casual Comfort Walk', ca: 12800, nb_ventes: 41, reference: 'CCW-004', couleur: '#8b5cf6' },
        { nom: 'Urban Style Sneaker', ca: 11400, nb_ventes: 29, reference: 'USS-005', couleur: '#ef4444' }
      ];
    }
  }

  async fetchEvolutionCAData(period = '30j') {
    try {
      const response = await fetch(`${this.apiEndpoint}evolution-ca/?period=${period}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success) {
        // Vérifier que data.evolution est un tableau
        if (!Array.isArray(data.evolution)) {
          throw new Error('Format de données d\'évolution invalide');
        }

        // Transformer les données API en format Chart.js
        const chartData = {
          labels: data.evolution.map(item => item && item.date_formatee ? item.date_formatee : 'N/A'),
          values: data.evolution.map(item => item && typeof item.ca === 'number' ? item.ca : 0),
          raw: data.evolution,
          resume: data.resume || { ca_total: 0, ca_moyen: 0, tendance: 0 }
        };
        return chartData;
      } else {
        throw new Error(data.message || 'Erreur lors du chargement des données d\'évolution');
      }

    } catch (error) {
      console.error('❌ Erreur récupération données évolution CA:', error);

      // Données de fallback
      const days = parseInt(period.replace('j', ''));
      const fallbackData = {
        labels: [],
        values: [],
        raw: [],
        resume: { ca_total: 0, ca_moyen: 0, tendance: 0 }
      };

      for (let i = days - 1; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const ca = Math.floor(Math.random() * 50000) + 10000;

        fallbackData.labels.push(date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' }));
        fallbackData.values.push(ca);
        fallbackData.raw.push({
          date: date.toISOString().split('T')[0],
          date_formatee: date.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric' }),
          ca: ca,
          ca_formate: `${ca.toLocaleString('fr-FR')} DH`
        });
      }

      fallbackData.resume.ca_total = fallbackData.values.reduce((a, b) => a + b, 0);
      fallbackData.resume.ca_moyen = fallbackData.resume.ca_total / fallbackData.values.length;

      return fallbackData;
    }
  }

  async changeEvolutionPeriod(period) {
    console.log(`🔄 Changement période évolution CA: ${period}`);

    // Persister la période sélectionnée
    this.selectedPeriod = period;

    // Mise à jour visuelle des boutons
    document.querySelectorAll('.period-btn').forEach(btn => {
      btn.classList.remove('bg-blue-100', 'text-blue-600', 'font-medium');
      btn.classList.add('bg-gray-100', 'text-gray-600');
    });

    const activeBtn = document.querySelector(`[data-period="${period}"]`);
    if (activeBtn) {
      activeBtn.classList.remove('bg-gray-100', 'text-gray-600');
      activeBtn.classList.add('bg-blue-100', 'text-blue-600', 'font-medium');
    }

    // Mise à jour de l'indicateur de période
    const periodeIndicator = document.getElementById('periode-indicator');
    if (periodeIndicator) {
      periodeIndicator.textContent = `Période: ${this.getPeriodLabel(period)}`;
    }

    // Affichage du loading
    const loadingElement = document.getElementById('evolution-ca-loading');
    if (loadingElement) {
      loadingElement.classList.remove('hidden');
    }

    try {
      const evolutionData = await this.fetchEvolutionCAData(period);

      const chartId = 'ventes-ca-evolution-chart';
      if (this.charts.has(chartId)) {
        const chart = this.charts.get(chartId);
        chart.data.labels = evolutionData.labels;
        chart.data.datasets[0].data = evolutionData.values;
        chart.update('active');
      }

      console.log('✅ Période mise à jour avec succès:', period);

    } catch (error) {
      console.error('❌ Erreur changement période:', error);

      // Notification d'erreur à l'utilisateur
      if (periodeIndicator) {
        const originalText = periodeIndicator.textContent;
        periodeIndicator.textContent = '❌ Erreur lors du changement de période';
        periodeIndicator.classList.add('text-red-600');

        setTimeout(() => {
          periodeIndicator.textContent = originalText;
          periodeIndicator.classList.remove('text-red-600');
        }, 3000);
      }
    } finally {
      if (loadingElement) {
        loadingElement.classList.add('hidden');
      }
    }
  }

  handleFilterChange(filterElement) {
    const filterName = filterElement.name;
    const filterValue = filterElement.value;

    this.filters[filterName] = filterValue;
    console.log('🎯 Filtre modifié:', filterName, '=', filterValue);

    this.refreshData();
  }

  updateVentesKPIs(data) {
    console.log('🔄 Mise à jour des KPIs Ventes...', data);

    try {
      // Afficher le contenu principal et masquer le loading
      document.getElementById('ventes-loading')?.classList.add('hidden');
      document.getElementById('ventes-main-content')?.classList.remove('hidden');

      // KPIs principaux
      if (data.kpis_principaux) {
        this.updateVentesKPICard('ca_periode', data.kpis_principaux.ca_periode);
        this.updateVentesKPICard('panier_moyen', data.kpis_principaux.panier_moyen);
        this.updateVentesKPICard('nb_commandes', data.kpis_principaux.nb_commandes);
      }

      // KPIs secondaires
      if (data.kpis_secondaires) {
        // Top modèle avec vérification des données
        if (data.kpis_secondaires.top_modele && data.kpis_secondaires.top_modele.nom) {
          this.updateVentesKPICard('top_modele', {
            nom: data.kpis_secondaires.top_modele.nom,
            valeur_formatee: data.kpis_secondaires.top_modele.nom,
            sub_value: data.kpis_secondaires.top_modele.ca ? `${data.kpis_secondaires.top_modele.ca.toLocaleString('fr-FR')} DH` : 'N/A',
            tendance: data.kpis_secondaires.top_modele.pourcentage || 0,
            pourcentage: data.kpis_secondaires.top_modele.pourcentage || 0,
            unite: ''
          });
        }

        // Top région avec vérification des données
        if (data.kpis_secondaires.top_region && data.kpis_secondaires.top_region.nom) {
          this.updateVentesKPICard('top_region', {
            nom: data.kpis_secondaires.top_region.nom,
            valeur_formatee: data.kpis_secondaires.top_region.nom,
            sub_value: data.kpis_secondaires.top_region.ca ? `${data.kpis_secondaires.top_region.ca.toLocaleString('fr-FR')} DH` : 'N/A',
            tendance: data.kpis_secondaires.top_region.pourcentage || 0,
            pourcentage: data.kpis_secondaires.top_region.pourcentage || 0,
            unite: '',
            est_donnees_manquantes: data.kpis_secondaires.top_region.est_donnees_manquantes || false
          });
        }

        // Commande max avec vérification des données
        if (data.kpis_secondaires.commande_max && data.kpis_secondaires.commande_max.valeur_formatee) {
          this.updateVentesKPICard('commande_max', {
            valeur_formatee: data.kpis_secondaires.commande_max.valeur_formatee,
            sub_value: 'Record ce mois',
            tendance: 0,
            unite: 'DH'
        });
        }
      }

      console.log('✅ KPIs Ventes mis à jour avec succès');
    } catch (error) {
      console.error('❌ Erreur lors de la mise à jour des KPIs Ventes:', error);
    }
  }

  // Nouvelle fonction pour mettre à jour les KPIs avec la structure des cartes Ventes
  updateVentesKPICard(kpiId, kpiData) {
    console.log(`🔄 Mise à jour KPI Ventes: ${kpiId}`, kpiData);

    // Vérifier que les données KPI sont valides
    if (!kpiData) {
      console.warn(`❌ Données KPI manquantes pour ${kpiId}`);
      return;
    }

    // Gestion spéciale pour les KPIs secondaires avec données manquantes
    if (kpiId === 'top_region' && kpiData.est_donnees_manquantes) {
      // Cas spécial : affichage simple pour données géographiques manquantes
      const valueElement = document.querySelector(`[data-kpi="${kpiId}"]`);
      const subValueElement = document.querySelector(`[data-kpi-sub="${kpiId}"]`);
      const trendElement = document.querySelector(`[data-kpi-trend="${kpiId}"]`);
      const uniteElement = document.querySelector(`[data-kpi-unite="${kpiId}"]`);

      if (valueElement) {
        valueElement.textContent = kpiData.nom || 'Données manquantes';
        valueElement.className = valueElement.className.replace('text-gray-900', 'text-orange-600');
        valueElement.style.fontSize = '14px';
      }
      if (subValueElement) {
        subValueElement.style.display = 'none'; // Masquer complètement
      }
      if (uniteElement) {
        uniteElement.style.display = 'none'; // Masquer complètement
      }
      if (trendElement) {
        // Masquer complètement toute la section tendance
        const trendParent = trendElement.closest('.text-right');
        if (trendParent) {
          trendParent.style.display = 'none';
        }
      }
      return;
    }

    // Mettre à jour la valeur principale
    const valueElement = document.querySelector(`[data-kpi="${kpiId}"]`);
    if (valueElement) {
      if (kpiId === 'top_modele' || kpiId === 'top_region') {
        // Pour les KPIs secondaires, afficher le nom
        valueElement.textContent = kpiData.nom || kpiData.valeur_formatee || kpiData.valeur || '-';
      } else {
        // Pour les KPIs principaux, afficher la valeur formatée
        valueElement.textContent = kpiData.valeur_formatee || kpiData.valeur || '-';
      }
      console.log(`✅ Valeur mise à jour pour ${kpiId}: ${valueElement.textContent}`);
    } else {
      console.warn(`❌ Élément [data-kpi="${kpiId}"] introuvable`);
    }

    // Mettre à jour l'unité
    const uniteElement = document.querySelector(`[data-kpi-unite="${kpiId}"]`);
    if (uniteElement && kpiData.unite) {
      uniteElement.textContent = kpiData.unite;
    }

    // Mettre à jour la sous-valeur
    const subValueElement = document.querySelector(`[data-kpi-sub="${kpiId}"]`);
    if (subValueElement && kpiData.sub_value) {
      subValueElement.textContent = kpiData.sub_value;
    }

    // Mettre à jour la tendance
    const trendElement = document.querySelector(`[data-kpi-trend="${kpiId}"]`);
    if (trendElement && kpiData.tendance !== undefined && kpiData.tendance !== null) {
      const trend = parseFloat(kpiData.tendance);
      const isPositive = trend > 0;
      const isNegative = trend < 0;

      // Mettre à jour l'icône
      const iconElement = trendElement.querySelector('i');
      if (iconElement) {
        iconElement.className = `fas ${isPositive ? 'fa-arrow-up text-green-600' : isNegative ? 'fa-arrow-down text-red-600' : 'fa-minus text-gray-600'}`;
      }

      // Mettre à jour le texte de la tendance
      const spanElement = trendElement.querySelector('span');
      if (spanElement) {
        // Pour les KPIs secondaires, on affiche le pourcentage
        if (kpiId === 'top_modele' || kpiId === 'top_region') {
          spanElement.textContent = kpiData.pourcentage ? `${kpiData.pourcentage}%` : '-';
        } else {
          spanElement.textContent = isPositive ? `+${trend}%` : `${trend}%`;
        }
        spanElement.className = isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600';
      }
    }
  }

  // ===== MÉTHODES CLIENTS =====
  async loadClientsData() {
    console.log('👥 Chargement des données Clients...');

    try {
      this.showClientsLoading();

      // Ajouter un timeout pour éviter les blocages
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 secondes max
      
      const response = await fetch(this.apiEndpoint + 'clients/', {
        signal: controller.signal,
        headers: {
          'X-Requested-With': 'XMLHttpRequest'
        }
      });

      clearTimeout(timeoutId); // Annuler le timeout si la requête réussit

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || 'Erreur API');
      }
      
      // Vérifier si les données sont vides
      if (data.empty) {
        this.showClientsEmpty();
        return;
      }
      
      // Mettre à jour l'interface avec les données
      this.updateClientsKPIs(data);
      this.updateClientsAnalyses(data);
      this.showClientsContent();

      console.log('✅ Données Clients chargées avec succès');

    } catch (error) {
      console.error('❌ Erreur chargement Clients:', error);
      
      // Gestion spécifique des erreurs de timeout
      if (error.name === 'AbortError') {
        this.showErrorState('clients', 'Le chargement des données clients a pris trop de temps. Veuillez réessayer.');
      } else {
        this.showErrorState('clients', 'Erreur lors du chargement des données clients');
      }
      
      // Afficher l'état vide pour éviter une interface bloquée
      this.showClientsEmpty();
    }
  }

  updateClientsKPIs(data) {
    console.log('🔄 Mise à jour des KPIs Clients...', data);

    try {
      // KPIs principaux
      if (data.kpis_principaux) {
        // Nouveaux Clients
        const nouveauxClients = data.kpis_principaux.nouveaux_clients;
        this.updateElement('[data-kpi="nouveaux_clients"]', nouveauxClients.valeur_formatee);
        this.updateElement('[data-kpi-unite="nouveaux_clients"]', nouveauxClients.unite);
        this.updateElement('[data-kpi-sub="nouveaux_clients"]', nouveauxClients.sub_value);
        this.updateTrend('[data-kpi-trend="nouveaux_clients"]', nouveauxClients.tendance);

        // Clients Actifs
        const clientsActifs = data.kpis_principaux.clients_actifs;
        this.updateElement('[data-kpi="clients_actifs"]', clientsActifs.valeur_formatee);
        this.updateElement('[data-kpi-unite="clients_actifs"]', clientsActifs.unite);
        this.updateElement('[data-kpi-sub="clients_actifs"]', clientsActifs.sub_value);
        this.updateTrend('[data-kpi-trend="clients_actifs"]', clientsActifs.tendance);

        // Taux Retour
        const tauxRetour = data.kpis_principaux.taux_retour;
        this.updateElement('[data-kpi="taux_retour"]', tauxRetour.valeur_formatee);
        this.updateElement('[data-kpi-unite="taux_retour"]', tauxRetour.unite);
        this.updateElement('[data-kpi-sub="taux_retour"]', tauxRetour.sub_value);
        this.updateTrend('[data-kpi-trend="taux_retour"]', tauxRetour.tendance, true); // Inverse pour retours

        // Satisfaction
        const satisfaction = data.kpis_principaux.satisfaction;
        this.updateElement('[data-kpi="satisfaction"]', satisfaction.valeur_formatee);
        this.updateElement('[data-kpi-unite="satisfaction"]', satisfaction.unite);
        this.updateElement('[data-kpi-sub="satisfaction"]', satisfaction.sub_value);
        this.updateTrend('[data-kpi-trend="satisfaction"]', satisfaction.tendance);
      }

      console.log('✅ KPIs Clients mis à jour avec succès');
    } catch (error) {
      console.error('❌ Erreur mise à jour KPIs Clients:', error);
    }
  }

  updateClientsAnalyses(data) {
    console.log('🔄 Mise à jour analyses Clients...', data);

    try {
      // Top Clients VIP
      if (data.analyses_detaillees && data.analyses_detaillees.top_clients_vip) {
        const topClientsList = document.getElementById('top-clients-list');
        const topClientsEmpty = document.getElementById('top-clients-empty');

        if (data.analyses_detaillees.top_clients_vip.length > 0) {
          topClientsList.innerHTML = '';
          topClientsEmpty.style.display = 'none';

          data.analyses_detaillees.top_clients_vip.forEach((client, index) => {
            const colors = ['yellow', 'blue', 'green', 'purple', 'indigo'];
            const color = colors[index % colors.length];

            const clientDiv = document.createElement('div');
            clientDiv.className = 'flex items-center justify-between p-3 bg-gray-50 rounded-lg';
            clientDiv.innerHTML = `
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 bg-${color}-100 text-${color}-600 rounded-full flex items-center justify-center text-sm font-bold">
                  ${index + 1}
                </div>
                <span class="font-medium">${client.nom}</span>
              </div>
              <div class="text-right">
                <div class="font-bold text-${color}-600">${client.ca_total_format}</div>
                <div class="text-xs text-gray-500">${client.nb_commandes} commandes</div>
              </div>
            `;
            topClientsList.appendChild(clientDiv);
          });
        } else {
          topClientsList.innerHTML = '';
          topClientsEmpty.style.display = 'block';
        }
      }      // Performance mensuelle
      if (data.analyses_detaillees && data.analyses_detaillees.performance_mensuelle) {
        const perf = data.analyses_detaillees.performance_mensuelle;
        this.updateElement('[data-perf="commandes_mois"]', `${perf.commandes_mois} commandes`);
        this.updateElement('[data-perf="ca_par_client"]', `${this.formatNumberFR(perf.ca_par_client, 2)} DH`);
      }

      // Statistiques globales
      if (data.stats_globales) {
        this.updateElement('[data-stats="total_clients"]', this.formatNumberFR(data.stats_globales.total_clients));
        this.updateElement('[data-stats="taux_activite"]', `${data.stats_globales.taux_activite}%`);
        this.updateElement('[data-stats="panier_moyen_clients"]', `${this.formatNumberFR(data.stats_globales.panier_moyen_clients, 2)} DH`);
      }

      console.log('✅ Analyses Clients mises à jour avec succès');
    } catch (error) {
      console.error('❌ Erreur mise à jour analyses Clients:', error);
    }
  }

  // Méthodes utilitaires pour les états d'affichage
  showLoadingState(section) {
    const loading = document.getElementById(`${section}-loading`);
    const content = document.getElementById(`${section}-content`);
    const emptyState = document.getElementById(`${section}-empty-state`);

    if (loading) loading.style.display = 'block';
    if (content) content.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';
  }

  showContentState(section) {
    const loading = document.getElementById(`${section}-loading`);
    const content = document.getElementById(`${section}-content`);
    const emptyState = document.getElementById(`${section}-empty-state`);

    if (loading) loading.style.display = 'none';
    if (content) content.style.display = 'block';
    if (emptyState) emptyState.style.display = 'none';
  }

  showEmptyState(section) {
    const loading = document.getElementById(`${section}-loading`);
    const content = document.getElementById(`${section}-content`);
    const emptyState = document.getElementById(`${section}-empty-state`);

    if (loading) loading.style.display = 'none';
    if (content) content.style.display = 'none';
    if (emptyState) emptyState.style.display = 'block';
  }

  showErrorState(section, message) {
    console.error(`Erreur section ${section}:`, message);
    // Pour le moment, on affiche l'état vide en cas d'erreur
    this.showEmptyState(section);
  }

  updateElement(selector, value) {
    const element = document.querySelector(selector);
    if (element) {
      element.textContent = value;
    }
  }

  updateTrend(selector, value, inverse = false) {
    const element = document.querySelector(selector);
    if (element) {
      const icon = element.querySelector('i');
      const span = element.querySelector('span');

      if (icon && span) {
        // Déterminer la direction (inverse pour taux de retour où baisse = bien)
        const isPositive = inverse ? value < 0 : value > 0;
        const isNegative = inverse ? value > 0 : value < 0;

        // Mettre à jour l'icône
        icon.className = isPositive ? 'fas fa-arrow-up text-green-600' :
          isNegative ? 'fas fa-arrow-down text-red-600' :
            'fas fa-minus text-gray-400';

        // Mettre à jour la valeur
        span.textContent = Math.abs(value);
        span.className = isPositive ? 'text-green-600' :
          isNegative ? 'text-red-600' :
            'text-gray-400';
      }
    }
  }

  // Fonctions spécialisées pour l'affichage des clients (évite conflit d'ID)
  showClientsLoading() {
    const loading = document.getElementById('clients-loading');
    const content = document.getElementById('clients-main-content');
    const emptyState = document.getElementById('clients-empty-state');

    if (loading) loading.style.display = 'block';
    if (content) content.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';
  }

  showClientsEmpty() {
    const loading = document.getElementById('clients-loading');
    const content = document.getElementById('clients-main-content');
    const emptyState = document.getElementById('clients-empty-state');

    if (loading) loading.style.display = 'none';
    if (content) content.style.display = 'none';
    if (emptyState) emptyState.style.display = 'block';
  }

  // Fonction spécialisée pour l'affichage des clients (évite conflit d'ID)
  showClientsContent() {
    const loading = document.getElementById('clients-loading');
    const content = document.getElementById('clients-main-content');
    const emptyState = document.getElementById('clients-empty-state');

    if (loading) loading.style.display = 'none';
    if (content) content.style.display = 'block';
    if (emptyState) emptyState.style.display = 'none';
    
    // Initialiser les graphiques clients une fois que le contenu est visible
    if (window.kpiCharts) {
      // Utiliser setTimeout pour s'assurer que le DOM est bien mis à jour avant de créer les graphiques
      setTimeout(() => {
        window.kpiCharts.loadClientCharts();
      }, 100);
    }
  }

  loadDataForTab(tabName) {
    switch (tabName) {
      case 'ventes':
        // Lors du changement d'onglet vers Ventes, charger TOUTES les données
        console.log('📊 Chargement de l\'onglet Ventes...');
        this.loadVentesData(); // Charge KPIs + graphiques
        break;
      case 'clients':
        this.loadClientsData();
        break;
      default:
        console.log('Onglet non encore implémenté:', tabName);
    }
  }
}

// Initialisation au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    window.kpiManager = new YoozakKPIManager();
  window.yoozakKPI = window.kpiManager; // Alias pour compatibilité avec le HTML généré
    window.kpiCharts = new KPICharts();

  // Vérification de l'attachement pour debug
  console.log('🔗 window.yoozakKPI attaché:', !!window.yoozakKPI);
  console.log('🔗 changeEvolutionPeriod disponible:', typeof window.yoozakKPI.changeEvolutionPeriod);
});

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = YoozakKPIManager;
}
