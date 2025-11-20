<template>
  <div class="card">
    <!-- Header -->
    <h2 class="card-header">RUW Container Status</h2>

    <!-- Loading State -->
    <div v-if="loading" class="p-8 text-center">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-red mx-auto"></div>
      <p class="mt-4 text-gray-600">Loading container data...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="p-6">
      <div class="bg-red-50 border border-red-200 rounded-lg p-4">
        <div class="flex items-start">
          <svg class="h-5 w-5 text-red-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <div class="ml-3">
            <h3 class="text-sm font-medium text-red-800">Error loading data</h3>
            <p class="mt-1 text-sm text-red-700">{{ error }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Data Display -->
    <div v-else-if="data" class="p-4">
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <!-- Total Containers -->
        <div class="text-center border-r border-gray-200 last:border-r-0">
          <div class="metric-value text-blue-600">{{ data.total.toLocaleString('en-US') }}</div>
          <div class="metric-label">Total Containers</div>
        </div>

        <!-- Loaded Containers -->
        <div class="text-center border-r border-gray-200 last:border-r-0">
          <div class="metric-value text-green-600">{{ data.loaded.toLocaleString('en-US') }}</div>
          <div class="metric-label">Loaded ({{ data.loaded_percentage }}%)</div>
        </div>

        <!-- Empty Containers -->
        <div class="text-center">
          <div class="metric-value text-gray-600">{{ data.empty.toLocaleString('en-US') }}</div>
          <div class="metric-label">Empty ({{ data.empty_percentage }}%)</div>
        </div>
      </div>

      <!-- Visual Progress Bar -->
      <div class="mb-6">
        <div class="flex items-center justify-between mb-2">
          <span class="text-sm font-medium text-gray-700">Container Status Distribution</span>
          <span class="text-sm text-gray-500">{{ data.total.toLocaleString('en-US') }} containers</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-6 overflow-hidden flex">
          <div 
            class="bg-green-500 flex items-center justify-center text-white text-xs font-medium transition-all duration-500"
            :style="{ width: data.loaded_percentage + '%' }"
          >
            <span v-if="data.loaded_percentage > 15">{{ data.loaded.toLocaleString('en-US') }} Loaded</span>
          </div>
          <div 
            class="bg-gray-400 flex items-center justify-center text-white text-xs font-medium transition-all duration-500"
            :style="{ width: data.empty_percentage + '%' }"
          >
            <span v-if="data.empty_percentage > 15">{{ data.empty.toLocaleString('en-US') }} Empty</span>
          </div>
        </div>
      </div>

      <!-- Recent Container Updates -->
      <div v-if="data.recent_containers && data.recent_containers.length > 0">
        <h4 class="text-sm font-semibold text-gray-700 mb-3">Recent Container Updates</h4>
        <div class="bg-gray-50 rounded-lg overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-100">
                <tr>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Container ID
                  </th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th class="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Updated
                  </th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="container in data.recent_containers" :key="container.id" class="hover:bg-gray-50">
                  <td class="px-4 py-2 text-sm font-medium text-gray-900">
                    {{ container.x_name || `#${container.id}` }}
                  </td>
                  <td class="px-4 py-2 text-sm">
                    <span 
                      :class="container.x_studio_filled 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'"
                      class="px-2 py-1 rounded-full text-xs font-medium"
                    >
                      {{ container.x_studio_filled ? 'Loaded' : 'Empty' }}
                    </span>
                  </td>
                  <td class="px-4 py-2 text-sm text-gray-500">
                    {{ formatDateTime(container.write_date) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Last Updated Footer -->
      <div class="mt-4 pt-3 border-t border-gray-200">
        <p class="text-xs text-gray-500 text-right">
          Last updated: {{ lastUpdated }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { apiService } from '../services/api'

const data = ref(null)
const loading = ref(true)
const error = ref(null)
const lastUpdated = ref('')
let refreshInterval = null

const fetchData = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await apiService.getIntermodalRUWContainers()
    
    if (response && response.success) {
      data.value = response.data
      // Update last updated time to browser's current time
      lastUpdated.value = formatLastUpdated()
    } else {
      throw new Error('Invalid response format')
    }
  } catch (err) {
    error.value = err.response?.data?.detail || err.message || 'Failed to load container data'
    console.error('Error fetching RUW container data:', err)
  } finally {
    loading.value = false
  }
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return 'N/A'
  
  // Ensure the date string is treated as UTC by appending 'Z' if not present
  const utcDateStr = dateStr.includes('Z') ? dateStr : dateStr + 'Z'
  
  // Parse the UTC datetime from Odoo
  const utcDate = new Date(utcDateStr)
  
  // Manually add 4 hours to convert UTC to UAE time
  const uaeTime = new Date(utcDate.getTime() + (4 * 60 * 60 * 1000))
  
  // Format the date
  const day = String(uaeTime.getUTCDate()).padStart(2, '0')
  const month = uaeTime.toLocaleString('en-GB', { month: 'short', timeZone: 'UTC' })
  const year = uaeTime.getUTCFullYear()
  const hours = String(uaeTime.getUTCHours()).padStart(2, '0')
  const minutes = String(uaeTime.getUTCMinutes()).padStart(2, '0')
  
  return `${day} ${month} ${year} ${hours}:${minutes}`
}

const formatLastUpdated = () => {
  const now = new Date()
  const day = String(now.getDate()).padStart(2, '0')
  const month = now.toLocaleString('en-GB', { month: 'short' })
  const year = now.getFullYear()
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  
  return `${day} ${month} ${year} ${hours}:${minutes}`
}

onMounted(() => {
  fetchData()
  // Refresh every 60 seconds
  refreshInterval = setInterval(fetchData, 60000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
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
</style>
