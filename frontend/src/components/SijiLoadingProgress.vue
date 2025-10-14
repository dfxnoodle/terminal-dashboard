<template>
  <div class="bg-white rounded-lg overflow-hidden">
    
    <div class="p-2">
    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      <p class="mt-4 text-gray-600">Loading train data...</p>
    </div>
    
    <div v-else-if="error" class="bg-red-50 border border-red-200 rounded p-2">
      <p class="text-red-600">{{ error }}</p>
    </div>
    
    <div v-else-if="data && !data.error">
      <!-- Header Info -->
      <div class="flex justify-between items-center mb-6 p-2 bg-gray-50 rounded text-base">
        <div>
          <span class="text-gray-600">Train ID:</span>
          <span class="font-bold ml-1">{{ data.train_id }}</span>
        </div>
        <div>
          <span class="text-gray-600">Status:</span>
          <span class="font-bold text-green-600 ml-1">{{ data.status }}</span>
        </div>
        <div>
          <span class="text-gray-600">Loading Date:</span>
          <span class="ml-1">{{ formatDate(data.loading_date) }}</span>
        </div>
      </div>
      
      <!-- Overall Summary -->
      <div>
             
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

        <br></br>
        <!-- Material Being Loaded -->
        <div v-if="loadedMaterials.length > 0" class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded flex items-center gap-3 text-sm">
          <span class="font-semibold text-blue-800">Materials:</span>
          <div class="flex flex-wrap gap-2">
            <span v-for="material in loadedMaterials" :key="material" 
                  class="inline-block px-3 py-2 bg-blue-100 text-blue-700 rounded-full">
              {{ material }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <div v-else-if="data && data.error" class="bg-yellow-50 border border-yellow-200 rounded p-4">
      <p class="text-yellow-700">{{ data.error }}</p>
    </div>
    </div> <!-- End padding div -->
  </div> <!-- End card div -->
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
