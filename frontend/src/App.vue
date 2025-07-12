<template>
  <div id="app" class="min-h-screen bg-brand-light-gray relative overflow-hidden">
    <!-- Animated Background - hidden on login page -->
    <div v-if="!isLoginPage" class="fixed inset-0 pointer-events-none z-0 opacity-20">
      <!-- Railway tracks -->
      <div class="railway-track railway-track-1"></div>
      <div class="railway-track railway-track-2"></div>
      
      <!-- Moving trains -->
      <div class="train train-1">
        <div class="locomotive locomotive-reverse"></div>
        <div class="cargo-car cargo-car-1"></div>
        <div class="cargo-car cargo-car-2"></div>
        <div class="cargo-car cargo-car-3"></div>
      </div>
      
      <div class="train train-2">
        <div class="locomotive locomotive-reverse"></div>
        <div class="cargo-car cargo-car-1"></div>
        <div class="cargo-car cargo-car-2"></div>
        <div class="cargo-car cargo-car-3"></div>
      </div>
    </div>

    <!-- Header - hidden on login page -->
    <header v-if="!isLoginPage" class="bg-brand-dark shadow-md relative z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center py-4">
          <div class="flex items-center space-x-4">
            <img src="/etihad_rail_logo.png" alt="Etihad Rail Logo" class="h-10 w-10">
            <h1 class="text-2xl font-bold text-white">Aggregates Operations Dashboard</h1>
          </div>
          <div class="flex items-center space-x-6">
            <div class="flex items-center">
              <label for="rounding-select" class="mr-2 text-sm font-medium text-white">Stockpile Rounding:</label>
              <select id="rounding-select" v-model="rounding" @change="onRoundingChange" class="bg-gray-700 text-white border border-gray-600 rounded-md shadow-sm py-1 px-2 focus:outline-none focus:ring-brand-red focus:border-brand-red sm:text-sm">
                <option :value="0">Whole Number</option>
                <option :value="10">Nearest 10</option>
                <option :value="100">Nearest 100</option>
              </select>
            </div>
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
    <main :class="isLoginPage ? '' : 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 relative z-10'">
      <router-view :rounding="rounding" />
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
import { useRoute } from 'vue-router'
import { apiService } from './services/api'

export default {
  name: 'App',
  setup() {
    const route = useRoute()
    const connectionStatus = ref('loading')
    const lastUpdated = ref('')
    let healthCheckInterval = null
    const rounding = ref(0)

    const onRoundingChange = (event) => {
      rounding.value = parseInt(event.target.value, 10)
    }

    const isLoginPage = computed(() => {
      return route.name === 'Login'
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

    return {
      connectionStatus,
      connectionStatusText,
      lastUpdated,
      isLoginPage,
      rounding,
      onRoundingChange
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

/* Animated Train Background */
.railway-track {
  position: absolute;
  height: 4px;
  background: linear-gradient(90deg, #8B4513 0%, #8B4513 40%, transparent 40%, transparent 60%, #8B4513 60%, #8B4513 100%);
  background-size: 20px 4px;
  width: 100%;
  opacity: 0.3;
}

.railway-track-1 {
  top: 20%;
  animation: trackMove 8s linear infinite;
}

.railway-track-2 {
  top: 70%;
  animation: trackMove 12s linear infinite reverse;
}

@keyframes trackMove {
  from { background-position-x: 0; }
  to { background-position-x: 20px; }
}

.train {
  position: absolute;
  display: flex;
  align-items: center;
  height: 20px;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

.train-1 {
  top: 15%;
  animation: trainMove1 25s linear infinite;
}

.train-2 {
  top: 65%;
  animation: trainMove2 30s linear infinite reverse;
}

@keyframes trainMove1 {
  from { 
    right: -300px; 
    transform: scaleX(1);
  }
  to { 
    right: 100vw; 
    transform: scaleX(1);
  }
}

@keyframes trainMove2 {
  from { 
    right: -300px; 
    transform: scaleX(-1);
  }
  to { 
    right: 100vw; 
    transform: scaleX(-1);
  }
}

.locomotive {
  width: 60px;
  height: 20px;
  background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
  border-radius: 4px 8px 4px 4px;
  position: relative;
  margin-right: 4px;
}

.locomotive::before {
  content: '';
  position: absolute;
  top: -4px;
  left: 40px;
  width: 15px;
  height: 8px;
  background: #2c3e50;
  border-radius: 2px;
}

.locomotive-reverse {
  transform: scaleX(-1);
}

.cargo-car {
  width: 40px;
  height: 16px;
  margin-right: 4px;
  border-radius: 2px;
  position: relative;
}

.cargo-car-1 {
  background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
}

.cargo-car-2 {
  background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
}

.cargo-car-3 {
  background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
}

.cargo-car::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  right: 2px;
  bottom: 6px;
  background: rgba(255,255,255,0.1);
  border-radius: 1px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .train {
    height: 16px;
  }
  
  .locomotive {
    width: 48px;
    height: 16px;
  }
  
  .cargo-car {
    width: 32px;
    height: 12px;
  }
  
  .railway-track {
    height: 3px;
  }
}
</style>
