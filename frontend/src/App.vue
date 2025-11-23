<template>
  <div id="app" class="min-h-screen bg-brand-light-gray relative overflow-hidden">
    <!-- Animated Background - hidden on login page -->
    <RealisticTrainBackground v-if="!isLoginPage" />

    <!-- Header - hidden on login page -->
    <header v-if="!isLoginPage" class="bg-brand-dark shadow-md relative z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div class="flex items-center space-x-4 cursor-pointer hover:opacity-80 transition-opacity" @click="goToDashboard">
            <img src="/etihad_rail_logo.png" alt="Etihad Rail Logo" class="h-10 w-10 bg-white rounded-full">
            <h1 class="text-2xl font-bold text-white">{{ dashboardTitle }}</h1>
          </div>
          <div class="flex items-center space-x-6">
            <div class="flex items-center space-x-2">
              <div 
                :class="{
                  'h-3 w-3 rounded-full border-2 border-white': true,
                  'bg-green-500': connectionStatus === 'connected',
                  'bg-red-500': connectionStatus === 'error',
                  'bg-yellow-500': connectionStatus === 'loading'
                }"
              ></div>
              <span class="text-sm text-white font-medium">
                {{ connectionStatusText }}
              </span>
            </div>
            <div class="text-sm text-gray-300">
              Last Updated: {{ lastUpdated }}
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- Main content -->
    <main :class="isLoginPage ? '' : 'max-w-7xl mx-auto px-2 sm:px-6 lg:px-8 py-10 relative z-10'">
      <router-view />
    </main>

    <!-- Footer - hidden on login page -->
    <footer v-if="!isLoginPage" class="bg-brand-dark mt-12 py-4 relative z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-400 text-sm">
        &copy;{{ new Date().getFullYear() }} Linus Services Limited. All rights reserved.
      </div>
    </footer>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiService } from './services/api'
import RealisticTrainBackground from './components/RealisticTrainBackground.vue'

export default {
  name: 'App',
  components: {
    RealisticTrainBackground
  },
  setup() {
    const route = useRoute()
    const router = useRouter()
    const connectionStatus = ref('loading')
    const lastUpdated = ref('')
    let healthCheckInterval = null

    const isLoginPage = computed(() => {
      return route.name === 'Login'
    })

    const dashboardTitle = computed(() => {
      switch (route.name) {
        case 'Dashboard':
          return 'Aggregates Operations Dashboard'
        case 'IntermodalDashboard':
          return 'Intermodal Operations Dashboard'
        case 'UserManagement':
          return 'User Management'
        default:
          return 'Operations Dashboard'
      }
    })

    const connectionStatusText = computed(() => {
      switch (connectionStatus.value) {
        case 'connected': return 'API Connected'
        case 'error': return 'Connection Error'
        case 'loading': return 'Connecting...'
        default: return 'Unknown'
      }
    })

    const checkHealth = async () => {
      try {
        await apiService.healthCheck()
        connectionStatus.value = 'connected'
        lastUpdated.value = new Date().toLocaleTimeString()
      } catch (error) {
        connectionStatus.value = 'error'
        console.error('Health check failed:', error)
      }
    }

    // Watch for route changes to manage body overflow
    const updateBodyOverflow = () => {
      if (isLoginPage.value) {
        document.body.style.overflow = 'hidden'
      } else {
        document.body.style.overflow = ''
      }
    }

    onMounted(() => {
      checkHealth()
      updateBodyOverflow()
      // Check health every 30 seconds
      healthCheckInterval = setInterval(checkHealth, 30000)
    })

    onUnmounted(() => {
      if (healthCheckInterval) {
        clearInterval(healthCheckInterval)
      }
      // Reset body overflow when component unmounts
      document.body.style.overflow = ''
    })

    // Use a watcher to update overflow when route changes
    watch(isLoginPage, updateBodyOverflow)

    const goToDashboard = () => {
      if (route.name !== 'Dashboard') {
        router.push('/')
      }
    }

    return {
      connectionStatus,
      connectionStatusText,
      lastUpdated,
      isLoginPage,
      dashboardTitle,
      goToDashboard
    }
  }
}
</script>

<style>
/* Add any additional global styles here */
.bg-brand-dark {
  background-color: #2c3e50;
}

.bg-brand-light-gray {
  background-color: #ecf0f1;
}
</style>
