<template>
  <div class="p-4 md:p-10 space-y-10">
    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-20">
      <div class="animate-spin rounded-full h-16 w-16 border-b-4 border-brand-red"></div>
      <span class="ml-4 text-xl text-brand-gray">Loading Dashboard...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-6 rounded-md shadow-md">
      <div class="flex">
        <div class="py-1">
          <svg class="h-6 w-6 text-red-500 mr-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
        </div>
        <div>
          <p class="font-bold">Error Loading Dashboard</p>
          <p class="text-sm">{{ error }}. Please try again.</p>
          <button 
            @click="loadDashboardData" 
            class="mt-4 bg-brand-red hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-300"
          >
            Retry
          </button>
        </div>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div v-else class="space-y-10">
      <!-- 1st Item: Forwarding Orders Train Departure -->
      <div class="card">
        <h2 class="card-header">Train Departures</h2>
        <div class="grid grid-cols-1 md:grid-cols-5 gap-6 py-4">
          <div class="text-center border-r border-gray-200">
            <div class="metric-value text-brand-gray">{{ dashboardData.forwarding_orders?.last_week_count || 0 }}</div>
            <div class="metric-label">Last Week</div>
          </div>          
          <div class="text-center border-r border-gray-200">
            <div class="metric-value text-brand-red">{{ dashboardData.forwarding_orders?.current_week_count || 0 }}</div>
            <div class="metric-label">This Week</div>
          </div>
          <div class="text-center border-r border-gray-200">
            <div class="metric-value text-green-600">{{ getTodayCount() }}</div>
            <div class="metric-label">Today</div>
          </div>
          <div class="text-center border-r border-gray-200">
            <div class="metric-value text-red-600">{{ getAverageStockpileAge('ICAD') }}</div>
            <div class="metric-label">ICAD Avg Age (hrs)</div>
          </div>
          <div class="text-center">
            <div class="metric-value text-amber-600">{{ getAverageStockpileAge('DIC') }}</div>
            <div class="metric-label">DIC Avg Age (hrs)</div>
          </div>
        </div>
        
        <!-- Daily breakdown chart 
        <div class="mt-6" v-if="Object.keys(dashboardData.forwarding_orders?.daily_counts || {}).length > 0">
          <h3 class="text-lg font-semibold text-brand-gray mb-3">Daily Breakdown (Last 14 Days)</h3>
          <div class="bg-brand-light-gray p-4 rounded-lg">
            <div class="grid grid-cols-7 gap-3">
              <div 
                v-for="(dayData, index) in getLast14Days()" 
                :key="index"
                class="text-center p-3 bg-white rounded-lg shadow-sm"
              >
                <div class="text-sm font-bold text-brand-red">{{ dayData.count }}</div>
                <div class="text-xs text-gray-500 mt-1">{{ dayData.fullDate }}</div>
                <div class="text-xs text-gray-400">{{ dayData.weekday }}</div>
              </div>
            </div>
          </div>
        </div> -->

        <!-- Departure Dot Plot Chart -->
        <div class="mt-6" v-if="dashboardData.forwarding_orders?.orders && dashboardData.forwarding_orders.orders.length > 0">
          <DepartureDotPlot :orders="dashboardData.forwarding_orders.orders" />
        </div>
      </div>

      <!-- 2nd, 3rd & 4th Items: Truck Orders -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- First Mile -->
        <div class="card text-center">
          <h2 class="card-header">First Mile (NDP)</h2>
          <div class="py-4">
            <div class="metric-value">{{ dashboardData.first_mile_truck?.total_orders || 0 }}</div>
            <div class="metric-label">Total Orders Today</div>
            <div class="metric-value mt-4">{{ formatWeight(dashboardData.first_mile_truck?.total_weight || 0) }}</div>
            <div class="metric-label">Total Weight (tons)</div>
          </div>
        </div>

        <!-- Last Mile ICAD -->
        <div class="card text-center">
          <h2 class="card-header">Last Mile (ICAD)</h2>
          <div class="py-4">
            <div class="metric-value">{{ dashboardData.last_mile_icad?.total_orders || 0 }}</div>
            <div class="metric-label">Total Orders Today</div>
            <div class="metric-value mt-4">{{ formatWeight(dashboardData.last_mile_icad?.total_weight || 0) }}</div>
            <div class="metric-label">Total Weight (tons)</div>
          </div>
        </div>

        <!-- Last Mile DIC -->
        <div class="card text-center">
          <h2 class="card-header">Last Mile (DIC)</h2>
          <div class="py-4">
            <div class="metric-value">{{ dashboardData.last_mile_dic?.total_orders || 0 }}</div>
            <div class="metric-label">Total Orders Today</div>
            <div class="metric-value mt-4">{{ formatWeight(dashboardData.last_mile_dic?.total_weight || 0) }}</div>
            <div class="metric-label">Total Weight (tons)</div>
          </div>
        </div>
      </div>

      <!-- 5th Item: Stockpile Utilization -->
      <div class="card">
        <h2 class="card-header">Stockpile Utilization</h2>
        
        <!-- ICAD Stockpiles -->
        <div class="mb-8">
          <h3 class="text-xl font-semibold text-brand-gray mb-4">ICAD Terminal</h3>
          <div v-if="getFilteredStockpiles(dashboardData.stockpiles?.ICAD).length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <StockpileBar v-for="stockpile in getFilteredStockpiles(dashboardData.stockpiles?.ICAD)" :key="stockpile.name" :stockpile="stockpile" :rounding="rounding" />
          </div>
          <p v-else class="text-gray-500">No stockpile data available for ICAD terminal.</p>
        </div>

        <!-- DIC Stockpiles -->
        <div>
          <h3 class="text-xl font-semibold text-brand-gray mb-4">DIC Terminal</h3>
          <div v-if="getFilteredStockpiles(dashboardData.stockpiles?.DIC).length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            <StockpileBar v-for="stockpile in getFilteredStockpiles(dashboardData.stockpiles?.DIC)" :key="stockpile.name" :stockpile="stockpile" :rounding="rounding" />
          </div>
          <p v-else class="text-gray-500">No stockpile data available for DIC terminal.</p>
        </div>
      </div>
    </div>

    <!-- Refresh Controls -->
    <div class="flex justify-center items-center space-x-4 pt-6 border-t border-gray-200 mt-10">
      <button 
        @click="loadDashboardData" 
        :disabled="loading"
        class="bg-brand-red hover:bg-red-700 disabled:bg-gray-400 text-white px-8 py-3 rounded-full font-bold text-lg shadow-lg transform hover:scale-105 transition-transform duration-300"
      >
        {{ loading ? 'Refreshing...' : 'Refresh Now' }}
      </button>
      <button 
        @click="toggleAutoRefresh" 
        :class="{
          'bg-green-600 hover:bg-green-700': autoRefresh,
          'bg-gray-600 hover:bg-gray-700': !autoRefresh
        }"
        class="text-white px-6 py-2 rounded-full font-medium shadow-md transition-colors duration-300"
      >
        Auto-Refresh: {{ autoRefresh ? 'ON' : 'OFF' }}
      </button>
      <button 
        @click="handleLogout" 
        class="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-full font-medium shadow-md transition-colors duration-300"
      >
        Logout
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiService } from '../services/api'
import { authService } from '../services/auth'
import StockpileBar from '../components/StockpileBar.vue'
import DepartureDotPlot from '../components/DepartureDotPlot.vue'

export default {
  name: 'Dashboard',
  components: {
    StockpileBar,
    DepartureDotPlot
  },
  props: {
    rounding: {
      type: Number,
      default: 0
    }
  },
  setup(props) {
    const router = useRouter()
    const loading = ref(false)
    const error = ref(null)
    const dashboardData = ref({})
    const autoRefresh = ref(false)
    let refreshInterval = null

    const formatDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-US', { weekday: 'short' })
    }

    const formatFullDate = (dateString) => {
      const date = new Date(dateString)
      return date.toLocaleDateString('en-GB', { 
        day: '2-digit', 
        month: '2-digit', 
        year: 'numeric' 
      })
    }

    const formatWeight = (weight) => {
      if (props.rounding === 0) {
        return Math.round(weight)
      } else {
        return (Math.round(weight / props.rounding) * props.rounding).toFixed(0)
      }
    }

    const getTodayCount = () => {
      const today = new Date().toISOString().split('T')[0] // Get today's date in YYYY-MM-DD format
      const dailyCounts = dashboardData.value.forwarding_orders?.daily_counts || {}
      return dailyCounts[today] || 0
    }

    const getFilteredStockpiles = (stockpiles) => {
      if (!stockpiles || !Array.isArray(stockpiles)) {
        return []
      }
      return stockpiles.filter(stockpile => stockpile.capacity > 0)
    }

    const getAverageStockpileAge = (terminal) => {
      const stockpiles = dashboardData.value.stockpiles?.[terminal]
      if (!stockpiles || !Array.isArray(stockpiles)) {
        return 'N/A'
      }
      
      // Filter stockpiles with quantity over 150 and valid age data
      const eligibleStockpiles = stockpiles.filter(stockpile => 
        stockpile.quantity > 150 && 
        stockpile.material_age_hours !== null && 
        stockpile.material_age_hours !== undefined &&
        stockpile.material_age_hours > 0
      )
      
      if (eligibleStockpiles.length === 0) {
        return 'N/A'
      }
      
      const totalAge = eligibleStockpiles.reduce((sum, stockpile) => sum + stockpile.material_age_hours, 0)
      const averageAge = totalAge / eligibleStockpiles.length
      
      return Math.round(averageAge)
    }

    const getLast14Days = () => {
      const today = new Date()
      const last14Days = []
      const dailyCounts = dashboardData.value.forwarding_orders?.daily_counts || {}
      
      // Generate the last 7 days (including today)
      for (let i = 13; i >= 0; i--) {
        const date = new Date(today)
        date.setDate(today.getDate() - i)
        
        const dateString = date.toISOString().split('T')[0] // YYYY-MM-DD format
        const count = dailyCounts[dateString] || 0
        
        last14Days.push({
          date: dateString,
          count: count,
          fullDate: date.toLocaleDateString('en-GB', { 
            day: '2-digit', 
            month: '2-digit', 
            year: 'numeric' 
          }),
          weekday: date.toLocaleDateString('en-US', { weekday: 'short' })
        })
      }
      
      return last14Days
    }

    const loadDashboardData = async () => {
      loading.value = true
      error.value = null
      try {
        const response = await apiService.getDashboardData()
        dashboardData.value = response.data
      } catch (err) {
        error.value = err.message || 'An unknown error occurred.'
        console.error('Failed to load dashboard data:', err)
      } finally {
        loading.value = false
      }
    }

    const toggleAutoRefresh = () => {
      autoRefresh.value = !autoRefresh.value
      if (autoRefresh.value) {
        // Refresh every 60 seconds
        refreshInterval = setInterval(loadDashboardData, 60000)
      } else {
        if (refreshInterval) {
          clearInterval(refreshInterval)
        }
      }
    }

    const handleLogout = () => {
      authService.logout()
      router.push('/login')
    }

    onMounted(() => {
      loadDashboardData()
    })

    onUnmounted(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    })

    return {
      loading,
      error,
      dashboardData,
      autoRefresh,
      formatDate,
      formatFullDate,
      formatWeight,
      getTodayCount,
      getFilteredStockpiles,
      getAverageStockpileAge,
      getLast14Days,
      loadDashboardData,
      toggleAutoRefresh,
      handleLogout
    }
  }
}
</script>

<style scoped>
.card {
  @apply bg-white rounded-lg shadow-md overflow-hidden;
}

.card-header {
  @apply bg-brand-red text-white text-lg font-semibold py-3 px-4;
}

.metric-value {
  @apply text-2xl font-bold;
}

.metric-label {
  @apply text-sm text-gray-500;
}

.stockpile-container {
  @apply bg-gray-50 rounded-lg p-4;
}
</style>

