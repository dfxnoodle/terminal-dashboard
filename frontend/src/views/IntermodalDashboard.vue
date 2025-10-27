<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Navigation Bar -->
    <nav class="bg-white shadow-sm border-b border-gray-200">
      <div class="max-w-full mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <img src="/etihad_rail_logo.png" alt="Etihad Rail" class="h-8 w-auto">
            <h1 class="ml-4 text-xl font-semibold text-gray-900">Operations Dashboard</h1>
          </div>
          
          <div class="flex items-center space-x-4">
            <!-- User Info -->
            <div class="flex items-center space-x-3">
              <span class="text-sm text-gray-700">Welcome, {{ user?.full_name || user?.username }}</span>
              <span :class="getRoleClass(user?.role)" class="px-2 py-1 text-xs font-medium rounded-full">
                {{ formatRole(user?.role) }}
              </span>
            </div>
            
            <!-- Dashboard Switcher -->
            <div class="border-l border-gray-300 pl-4">
              <button
                @click="switchToAggregates"
                class="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 transition-colors"
                title="Switch to Aggregates Dashboard"
              >
                <i class="fas fa-exchange-alt"></i>
                <span>Aggregates</span>
              </button>
            </div>
            
            <!-- Admin Menu -->
            <div v-if="authStore.isAdmin" class="relative">
              <button 
                @click="showAdminMenu = !showAdminMenu"
                class="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50"
              >
                <i class="fas fa-cog"></i>
                <span>Admin</span>
                <i class="fas fa-chevron-down"></i>
              </button>
              
              <div v-if="showAdminMenu" class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                <router-link 
                  to="/admin/users" 
                  class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  @click="showAdminMenu = false"
                >
                  <i class="fas fa-users mr-2"></i>
                  User Management
                </router-link>
              </div>
            </div>
            
            <!-- Logout Button -->
            <button 
              @click="handleLogout"
              class="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50"
            >
              <i class="fas fa-sign-out-alt"></i>
              <span>Logout</span>
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- Dashboard Content -->
    <div class="p-2 md:p-4 space-y-4">
      <!-- Train Departures Chart -->
      <div class="card">
        <h2 class="card-header">Train Departures</h2>
        <div class="p-4">
          <div v-if="loading" class="flex justify-center items-center py-12">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-brand-red"></div>
          </div>
          <div v-else-if="error" class="text-center py-8 text-red-600">
            <i class="fas fa-exclamation-triangle text-4xl mb-2"></i>
            <p>{{ error }}</p>
          </div>
          <div v-else-if="trainData && trainData.length > 0">
            <IntermodalTrainDepartures :trains="trainData" />
          </div>
          <div v-else class="text-center py-12 text-gray-500">
            <i class="fas fa-train text-4xl mb-2"></i>
            <p>No train departure data available</p>
          </div>
        </div>
      </div>

      <!-- RUW Container Status Component -->
      <RUWContainerStatus />

      <!-- Refresh Controls -->
      <div class="flex justify-center items-center space-x-4 pt-4 border-t border-gray-200 mt-6">
        <button 
          @click="fetchTrainDepartures" 
          :disabled="loading"
          class="bg-brand-red hover:bg-red-700 disabled:bg-gray-400 text-white px-8 py-3 rounded-full font-bold text-lg shadow-lg transform hover:scale-105 transition-transform duration-300"
        >
          {{ loading ? 'Refreshing...' : 'Refresh Now' }}
        </button>
        
        <!-- Auto-Refresh Radio Toggle -->
        <div class="flex items-center bg-white rounded-full shadow-md px-2 py-1 border border-gray-300">
          <span class="text-sm font-medium text-gray-700 mr-3 ml-2">Auto-Refresh:</span>
          <div class="flex gap-1">
            <button 
              @click="setAutoRefresh(false)"
              :class="{
                'bg-gray-600 text-white': !autoRefresh,
                'bg-gray-100 text-gray-600 hover:bg-gray-200': autoRefresh
              }"
              class="px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200"
            >
              OFF
            </button>
            <button 
              @click="setAutoRefresh(true)"
              :class="{
                'bg-green-600 text-white': autoRefresh,
                'bg-gray-100 text-gray-600 hover:bg-gray-200': !autoRefresh
              }"
              class="px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-200"
            >
              ON
            </button>
          </div>
        </div>
      </div>
    </div> <!-- End dashboard content -->
  </div> <!-- End main container -->
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import RUWContainerStatus from '../components/RUWContainerStatus.vue'
import IntermodalTrainDepartures from '../components/IntermodalTrainDepartures.vue'
import apiService from '../services/api'

const router = useRouter()
const authStore = useAuthStore()
const currentTime = ref('')
const showAdminMenu = ref(false)
const loading = ref(true)
const error = ref(null)
const trainData = ref([])
const autoRefresh = ref(true)

let timeInterval = null
let refreshInterval = null

const user = computed(() => authStore.user)

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('en-GB', {
    timeZone: 'Asia/Dubai',
    dateStyle: 'medium',
    timeStyle: 'short'
  })
}

const fetchTrainDepartures = async () => {
  try {
    loading.value = true
    error.value = null
    const response = await apiService.getIntermodalTrainDepartures(14)
    
    if (response.success && response.data && response.data.trains) {
      trainData.value = response.data.trains
    } else {
      error.value = 'No train data available'
    }
  } catch (err) {
    console.error('Error fetching train departures:', err)
    error.value = err.detail || err.message || 'Failed to load train departure data'
  } finally {
    loading.value = false
  }
}

const handleLogout = () => {
  localStorage.removeItem('dashboardType')
  authStore.logout()
  router.push('/login')
}

const switchToAggregates = () => {
  localStorage.setItem('dashboardType', 'aggregates')
  router.push('/')
}

const getRoleClass = (role) => {
  const classes = {
    admin: 'bg-red-100 text-red-800',
    operator: 'bg-orange-100 text-orange-800',
    executive: 'bg-green-100 text-green-800',
    visitor: 'bg-gray-100 text-gray-800'
  }
  return classes[role] || 'bg-gray-100 text-gray-800'
}

const formatRole = (role) => {
  return role ? role.charAt(0).toUpperCase() + role.slice(1) : ''
}

const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    // Refresh every 5 minutes
    if (refreshInterval) {
      clearInterval(refreshInterval)
    }
    refreshInterval = setInterval(() => {
      if (!loading.value) {
        fetchTrainDepartures()
      }
    }, 5 * 60 * 1000)
  } else {
    if (refreshInterval) {
      clearInterval(refreshInterval)
    }
  }
}

const setAutoRefresh = (enabled) => {
  if (enabled === autoRefresh.value) {
    return // Already in the desired state
  }
  toggleAutoRefresh()
}

onMounted(() => {
  // Check authentication
  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }

  // Check if user is admin
  if (!authStore.isAdmin) {
    router.push('/')
    return
  }

  updateTime()
  timeInterval = setInterval(updateTime, 1000)
  
  // Fetch train departures initially
  fetchTrainDepartures()
  
  // Refresh train departures every 5 minutes
  refreshInterval = setInterval(fetchTrainDepartures, 5 * 60 * 1000)
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
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
