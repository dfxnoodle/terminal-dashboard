<template>
  <div class="login-container fixed inset-0 w-full h-full bg-brand-dark relative overflow-hidden">
    <!-- Full screen video background -->
    <div class="absolute inset-0 w-full h-full">
      <video 
        ref="videoRef"
        class="w-full h-full object-cover"
        autoplay 
        loop 
        muted
        preload="metadata"
        @loadstart="onVideoLoadStart"
        @canplay="onVideoCanPlay"
        @error="onVideoError"
      >
        <source src="/Odoo_Terminal_Video_Generation.mp4" type="video/mp4">
        Your browser does not support the video tag.
      </video>
      
      <!-- Video loading indicator -->
      <div v-if="videoLoading" class="absolute inset-0 flex items-center justify-center bg-brand-dark bg-opacity-90">
        <div class="text-center text-white">
          <div class="animate-spin rounded-full h-12 w-12 border-b-4 border-white mx-auto mb-4"></div>
          <p class="text-lg">Loading video...</p>
        </div>
      </div>
    </div>

    <!-- Dark overlay for better text readability -->
    <div class="absolute inset-0 bg-black bg-opacity-50"></div>

    <!-- Login Form Overlay -->
    <div class="relative z-10 h-full flex items-center justify-center p-8">
      <div class="max-w-md w-full">
        <!-- Login Card with Glass Effect -->
        <div class="bg-white bg-opacity-10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white border-opacity-20">
          <!-- Logo and Header -->
          <div class="text-center mb-8">
            <img src="/etihad_rail_logo.png" alt="Etihad Rail" class="mx-auto h-20 w-auto mb-6 filter brightness-0 invert">
            <h2 class="text-4xl font-bold text-white mb-2">Aggregates Operations Dashboard</h2>
            <p class="text-white text-opacity-80 text-lg">Sign in to access the dashboard</p>
          </div>

          <!-- Error Message -->
          <div v-if="error" class="bg-red-500 bg-opacity-20 border border-red-400 text-red-100 p-4 rounded-lg mb-6 backdrop-blur-sm">
            <div class="flex">
              <div class="py-1">
                <svg class="h-5 w-5 text-red-300 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
              <div>
                <p class="font-medium text-red-200">Authentication Failed</p>
                <p class="text-sm text-red-300">{{ error }}</p>
              </div>
            </div>
          </div>

          <!-- Login Form -->
          <form @submit.prevent="handleLogin" class="space-y-6">
            <div class="space-y-5">
              <!-- Username Field -->
              <div>
                <label for="username" class="block text-sm font-medium text-white text-opacity-90 mb-2">
                  Username
                </label>
                <input
                  id="username"
                  v-model="credentials.username"
                  type="text"
                  required
                  class="w-full px-4 py-3 bg-white bg-opacity-10 border border-white border-opacity-30 rounded-lg focus:ring-2 focus:ring-white focus:ring-opacity-50 focus:border-white focus:border-opacity-70 transition-all duration-300 text-white placeholder-white placeholder-opacity-50 backdrop-blur-sm"
                  placeholder="Enter your username"
                  :disabled="loading"
                >
              </div>

              <!-- Password Field -->
              <div>
                <label for="password" class="block text-sm font-medium text-white text-opacity-90 mb-2">
                  Password
                </label>
                <input
                  id="password"
                  v-model="credentials.password"
                  type="password"
                  required
                  class="w-full px-4 py-3 bg-white bg-opacity-10 border border-white border-opacity-30 rounded-lg focus:ring-2 focus:ring-white focus:ring-opacity-50 focus:border-white focus:border-opacity-70 transition-all duration-300 text-white placeholder-white placeholder-opacity-50 backdrop-blur-sm"
                  placeholder="Enter your password"
                  :disabled="loading"
                >
              </div>
            </div>

            <!-- Submit Button -->
            <div class="pt-4">
              <button
                type="submit"
                :disabled="loading"
                class="group relative w-full flex justify-center py-4 px-6 border border-transparent text-lg font-semibold rounded-lg text-white bg-brand-red bg-opacity-90 hover:bg-opacity-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white focus:ring-opacity-50 disabled:bg-gray-600 disabled:bg-opacity-50 disabled:cursor-not-allowed transition-all duration-300 backdrop-blur-sm shadow-lg"
              >
                <span v-if="loading" class="absolute left-0 inset-y-0 flex items-center pl-4">
                  <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                </span>
                {{ loading ? 'Signing in...' : 'Sign in' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Footer positioned at bottom -->
    <div class="absolute bottom-4 left-0 right-0 z-20 text-center text-sm text-white text-opacity-60">
      <p>&copy; {{ new Date().getFullYear() }} Linus Services Limited. All rights reserved.</p>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { authService } from '../services/auth'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const error = ref(null)
    const videoLoading = ref(true)
    const videoRef = ref(null)
    
    const credentials = ref({
      username: '',
      password: ''
    })

    const onVideoLoadStart = () => {
      videoLoading.value = true
    }

    const onVideoCanPlay = () => {
      videoLoading.value = false
    }

    const onVideoError = (e) => {
      console.warn('Video failed to load:', e)
      videoLoading.value = false
    }

    const handleLogin = async () => {
      loading.value = true
      error.value = null

      try {
        const success = await authService.login(credentials.value.username, credentials.value.password)
        if (success) {
          router.push('/')
        } else {
          error.value = 'Invalid username or password'
        }
      } catch (err) {
        error.value = err.message || 'An error occurred during login'
      } finally {
        loading.value = false
      }
    }

    onMounted(() => {
      // Check if already authenticated
      if (authService.isAuthenticated()) {
        router.push('/')
      }
    })

    return {
      credentials,
      loading,
      error,
      videoLoading,
      videoRef,
      handleLogin,
      onVideoLoadStart,
      onVideoCanPlay,
      onVideoError
    }
  }
}
</script>

<style scoped>
/* Ensure full screen coverage */
.login-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100vw;
  height: 100vh;
  margin: 0;
  padding: 0;
}

/* Additional styles if needed */
.video-container {
  position: relative;
}
</style>
