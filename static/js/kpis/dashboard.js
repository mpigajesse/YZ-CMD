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
    this.activeTab = 'vue-generale';
    this.isLoading = false;

    this.init();
  }

  init() {
    console.log('🏭 Initialisation KPI Manager Yoozak v' + this.version);
    this.bindEvents();
    this.loadInitialData();
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

    // Bouton actualiser
    const refreshBtn = document.querySelector('[data-action="refresh"]');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => this.refreshCurrentTab());
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
      case 'vue-generale':
        await this.loadVueGeneraleData();
        break;
      case 'ventes':
        // CORRECTION : Les KPIs ne sont PAS chargés côté serveur !
        // Il faut toujours appeler l'API pour charger les KPIs + graphiques
        await this.loadVentesData();
        break;
      default:
        console.log('⚠️ Onglet non implémenté, chargement vue générale par défaut');
        await this.loadVueGeneraleData();
    }
  }

  async loadVueGeneraleData() {
    if (this.isLoading) return;

    this.isLoading = true;
    this.showLoadingState();

    try {
      const response = await fetch(this.apiEndpoint + 'vue-generale/', {
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
        this.updateVueGeneraleKPIs(data);
        this.updateLastUpdateTime(data.timestamp);
        console.log('✅ Données Vue Générale chargées avec succès');
      } else {
        throw new Error(data.message || 'Erreur lors du chargement des données');
      }

    } catch (error) {
      console.error('❌ Erreur chargement Vue Générale:', error);
      this.showErrorState('Impossible de charger les données KPIs. Veuillez actualiser la page.');
    } finally {
      this.isLoading = false;
      this.hideLoadingState();
    }
  }

  updateVueGeneraleKPIs(data) {
    // Mettre à jour les KPIs principaux
    this.updateKPICard('ca-mois', data.kpis_principaux.ca_mois);
    this.updateKPICard('commandes-jour', data.kpis_principaux.commandes_jour);
    this.updateKPICard('stock-critique', data.kpis_principaux.stock_critique);
    this.updateKPICard('taux-conversion', data.kpis_principaux.taux_conversion);

    // Mettre à jour les KPIs secondaires
    this.updateKPICard('clients-fideles', data.kpis_secondaires.clients_fideles);
    this.updateKPICard('panier-moyen', data.kpis_secondaires.panier_moyen);
    this.updateKPICard('delai-livraison', data.kpis_secondaires.delai_livraison);
    this.updateKPICard('satisfaction', data.kpis_secondaires.satisfaction);
    this.updateKPICard('support-24-7', data.kpis_secondaires.support_24_7);
    this.updateKPICard('stock-total', data.kpis_secondaires.stock_total);
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
      case 'vue-generale':
        await this.loadVueGeneraleData();
        break;
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
      case 'vue-generale':
        await this.loadVueGeneraleData();
        break;
      case 'ventes':
        await this.loadVentesData(); // Actualisation complète
        break;
      default:
        console.log('Actualisation non disponible pour cet onglet');
    }
  }

  switchTab(tabName) {
    this.activeTab = tabName;
    console.log('📑 Changement d\'onglet:', tabName);

    this.updateTabUI(tabName);

    switch (tabName) {
      case 'vue-generale':
        this.loadVueGeneraleData();
        break;
      case 'ventes':
        // CORRECTION : Lors du changement d'onglet vers Ventes,
        // on charge seulement les graphiques car les KPIs sont déjà présents
        // (ils ont été chargés lors du premier accès)
        if (this.chartsLoaded.has('ventes-graphs')) {
          // Si déjà chargé, ne rien faire
          console.log('✅ Données Ventes déjà chargées');
        } else {
          // Premier accès à l'onglet Ventes : charger graphiques seulement
          this.loadVentesGraphsOnly();
        }
        break;
      default:
        console.log('Onglet non encore implémenté:', tabName);
    }
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
          this.updateEvolutionCAChart(),
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
        this.updateEvolutionCAChart(), // API call interne
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

  async updateEvolutionCAChart(data) {
    const chartId = 'evolution-ca-chart';
    let canvasElement = document.getElementById(chartId);

    if (!canvasElement) {
      const container = document.querySelector('.evolution-ca-container');
      if (!container) return;

      container.innerHTML = `
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-900">📈 Evolution du CA</h3>
          <div class="flex gap-2">
            <button onclick="window.yoozakKPI.changeEvolutionPeriod('7j')" class="text-xs px-2 py-1 bg-blue-100 text-blue-600 rounded period-btn" data-period="7j">7j</button>
            <button onclick="window.yoozakKPI.changeEvolutionPeriod('30j')" class="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded period-btn active" data-period="30j">30j</button>
            <button onclick="window.yoozakKPI.changeEvolutionPeriod('90j')" class="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded period-btn" data-period="90j">90j</button>
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
      const evolutionData = await this.fetchEvolutionCAData('30j');

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
                  return `CA: ${context.parsed.y.toLocaleString()} DH`;
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
                  return value.toLocaleString() + ' DH';
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
        canvasElement.parentElement.innerHTML = '<div class="h-64 flex items-center justify-center text-gray-500"><i class="fas fa-box-open mr-2"></i>Aucun modèle trouvé</div>';
        return;
      }

      if (this.charts.has(chartId)) {
        this.charts.get(chartId).destroy();
      }

      // Prendre seulement les 5 premiers
      const topModeles = modeles.slice(0, 5);
      const labels = topModeles.map(model =>
        model.nom.length > 15 ? model.nom.substring(0, 15) + '...' : model.nom
      );
      const values = topModeles.map(model => model.ca);
      const backgroundColors = topModeles.map(model => model.couleur || '#3b82f6');

      const ctx = canvasElement.getContext('2d');
      const chart = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Chiffre d\'Affaires (DH)',
            data: values,
            backgroundColor: backgroundColors.map(color => color + '20'),
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
                    `CA: ${context.parsed.y.toLocaleString()} DH`,
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
                  return value.toLocaleString() + ' DH';
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
        // Transformer les données API en format Chart.js
        const chartData = {
          labels: data.evolution.map(item => item.date_formatee),
          values: data.evolution.map(item => item.ca),
          raw: data.evolution,
          resume: data.resume
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
          ca_formate: `${ca.toLocaleString()} DH`
        });
      }

      fallbackData.resume.ca_total = fallbackData.values.reduce((a, b) => a + b, 0);
      fallbackData.resume.ca_moyen = fallbackData.resume.ca_total / fallbackData.values.length;

      return fallbackData;
    }
  }

  async changeEvolutionPeriod(period) {
    console.log(`🔄 Changement période évolution CA: ${period}`);

    document.querySelectorAll('.period-btn').forEach(btn => {
      btn.classList.remove('active', 'bg-blue-100', 'text-blue-600');
      btn.classList.add('bg-gray-100', 'text-gray-600');
    });

    const activeBtn = document.querySelector(`[data-period="${period}"]`);
    if (activeBtn) {
      activeBtn.classList.remove('bg-gray-100', 'text-gray-600');
      activeBtn.classList.add('active', 'bg-blue-100', 'text-blue-600');
    }

    const loadingElement = document.getElementById('evolution-ca-loading');
    if (loadingElement) {
      loadingElement.classList.remove('hidden');
    }

    try {
      const evolutionData = await this.fetchEvolutionCAData(period);

      const chartId = 'evolution-ca-chart';
      if (this.charts.has(chartId)) {
        const chart = this.charts.get(chartId);
        chart.data.labels = evolutionData.labels;
        chart.data.datasets[0].data = evolutionData.values;
        chart.update('active');
      }

    } catch (error) {
      console.error('❌ Erreur changement période:', error);
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
      // KPIs principaux
      if (data.kpis_principaux) {
        console.log('-------------- 📊 Mise à jour KPIs principaux Ventes --------------');
        this.updateKPICard('ca_total', data.kpis_principaux.ca_periode);
        this.updateKPICard('panier_moyen', data.kpis_principaux.panier_moyen);
        this.updateKPICard('nb_commandes', data.kpis_principaux.nb_commandes);
        this.updateKPICard('taux_confirmation', data.kpis_principaux.taux_confirmation);
      }

      // KPIs secondaires
      if (data.kpis_secondaires) {
        const topModeles = data.kpis_secondaires.top_modeles;
        const topRegions = data.kpis_secondaires.ventes_geographique;

        if (topModeles && topModeles.length > 0) {
          const topModele = topModeles[0];
          this.updateKPICard('top_modele', {
            valeur_formatee: topModele.nom,
            sub_value: `${topModele.ca.toLocaleString()} DH`,
            tendance: ((topModele.ca / data.kpis_principaux.ca_periode.valeur) * 100).toFixed(1)
          });
        }

        if (topRegions && topRegions.length > 0) {
          const topRegion = topRegions[0];
          this.updateKPICard('top_region', {
            valeur_formatee: topRegion.ville,
            sub_value: `${topRegion.ca.toLocaleString()} DH`,
            tendance: ((topRegion.ca / data.kpis_principaux.ca_periode.valeur) * 100).toFixed(1)
          });
        }

        const commandeMax = Math.max(...data.kpis_secondaires.ventes_geographique.map(v => v.ca / v.commandes));
        this.updateKPICard('commande_max', {
          valeur_formatee: commandeMax.toLocaleString(),
          sub_value: 'Record période',
          tendance: 0
        });
      }

      console.log('✅ KPIs Ventes mis à jour avec succès');
    } catch (error) {
      console.error('❌ Erreur mise à jour KPIs Ventes:', error);
    }
  }
}

// Initialisation globale
window.addEventListener('DOMContentLoaded', () => {
  window.yoozakKPI = new YoozakKPIManager();
});

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = YoozakKPIManager;
}
