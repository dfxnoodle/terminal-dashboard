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
    const trainIcon = new Image(24, 24);
    trainIcon.src = '/train-icon.svg';

    const processData = (orders) => {
      // Helper to get date string in 'YYYY-MM-DD' format, respecting local timezone
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

      // Sort labels descending (e.g., 2025-07-13, 2025-07-12, ...)
      // This places the oldest date at the top of the Y-axis.
      const sortedYLabels = Array.from(yLabels).sort((a, b) => b.localeCompare(a));

      const dataPoints = [];
      if (orders) {
        // Sort orders by departure time to ensure correct processing
        const sortedOrders = [...orders].sort((a, b) => 
          new Date(a.x_studio_actual_train_departure) - new Date(b.x_studio_actual_train_departure)
        );

        sortedOrders.forEach(order => {
          const departureDateTime = new Date(order.x_studio_actual_train_departure);
          const dateStr = toYYYYMMDD(departureDateTime);

          // Only include data points that fall within our 14-day window
          if (yLabels.has(dateStr)) {
            // X-axis value: Time of day, normalized to a single date (e.g., Jan 1, 2000)
            const timeValue = new Date(departureDateTime);
            timeValue.setFullYear(2000, 0, 1); // Normalize date part to a constant

            dataPoints.push({
              x: timeValue,
              y: dateStr,
              order: order // Keep original order data for tooltips
            });
          }
        });
      }

      return {
        datasets: [{
          data: dataPoints,
          pointStyle: trainIcon,
          radius: 12,
          hoverRadius: 16,
        }],
        labels: sortedYLabels,
      };
    };

    const renderChart = () => {
      if (chartInstance) {
        chartInstance.destroy();
      }

      const { datasets, labels } = processData(props.orders);

      // Always render the chart, even if there's no data, to show the axes and labels.
      if (!labels || labels.length === 0) {
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
              display: false, // Hide legend as it's not needed for a single dataset
            },
            title: {
              display: true,
              text: 'Train Departures (Last 14 Days)',
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
                  
                  const lines = [];
                  lines.push(`ID: ${order.id}`);
                  lines.push(`Time: ${time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true })}`);
                  
                  if (order.x_studio_selection_field_83c_1ig067df9) {
                    lines.push(`Status: ${order.x_studio_selection_field_83c_1ig067df9}`);
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
      if (trainIcon.complete) {
        renderChart();
      } else {
        trainIcon.onload = renderChart;
      }
    });

    watch(() => props.orders, () => {
      renderChart();
    }, { deep: true });

    return {
      chartCanvas,
    };
  },
};
</script>
