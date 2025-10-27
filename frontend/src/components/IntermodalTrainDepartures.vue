<template>
  <div class="relative" style="height: 500px;">
    <canvas ref="chartCanvas"></canvas>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue';
import Chart from 'chart.js/auto';
import 'chartjs-adapter-date-fns';
import { enUS } from 'date-fns/locale';

export default {
  name: 'IntermodalTrainDepartures',
  props: {
    trains: {
      type: Array,
      required: true,
    },
  },
  setup(props) {
    const chartCanvas = ref(null);
    let chartInstance = null;
    
    // Create colored train icons
    const createColoredTrainIcon = async (color) => {
      try {
        const response = await fetch('/train-icon.svg');
        const svgText = await response.text();
        const coloredSvg = svgText.replace(/fill="#[A-Fa-f0-9]{6}"/g, `fill="${color}"`);
        const blob = new Blob([coloredSvg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const img = new Image(24, 24);
        img.src = url;
        
        return new Promise((resolve) => {
          img.onload = () => {
            URL.revokeObjectURL(url);
            resolve(img);
          };
        });
      } catch (error) {
        console.error('Error creating colored train icon:', error);
        // Fallback: create SVG directly
        const trainSvg = `<svg xmlns="http://www.w3.org/2000/svg" height="24px" viewBox="0 0 24 24" width="24px" fill="${color}">
          <path d="M0 0h24v24H0V0z" fill="none"/>
          <path d="M12 2c-4 0-8 .5-8 4v9.5C4 17.43 5.57 19 7.5 19L6 20.5v.5h12v-.5L16.5 19c1.93 0 3.5-1.57 3.5-3.5V6c0-3.5-4-4-8-4zm0 2c2.76 0 5 1.12 5 2.5V12H7V6.5C7 5.12 9.24 4 12 4zm-3.5 13.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm7 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM7 15h10v-1.5c0-.83-.67-1.5-1.5-1.5h-7c-.83 0-1.5.67-1.5 1.5V15z"/>
        </svg>`;
        
        const blob = new Blob([trainSvg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const img = new Image(24, 24);
        img.src = url;
        
        return new Promise((resolve) => {
          img.onload = () => {
            URL.revokeObjectURL(url);
            resolve(img);
          };
        });
      }
    };
    
    // Icons for different routes (origin-destination combinations)
    let ruwKpoIcon = null;
    let ruwIcadIcon = null;
    let ruwGttIcon = null;
    let ruwFujIcon = null;
    let ruwJartIcon = null;
    let otherRouteIcon = null;
    
    // Initialize icons
    const initIcons = async () => {
      ruwKpoIcon = await createColoredTrainIcon('#f02222');     // Red for RUW-KPO
      ruwIcadIcon = await createColoredTrainIcon('#F97316');    // Orange for RUW-ICAD
      ruwGttIcon = await createColoredTrainIcon('#4B5563');     // Dark Grey for RUW-GTT
      ruwFujIcon = await createColoredTrainIcon('#3B82F6');     // Blue for RUW-FUJ
      ruwJartIcon = await createColoredTrainIcon('#10B981');    // Green for RUW-JART
      otherRouteIcon = await createColoredTrainIcon('#9CA3AF'); // Light Grey for other routes
      
      renderChart();
    };

    const processData = (trains) => {
      // Helper to get date string in 'YYYY-MM-DD' format
      const toYYYYMMDD = (date) => {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
      };

      // Generate labels for the last 14 days
      const yLabels = new Set();
      const today = new Date();
      for (let i = 0; i < 14; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        yLabels.add(toYYYYMMDD(date));
      }

      // Sort labels descending
      const sortedYLabels = Array.from(yLabels).sort((a, b) => b.localeCompare(a));

      // Separate data points by route
      const ruwKpoDataPoints = [];
      const ruwIcadDataPoints = [];
      const ruwGttDataPoints = [];
      const ruwFujDataPoints = [];
      const ruwJartDataPoints = [];
      const otherRouteDataPoints = [];
      
      if (trains) {
        const sortedTrains = [...trains].sort((a, b) => 
          new Date(a.actual_departure) - new Date(b.actual_departure)
        );

        sortedTrains.forEach((train, index) => {
          const departureDateTime = new Date(train.actual_departure);
          const dateStr = toYYYYMMDD(departureDateTime);

          if (yLabels.has(dateStr)) {
            // X-axis value: Time of day
            const timeValue = new Date(departureDateTime);
            timeValue.setHours(timeValue.getHours() + 4); // Convert UTC to UAE time
            timeValue.setFullYear(2000, 0, 1); // Normalize date

            const dataPoint = {
              x: timeValue,
              y: dateStr,
              train: train
            };

            // Categorize by route
            const route = `${train.origin}-${train.destination}`;
            if (route === 'RUW-KPO') {
              ruwKpoDataPoints.push(dataPoint);
            } else if (route === 'RUW-ICAD') {
              ruwIcadDataPoints.push(dataPoint);
            } else if (route === 'RUW-GTT') {
              ruwGttDataPoints.push(dataPoint);
            } else if (route === 'RUW-FUJ') {
              ruwFujDataPoints.push(dataPoint);
            } else if (route === 'RUW-JART') {
              ruwJartDataPoints.push(dataPoint);
            } else {
              otherRouteDataPoints.push(dataPoint);
            }
          }
        });
      }

      const datasets = [];
      
      if (ruwKpoDataPoints.length > 0) {
        datasets.push({
          label: 'RUW → KPO',
          data: ruwKpoDataPoints,
          pointStyle: ruwKpoIcon,
          radius: 12,
          hoverRadius: 16,
          backgroundColor: '#f02222',
          borderColor: '#DC2626',
        });
      }
      
      if (ruwIcadDataPoints.length > 0) {
        datasets.push({
          label: 'RUW → ICAD',
          data: ruwIcadDataPoints,
          pointStyle: ruwIcadIcon,
          radius: 12,
          hoverRadius: 16,
          backgroundColor: '#F97316',
          borderColor: '#EA580C',
        });
      }
      
      if (ruwGttDataPoints.length > 0) {
        datasets.push({
          label: 'RUW → GTT',
          data: ruwGttDataPoints,
          pointStyle: ruwGttIcon,
          radius: 12,
          hoverRadius: 16,
          backgroundColor: '#4B5563',
          borderColor: '#374151',
        });
      }
      
      if (ruwFujDataPoints.length > 0) {
        datasets.push({
          label: 'RUW → FUJ',
          data: ruwFujDataPoints,
          pointStyle: ruwFujIcon,
          radius: 12,
          hoverRadius: 16,
          backgroundColor: '#3B82F6',
          borderColor: '#2563EB',
        });
      }
      
      if (ruwJartDataPoints.length > 0) {
        datasets.push({
          label: 'RUW → JART',
          data: ruwJartDataPoints,
          pointStyle: ruwJartIcon,
          radius: 12,
          hoverRadius: 16,
          backgroundColor: '#10B981',
          borderColor: '#059669',
        });
      }
      
      if (otherRouteDataPoints.length > 0) {
        datasets.push({
          label: 'Other Routes',
          data: otherRouteDataPoints,
          pointStyle: otherRouteIcon,
          radius: 12,
          hoverRadius: 16,
          backgroundColor: '#9CA3AF',
          borderColor: '#6B7280',
        });
      }

      return {
        datasets: datasets,
        labels: sortedYLabels,
      };
    };

    const renderChart = () => {
      if (chartInstance) {
        chartInstance.destroy();
      }

      const { datasets, labels } = processData(props.trains);

      // Don't render if icons aren't ready or no labels
      if (!ruwKpoIcon || !ruwIcadIcon || !ruwGttIcon || !ruwFujIcon || !ruwJartIcon || !otherRouteIcon || !labels || labels.length === 0) {
        return;
      }

      const chartConfig = {
        type: 'scatter',
        data: {
          labels: labels,
          datasets: datasets,
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: {
            duration: 800,
            easing: 'easeOutQuart',
          },
          plugins: {
            legend: {
              display: true,
              position: 'top',
              align: 'center',
              labels: {
                usePointStyle: true,
                pointStyle: 'circle',
                padding: 20,
                font: {
                  size: 12,
                  weight: 'bold'
                },
                generateLabels: function(chart) {
                  const datasets = chart.data.datasets;
                  return datasets.map((dataset, i) => ({
                    text: dataset.label,
                    fillStyle: dataset.backgroundColor,
                    strokeStyle: dataset.borderColor,
                    lineWidth: 2,
                    hidden: false,
                    datasetIndex: i
                  }));
                }
              }
            },
            title: {
              display: true,
              text: 'Intermodal Train Departures (Last 14 Days)',
              font: {
                size: 20,
                weight: 'bold',
                family: 'sans-serif',
              },
              color: '#333333',
              padding: {
                top: 10,
                bottom: 30,
              }
            },
            tooltip: {
              enabled: true,
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleFont: { size: 14, weight: 'bold' },
              bodyFont: { size: 12 },
              padding: 10,
              callbacks: {
                title: function(context) {
                  const point = context[0].raw;
                  const date = new Date(point.train.actual_departure);
                  return date.toLocaleDateString('en-GB', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  });
                },
                label: function(context) {
                  const point = context.raw;
                  const train = point.train;
                  const time = new Date(train.actual_departure);
                  time.setHours(time.getHours() + 4); // Convert to UAE time
                  
                  const lines = [];
                  
                  if (train.train_id) {
                    lines.push(`Train: ${train.train_id}`);
                  } else {
                    lines.push(`ID: ${train.id}`);
                  }
                  
                  lines.push(`Time: ${time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}`);
                  
                  if (train.origin && train.destination) {
                    lines.push(`Route: ${train.origin} → ${train.destination}`);
                  }
                  
                  if (train.status) {
                    lines.push(`Status: ${train.status}`);
                  }
                  
                  if (train.train_set) {
                    lines.push(`Train Set: ${train.train_set}`);
                  }
                  
                  return lines;
                }
              }
            }
          },
          scales: {
            x: {
              type: 'time',
              position: 'bottom',
              min: '2000-01-01T00:00:00',
              max: '2000-01-01T23:59:59',
              time: {
                unit: 'hour',
                displayFormats: {
                  hour: 'HH:mm',
                },
                tooltipFormat: 'HH:mm',
                adapter: {
                  locale: enUS,
                },
              },
              title: {
                display: true,
                text: 'Time of Day',
                font: { size: 14, weight: 'bold' },
                color: '#666',
              },
              grid: {
                color: '#e0e0e0',
                borderColor: '#c0c0c0',
              },
              ticks: {
                color: '#333',
                autoSkip: true,
                maxRotation: 0,
                minRotation: 0,
                callback: function(value) {
                  const date = new Date(value);
                  const hours = String(date.getHours()).padStart(2, '0');
                  const minutes = String(date.getMinutes()).padStart(2, '0');
                  return `${hours}:${minutes}`;
                }
              }
            },
            y: {
              type: 'category',
              labels: labels,
              offset: true,
              position: 'left',
              title: {
                display: true,
                text: 'Date',
                font: { size: 14, weight: 'bold' },
                color: '#666',
              },
              grid: {
                display: false,
              },
              ticks: {
                color: '#333',
              }
            },
          },
        },
      };

      chartInstance = new Chart(chartCanvas.value, chartConfig);
    };

    onMounted(() => {
      initIcons();
    });

    watch(() => props.trains, () => {
      if (ruwKpoIcon && ruwIcadIcon && ruwGttIcon && ruwFujIcon && ruwJartIcon && otherRouteIcon) {
        renderChart();
      }
    }, { deep: true });

    return {
      chartCanvas,
    };
  },
};
</script>
