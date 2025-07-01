/**
 * Configuration et gestion des graphiques KPIs Yoozak
 * Chart.js avec styles personnalisés pour chaussures
 */

class KPICharts {
  constructor() {
    this.charts = new Map();
    this.defaultConfig = this.getDefaultChartConfig();
    this.colors = {
      primary: '#3b82f6',
      secondary: '#10b981',
      accent: '#f59e0b',
      warning: '#ef4444',
      purple: '#8b5cf6',
      brown: '#92400e',
      gray: '#6b7280'
    };

    this.init();
  }

  init() {
    console.log('📊 Initialisation des graphiques KPIs');
    this.setupChartDefaults();
    this.bindEvents();
  }

  setupChartDefaults() {
    if (typeof Chart !== 'undefined') {
      Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
      Chart.defaults.color = '#374151';
      Chart.defaults.borderColor = '#e5e7eb';
      Chart.defaults.backgroundColor = 'rgba(59, 130, 246, 0.1)';

      // Configuration responsive
      Chart.defaults.responsive = true;
      Chart.defaults.maintainAspectRatio = false;
    }
  }

  getDefaultChartConfig() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            usePointStyle: true,
            padding: 20,
            font: {
              size: 12
            }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleFont: {
            size: 14,
            weight: 'bold'
          },
          bodyFont: {
            size: 12
          },
          cornerRadius: 8,
          displayColors: true
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          },
          ticks: {
            font: {
              size: 11
            }
          }
        },
        y: {
          grid: {
            color: '#f3f4f6'
          },
          ticks: {
            font: {
              size: 11
            }
          }
        }
      }
    };
  }

  bindEvents() {
    // Écouter les changements de filtres
    document.addEventListener('filtersChanged', (e) => {
      this.updateAllCharts(e.detail.filters);
    });

    // Écouter les changements d'onglets
    document.addEventListener('tabChanged', (e) => {
      this.loadChartsForTab(e.detail.tab);
    });

    // Resize handler
    window.addEventListener('resize', () => {
      this.resizeAllCharts();
    });
  }

  createLineChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
      console.warn('Canvas non trouvé:', canvasId);
      return null;
    }

    const config = {
      type: 'line',
      data: data,
      options: {
        ...this.defaultConfig,
        ...options
      }
    };

    const chart = new Chart(canvas, config);
    this.charts.set(canvasId, chart);

    return chart;
  }

  createBarChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
      console.warn('Canvas non trouvé:', canvasId);
      return null;
    }

    const config = {
      type: 'bar',
      data: data,
      options: {
        ...this.defaultConfig,
        ...options
      }
    };

    const chart = new Chart(canvas, config);
    this.charts.set(canvasId, chart);

    return chart;
  }

  createPieChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
      console.warn('Canvas non trouvé:', canvasId);
      return null;
    }

    const config = {
      type: 'pie',
      data: data,
      options: {
        ...this.defaultConfig,
        ...options,
        scales: {} // Pas d'échelles pour les graphiques circulaires
      }
    };

    const chart = new Chart(canvas, config);
    this.charts.set(canvasId, chart);

    return chart;
  }

  // Données d'exemple pour les graphiques
  getSampleCAData() {
    return {
      labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'],
      datasets: [{
        label: 'CA (DH)',
        data: [850000, 920000, 1100000, 1050000, 1180000, 1220000, 1350000, 1280000, 1450000, 1380000, 1520000, 1250000],
        borderColor: this.colors.primary,
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    };
  }

  getSampleCategorieData() {
    return {
      labels: ['Chaussures Homme', 'Chaussures Femme', 'Sandales', 'Baskets'],
      datasets: [{
        label: 'CA par Catégorie',
        data: [485000, 520000, 165000, 80000],
        backgroundColor: [
          this.colors.primary,
          this.colors.purple,
          this.colors.accent,
          this.colors.secondary
        ],
        borderColor: [
          this.colors.primary,
          this.colors.purple,
          this.colors.accent,
          this.colors.secondary
        ],
        borderWidth: 2
      }]
    };
  }

  getSampleTopModelesData() {
    return {
      labels: ['Classic Homme', 'Élégance Femme', 'Sport Basket', 'Sandales Été', 'Cuir Premium'],
      datasets: [{
        label: 'CA (DH)',
        data: [180000, 165000, 145000, 120000, 95000],
        backgroundColor: this.colors.secondary,
        borderColor: this.colors.secondary,
        borderWidth: 1
      }]
    };
  }

  updateAllCharts(filters) {
    console.log('📊 Mise à jour des graphiques avec filtres:', filters);

    // Ici on ferait les appels API pour récupérer les nouvelles données
    // Pour l'instant, on simule avec un délai
    setTimeout(() => {
      this.charts.forEach((chart, chartId) => {
        // Logique de mise à jour spécifique selon le type de graphique
        this.updateChartData(chart, this.getUpdatedData(chartId, filters));
      });
    }, 500);
  }

  updateChartData(chart, newData) {
    chart.data = newData;
    chart.update('active');
  }

  getUpdatedData(chartId, filters) {
    // Simuler des données différentes selon les filtres
    // Dans la vraie application, ceci ferait des appels API

    switch (chartId) {
      case 'ca-evolution-chart':
        return this.getSampleCAData();
      case 'categories-chart':
        return this.getSampleCategorieData();
      case 'top-modeles-chart':
        return this.getSampleTopModelesData();
      default:
        return null;
    }
  }

  loadChartsForTab(tabName) {
    console.log('📊 Chargement des graphiques pour l\'onglet:', tabName);

    // Destroy existing charts if switching tabs
    this.destroyTabCharts(tabName);

    switch (tabName) {
      case 'vue-generale':
        this.loadGeneralCharts();
        break;
      case 'ventes':
        this.loadSalesCharts();
        break;
      case 'clients':
        this.loadClientCharts();
        break;
      case 'operations':
        this.loadOperationsCharts();
        break;
      case 'chaussures-stocks':
        this.loadStockCharts();
        break;
    }
  }

  loadGeneralCharts() {
    // Vérifier si le graphique existe déjà et le détruire
    if (this.charts.has('ca-evolution-chart')) {
      this.charts.get('ca-evolution-chart').destroy();
      this.charts.delete('ca-evolution-chart');
    }
    
    // Graphique évolution CA
    const caChart = this.createLineChart('ca-evolution-chart', this.getSampleCAData(), {
      plugins: {
        legend: {
          display: false
        }
      },
      scales: {
        y: {
          ticks: {
            callback: function (value) {
              return (value / 1000) + 'K DH';
            }
          }
        }
      }
    });
  }

  loadSalesCharts() {
    // Graphiques pour l'onglet ventes (à implémenter)
    console.log('📈 Chargement des graphiques de vente');
    
    // Détruire les graphiques existants avant d'en créer de nouveaux
    ['sales-chart-1', 'sales-chart-2'].forEach(chartId => {
      if (this.charts.has(chartId)) {
        this.charts.get(chartId).destroy();
        this.charts.delete(chartId);
      }
    });
  }

  loadClientCharts() {
    // Graphiques pour l'onglet clients
    console.log('👥 Chargement des graphiques clients');
    
    // Détruire les graphiques existants avant d'en créer de nouveaux
    ['client-evolution-chart', 'client-segmentation-chart'].forEach(chartId => {
      if (this.charts.has(chartId)) {
        this.charts.get(chartId).destroy();
        this.charts.delete(chartId);
      }
    });
    
    // Vérifier si les éléments canvas existent
    const evolutionCanvas = document.getElementById('client-evolution-chart');
    const segmentationCanvas = document.getElementById('client-segmentation-chart');
    
    if (evolutionCanvas) {
      this.createClientEvolutionChart();
    }
    
    if (segmentationCanvas) {
      this.createClientSegmentationChart();
    }
  }
  
  createClientEvolutionChart() {
    // Données d'exemple pour l'évolution du nombre de clients
    const data = {
      labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'],
      datasets: [{
        label: 'Nouveaux Clients',
        data: [45, 52, 38, 65, 72, 58, 80, 95, 110, 87, 95, 102],
        borderColor: this.colors.primary,
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 6
      }, {
        label: 'Clients Actifs',
        data: [120, 135, 150, 165, 180, 195, 210, 225, 240, 255, 270, 285],
        borderColor: this.colors.secondary,
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        borderDash: [5, 5],
        fill: false,
        pointRadius: 4,
        pointHoverRadius: 6
      }]
    };
    
    this.createLineChart('client-evolution-chart', data, {
      plugins: {
        legend: {
          display: true
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Nombre de clients'
          }
        }
      }
    });
  }
  
  createClientSegmentationChart() {
    // Essayer d'obtenir les données de segmentation réelles depuis le DOM
    let segmentData = [];
    let segmentLabels = [];
    
    try {
      // Récupérer les données depuis les éléments HTML
      const acheteurs = document.querySelector('[data-segment="acheteurs_reguliers"]');
      const nouveaux = document.querySelector('[data-segment="nouveaux_testeurs"]');
      const occasionnels = document.querySelector('[data-segment="clients_occasionnels"]');
      const vip = document.querySelector('[data-segment="vip_premium"]');
      
      if (acheteurs && nouveaux && occasionnels && vip) {
        // Extraire les valeurs numériques (retirer le symbole %)
        const getValue = el => parseFloat(el.textContent.replace('%', '')) || 0;
        
        segmentData = [
          getValue(acheteurs),
          getValue(nouveaux),
          getValue(occasionnels),
          getValue(vip)
        ];
        
        segmentLabels = [
          'Acheteurs Réguliers',
          'Nouveaux Testeurs',
          'Clients Occasionnels',
          'VIP Premium'
        ];
      }
    } catch (e) {
      console.warn('Erreur lors de la récupération des données de segmentation:', e);
      // Utiliser des données par défaut en cas d'erreur
      segmentData = [35, 40, 15, 10];
      segmentLabels = [
        'Acheteurs Réguliers',
        'Nouveaux Testeurs',
        'Clients Occasionnels',
        'VIP Premium'
      ];
    }
    
    // Si aucune donnée valide n'a été trouvée, utiliser les données par défaut
    if (segmentData.length === 0 || segmentData.every(val => val === 0)) {
      segmentData = [35, 40, 15, 10];
    }
    
    // Données pour le graphique
    const data = {
      labels: segmentLabels,
      datasets: [{
        label: 'Répartition des clients',
        data: segmentData,
        backgroundColor: [
          this.colors.secondary,
          this.colors.primary,
          this.colors.accent,
          this.colors.purple
        ],
        borderColor: [
          this.colors.secondary,
          this.colors.primary,
          this.colors.accent,
          this.colors.purple
        ],
        borderWidth: 1
      }]
    };
    
    this.createPieChart('client-segmentation-chart', data, {
      plugins: {
        legend: {
          position: 'right'
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.label}: ${context.raw}%`;
            }
          }
        }
      }
    });
  }

  loadOperationsCharts() {
    // Graphiques pour l'onglet opérations (à implémenter)
    console.log('⚙️ Chargement des graphiques opérationnels');
    
    // Détruire les graphiques existants avant d'en créer de nouveaux
    ['operations-chart-1', 'operations-chart-2'].forEach(chartId => {
      if (this.charts.has(chartId)) {
        this.charts.get(chartId).destroy();
        this.charts.delete(chartId);
      }
    });
  }

  loadStockCharts() {
    // Graphiques pour l'onglet stocks (à implémenter)
    console.log('📦 Chargement des graphiques de stock');
    
    // Détruire les graphiques existants avant d'en créer de nouveaux
    ['stock-chart-1', 'stock-chart-2'].forEach(chartId => {
      if (this.charts.has(chartId)) {
        this.charts.get(chartId).destroy();
        this.charts.delete(chartId);
      }
    });
  }

  destroyTabCharts(newTab) {
    // Nettoyer les graphiques qui ne sont plus visibles
    this.charts.forEach((chart, chartId) => {
      if (!document.getElementById(chartId) ||
        !document.getElementById(chartId).offsetParent) {
        chart.destroy();
        this.charts.delete(chartId);
      }
    });
  }

  resizeAllCharts() {
    this.charts.forEach(chart => {
      chart.resize();
    });
  }

  destroyAllCharts() {
    this.charts.forEach(chart => {
      chart.destroy();
    });
    this.charts.clear();
  }

  // Utilitaires pour les couleurs
  getColorPalette(count) {
    const palette = Object.values(this.colors);
    return palette.slice(0, count);
  }

  hexToRgba(hex, alpha = 0.1) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
}

// Export
window.KPICharts = KPICharts;
