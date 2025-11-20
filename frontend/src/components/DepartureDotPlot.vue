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
  name: 'DepartureDotPlot',
  props: {
    orders: {
      type: Array,
      required: true,
    },
  },
  setup(props) {
    const chartCanvas = ref(null);
    let chartInstance = null;
    
    // Create colored train icons from the original SVG
    const createColoredTrainIcon = async (color) => {
      try {
        // Fetch the original SVG
        const response = await fetch('/train-icon.svg');
        const svgText = await response.text();
        
        // Replace only the main fill color, not fill="none"
        const coloredSvg = svgText.replace(/fill="#[A-Fa-f0-9]{6}"/g, `fill="${color}"`);
        
        // Create a blob and object URL
        const blob = new Blob([coloredSvg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        
        // Create an image from the colored SVG
        const img = new Image(24, 24);
        img.src = url;
        
        return new Promise((resolve) => {
          img.onload = () => {
            URL.revokeObjectURL(url); // Clean up
            resolve(img);
          };
        });
      } catch (error) {
        console.error('Error creating colored train icon:', error);
        // Fallback: create the train icon directly from the SVG template
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
    
    // Create icons for all origin-destination combinations
    let ndpIcadTrainIcon = null;
    let ndpDicTrainIcon = null;
    let sijiIcadTrainIcon = null;
    let sijiDicTrainIcon = null;
    
    // Initialize icons
    const initIcons = async () => {
      ndpIcadTrainIcon = await createColoredTrainIcon('#f02222'); // Red for NDP-ICAD
      ndpDicTrainIcon = await createColoredTrainIcon('#F97316');  // Orange for NDP-DIC
      sijiIcadTrainIcon = await createColoredTrainIcon('#4B5563'); // Dark Grey for Siji-ICAD
      sijiDicTrainIcon = await createColoredTrainIcon('#9CA3AF');  // Light Grey for Siji-DIC
      
      // Render chart after icons are ready
      renderChart();
    };

    const processData = (orders) => {
      // Helper to get date string in 'YYYY-MM-DD' format, respecting local timezone
      const toYYYYMMDD = (date) => {
        const y = date.getFullYear();
        const m = String(date.getMonth() + 1).padStart(2, '0');
        const d = String(date.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
      };

      // Generate labels for the last 7 days
      const yLabels = new Set();
      const today = new Date();
      for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(today.getDate() - i);
        yLabels.add(toYYYYMMDD(date));
      }

      // Sort labels descending (e.g., 2025-07-13, 2025-07-12, ...)
      // This places the oldest date at the top of the Y-axis.
      const sortedYLabels = Array.from(yLabels).sort((a, b) => b.localeCompare(a));

      // Separate data points by origin-destination combination
      const ndpIcadDataPoints = [];
      const ndpDicDataPoints = [];
      const sijiIcadDataPoints = [];
      const sijiDicDataPoints = [];
      
      if (orders) {
        // Sort orders by departure time to ensure correct processing
        const sortedOrders = [...orders].sort((a, b) => 
          new Date(a.x_studio_actual_train_departure) - new Date(b.x_studio_actual_train_departure)
        );

        sortedOrders.forEach((order, index) => {
          // Parse the datetime string assuming it's in UAE timezone (UTC+4)
          // but treat it as local time to avoid timezone conversion issues
          const departureDateTime = new Date(order.x_studio_actual_train_departure);
          const dateStr = toYYYYMMDD(departureDateTime);

          // Debug: log first few orders to see what dates we're getting
          if (index < 5) {
            console.log(`Order ${index + 1}:`, {
              departure: order.x_studio_actual_train_departure,
              parsed: departureDateTime,
              dateStr: dateStr,
              origin: order.x_studio_origin_terminal,
              destination: order.x_studio_destination_terminal,
              inRange: yLabels.has(dateStr)
            });
          }

          // Only include data points that fall within our 14-day window
          if (yLabels.has(dateStr)) {
            // X-axis value: Time of day, normalized to a single date (e.g., Jan 1, 2000)
            const timeValue = new Date(departureDateTime);
            // Add 4 hours to convert from UTC to UAE time
            timeValue.setHours(timeValue.getHours() + 4);
            timeValue.setFullYear(2000, 0, 1); // Normalize date part to a constant

            const dataPoint = {
              x: timeValue,
              y: dateStr,
              order: order // Keep original order data for tooltips
            };

            // Separate by origin-destination combination
            const origin = order.x_studio_origin_terminal;
            const destination = order.x_studio_destination_terminal;
            
            if (origin === 'NDP' && destination === 'ICAD') {
              ndpIcadDataPoints.push(dataPoint);
            } else if (origin === 'NDP' && destination === 'DIC') {
              ndpDicDataPoints.push(dataPoint);
            } else if (origin === 'Siji' && destination === 'ICAD') {
              sijiIcadDataPoints.push(dataPoint);
            } else if (origin === 'Siji' && destination === 'DIC') {
              sijiDicDataPoints.push(dataPoint);
            }
          }
        });
      }

      // Debug: log final data points
      console.log('DepartureDotPlot - Processed data points:', {
        ndpIcadCount: ndpIcadDataPoints.length,
        ndpDicCount: ndpDicDataPoints.length,
        sijiIcadCount: sijiIcadDataPoints.length,
        sijiDicCount: sijiDicDataPoints.length,
        totalProcessed: ndpIcadDataPoints.length + ndpDicDataPoints.length + sijiIcadDataPoints.length + sijiDicDataPoints.length
      });

      const datasets = [];
      
      // NDP-ICAD dataset (red train icons)
      if (ndpIcadDataPoints.length > 0) {
        datasets.push({
          label: 'NDP → ICAD',
          data: ndpIcadDataPoints,
          pointStyle: ndpIcadTrainIcon,
          radius: 12,
          hoverRadius: 16,
          backgroundColor: '#f02222', // Red color for NDP-ICAD
          borderColor: '#DC2626',
        });
      }
      
      // NDP-DIC dataset (orange train icons)
      if (ndpDicDataPoints.length > 0) {
        datasets.push({
          label: 'NDP → DIC',
          data: ndpDicDataPoints,
          pointStyle: ndpDicTrainIcon,
          radius: 12,
          hoverRadius: 16,
          backgroundColor: '#F97316', // Orange color for NDP-DIC
          borderColor: '#EA580C',
        });
      }
      
      // Siji-ICAD dataset (dark grey train icons)
      if (sijiIcadDataPoints.length > 0) {
        datasets.push({
          label: 'Siji → ICAD',
          data: sijiIcadDataPoints,
          pointStyle: sijiIcadTrainIcon,
          radius: 12,
          hoverRadius: 16,
          backgroundColor: '#4B5563', // Dark Grey color for Siji-ICAD
          borderColor: '#374151',
        });
      }
      
      // Siji-DIC dataset (light grey train icons)
      if (sijiDicDataPoints.length > 0) {
        datasets.push({
          label: 'Siji → DIC',
          data: sijiDicDataPoints,
          pointStyle: sijiDicTrainIcon,
          radius: 12,
          hoverRadius: 16,
          backgroundColor: '#9CA3AF', // Light Grey color for Siji-DIC
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

      const { datasets, labels } = processData(props.orders);

      // Don't render if icons aren't ready yet or no labels
      if (!ndpIcadTrainIcon || !ndpDicTrainIcon || !sijiIcadTrainIcon || !sijiDicTrainIcon || !labels || labels.length === 0) {
        return;
      }

      const chartConfig = {
        type: 'scatter',
        data: {
          labels: labels, // Y-axis labels
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
              text: 'Train Departures (Last 7 Days)',
              font: {
                size: 20,
                weight: 'bold',
                family: 'sans-serif',
              },
              color: '#333333', // brand-gray
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
                  const date = new Date(point.order.x_studio_actual_train_departure);
                  return date.toLocaleDateString('en-GB', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  });
                },
                label: function(context) {
                  const point = context.raw;
                  const order = point.order;
                  const time = new Date(order.x_studio_actual_train_departure);
                  // Add 4 hours to convert from UTC to UAE time for display
                  time.setHours(time.getHours() + 4);
                  
                  const lines = [];
                  
                  // Forwarding Order Number (if available)
                  if (order.x_name) {
                    lines.push(`Order: ${order.x_name}`);
                  } else {
                    lines.push(`ID: ${order.id}`);
                  }
                  
                  // Train ID
                  if (order.x_studio_train_id) {
                    lines.push(`Train: ${order.x_studio_train_id}`);
                  }
                  
                  // Departure Time
                  lines.push(`Time: ${time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}`);
                  
                  // Origin and Destination Terminals
                  if (order.x_studio_origin_terminal && order.x_studio_destination_terminal) {
                    lines.push(`Route: ${order.x_studio_origin_terminal} → ${order.x_studio_destination_terminal}`);
                  } else if (order.x_studio_destination_terminal) {
                    lines.push(`Destination: ${order.x_studio_destination_terminal}`);
                  }
                  
                  // Status
                  if (order.x_studio_selection_field_83c_1ig067df9) {
                    lines.push(`Status: ${order.x_studio_selection_field_83c_1ig067df9}`);
                  }
                  
                  // Weight information
                  if (order.x_studio_total_weight_tons && order.x_studio_total_weight_tons > 0) {
                    const formattedWeight = order.x_studio_total_weight_tons.toLocaleString('en-US', { 
                      minimumFractionDigits: 1, 
                      maximumFractionDigits: 1 
                    });
                    lines.push(`Weight: ${formattedWeight} tons`);
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
                  hour: 'HH:mm', // 24-hour format
                  day: 'HH:mm',
                  month: 'HH:mm',
                  year: 'HH:mm',
                  week: 'HH:mm',
                  quarter: 'HH:mm',
                  minute: 'HH:mm',
                  second: 'HH:mm',
                  millisecond: 'HH:mm'
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
                major: {
                  enabled: true,
                },
              }
            },
            y: {
              type: 'category',
              labels: labels, // Use the sorted date strings as labels
              offset: true,
              position: 'left',
              title: {
                display: true,
                text: 'Date',
                font: { size: 14, weight: 'bold' },
                color: '#666',
              },
              grid: {
                display: false, // Hide horizontal grid lines for a cleaner look
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
      // Initialize colored icons and render chart when ready
      initIcons();
    });

    watch(() => props.orders, () => {
      // Only render if icons are ready
      if (ndpIcadTrainIcon && ndpDicTrainIcon && sijiIcadTrainIcon && sijiDicTrainIcon) {
        renderChart();
      }
    }, { deep: true });

    return {
      chartCanvas,
    };
  },
};
</script>
