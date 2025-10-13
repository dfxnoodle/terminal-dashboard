<template>
  <div class="bg-white rounded-lg shadow-lg p-6">
    <h2 class="text-2xl font-bold mb-4 flex items-center">
      🚂 Train Loading Progress - Siji Terminal
    </h2>
    
    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-4 text-gray-600">Loading train data...</p>
    </div>
    
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded p-4">
      <p class="text-red-600">{{ error }}</p>
    </div>
    
    <div v-else-if="data && !data.error">
      <!-- Header Info -->
      <div class="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded">
        <div>
          <p class="text-sm text-gray-600">Train ID</p>
          <p class="text-xl font-bold">{{ data.train_id }}</p>
        </div>
        <div>
          <p class="text-sm text-gray-600">Status</p>
          <p class="text-xl font-bold text-green-600">{{ data.status }}</p>
        </div>
        <div>
          <p class="text-sm text-gray-600">Loading Date</p>
          <p class="text-lg">{{ formatDate(data.loading_date) }}</p>
        </div>
        <div>
          <p class="text-sm text-gray-600">Last Updated</p>
          <p class="text-lg">{{ formatDateTime(data.last_updated) }}</p>
        </div>
      </div>
      
      <!-- Overall Summary -->
      <div class="pt-2">
        <h3 class="text-lg font-semibold mb-3">Overall Summary</h3>
        
        <!-- Material Being Loaded -->
        <div v-if="loadedMaterials.length > 0" class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
          <p class="text-sm font-semibold text-blue-800 mb-1">Materials:</p>
          <div class="flex flex-wrap gap-2">
            <span v-for="material in loadedMaterials" :key="material" 
                  class="inline-block px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
              📦 {{ material }}
            </span>
          </div>
        </div>
        
        <!-- Wagon Counts -->
        <div class="grid grid-cols-4 gap-4 text-center">
          <div>
            <p class="text-2xl font-bold text-blue-600">{{ data.overall.total_wagons }}</p>
            <p class="text-sm text-gray-600">Total Wagons</p>
          </div>
          <div>
            <p class="text-2xl font-bold text-green-600">{{ data.overall.loaded }}</p>
            <p class="text-sm text-gray-600">Loaded</p>
          </div>
          <div>
            <p class="text-2xl font-bold text-yellow-600">{{ data.overall.being_loaded }}</p>
            <p class="text-sm text-gray-600">Loading</p>
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-600">{{ data.overall.not_started }}</p>
            <p class="text-sm text-gray-600">Pending/Empty</p>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else-if="data && data.error" class="bg-yellow-50 border border-yellow-200 rounded p-4">
      <p class="text-yellow-700">{{ data.error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { apiService } from '../services/api'

const data = ref(null)
const loading = ref(true)
const error = ref(null)
let refreshInterval = null

// Get list of materials that have wagons (excluding Unknown if it has no activity)
const loadedMaterials = computed(() => {
  if (!data.value || !data.value.materials) return []
  
  return data.value.materials
    .filter(m => {
      // Exclude Unknown if it has no loaded or being_loaded wagons
      if (m.name === 'Unknown' && m.loaded === 0 && m.being_loaded === 0) {
        return false
      }
      return true
    })
    .map(m => m.name)
})

const fetchData = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await apiService.getSijiLoadingProgress()
    
    // Handle the DashboardResponse wrapper
    if (response && response.success) {
      data.value = response.data
    } else {
      throw new Error('Invalid response format')
    }
  } catch (err) {
    error.value = err.message || 'Failed to load loading progress'
    console.error('Error fetching Siji loading progress:', err)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString()
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleString()
}

onMounted(() => {
  fetchData()
  // Refresh every 30 seconds
  refreshInterval = setInterval(fetchData, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>
