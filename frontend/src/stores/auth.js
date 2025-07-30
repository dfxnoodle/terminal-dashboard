import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { Base64 } from 'js-base64'

// Use the same origin in production, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (window.location.origin.includes('localhost') ? 'http://localhost:8003' : window.location.origin)

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token'))
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const refreshing = ref(false)
  let tokenRefreshInterval = null
  
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isOperator = computed(() => user.value?.role === 'operator' || isAdmin.value)
  const isExecutive = computed(() => user.value?.role === 'executive' || isOperator.value)

  // Helper function to decode JWT and check expiration
  const isTokenExpired = (token) => {
    if (!token) return true
    
    try {
      const parts = token.split('.')
      if (parts.length !== 3) return true
      
      const payload = JSON.parse(Base64.decode(parts[1]))
      const currentTime = Math.floor(Date.now() / 1000)
      
      // Check if token expires within the next 5 minutes (300 seconds)
      // This gives us time to handle renewal before it actually expires
      return payload.exp <= (currentTime + 300)
    } catch (error) {
      console.error('Error decoding token:', error)
      return true
    }
  }

  // Helper function to check if token needs refresh (expires within 10 minutes)
  const isTokenNearExpiry = (token) => {
    if (!token) return false
    
    try {
      const parts = token.split('.')
      if (parts.length !== 3) return false
      
      const payload = JSON.parse(Base64.decode(parts[1]))
      const currentTime = Math.floor(Date.now() / 1000)
      
      // Check if token expires within the next 10 minutes (600 seconds)
      return payload.exp <= (currentTime + 600)
    } catch (error) {
      console.error('Error decoding token:', error)
      return false
    }
  }

  // Helper function to get token expiration time
  const getTokenExpiration = (token) => {
    if (!token) return null
    
    try {
      const parts = token.split('.')
      if (parts.length !== 3) return null
      
      const payload = JSON.parse(Base64.decode(parts[1]))
      return new Date(payload.exp * 1000)
    } catch (error) {
      console.error('Error decoding token:', error)
      return null
    }
  }

  // Function to automatically refresh token by calling the backend
  const refreshToken = async () => {
    if (refreshing.value) return false
    
    refreshing.value = true
    console.log('Attempting to refresh token...')
    
    try {
      const response = await api.post('/api/auth/refresh-token')
      
      if (response.success) {
        token.value = response.token
        user.value = response.user
        
        localStorage.setItem('token', token.value)
        localStorage.setItem('user', JSON.stringify(user.value))
        
        // Update authorization header
        api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
        
        console.log('Token refreshed successfully')
        return true
      } else {
        console.log('Token refresh failed:', response.message)
        return false
      }
      
    } catch (error) {
      console.error('Token refresh failed:', error)
      // If refresh fails due to auth error, the interceptor will handle logout
      return false
    } finally {
      refreshing.value = false
    }
  }

  // Start token refresh monitoring
  const startTokenRefreshMonitoring = () => {
    if (tokenRefreshInterval) {
      clearInterval(tokenRefreshInterval)
    }
    
    // Check every 5 minutes if token needs refresh
    tokenRefreshInterval = setInterval(async () => {
      if (token.value && isTokenNearExpiry(token.value)) {
        console.log('Token is near expiry, attempting refresh...')
        const refreshed = await refreshToken()
        
        if (!refreshed) {
          console.log('Token refresh failed, user will need to re-authenticate')
          // Don't force logout here, let the user see the warning and choose when to refresh
        }
      }
    }, 5 * 60 * 1000) // Check every 5 minutes
  }

  // Stop token refresh monitoring
  const stopTokenRefreshMonitoring = () => {
    if (tokenRefreshInterval) {
      clearInterval(tokenRefreshInterval)
      tokenRefreshInterval = null
    }
  }

  // Create axios instance
  const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json'
    }
  })

  // Request interceptor to add token
  api.interceptors.request.use(
    (config) => {
      console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`)
      
      // Check if token is expired before making request
      if (token.value && isTokenExpired(token.value)) {
        console.log('Token is expired or expiring soon, clearing auth state')
        forceLogout()
        return Promise.reject(new Error('Token expired'))
      }
      
      if (token.value) {
        config.headers.Authorization = `Bearer ${token.value}`
      }
      
      return config
    },
    (error) => {
      return Promise.reject(error)
    }
  )

  // Response interceptor to handle token expiration
  api.interceptors.response.use(
    (response) => {
      return response.data
    },
    async (error) => {
      const originalRequest = error.config

      // Handle 401 errors (token expired/invalid)
      if (error.response?.status === 401 && !originalRequest._retry) {
        console.log('Token expired, attempting to refresh...')
        
        // Mark this request as retried to avoid infinite loops
        originalRequest._retry = true
        
        // If we're already refreshing, wait for it to complete
        if (refreshing.value) {
          return new Promise((resolve) => {
            // Wait a bit and retry
            setTimeout(() => {
              if (token.value) {
                originalRequest.headers.Authorization = `Bearer ${token.value}`
                resolve(api(originalRequest))
              } else {
                forceLogout()
                resolve(Promise.reject(error))
              }
            }, 1000)
          })
        }

        // Try to refresh the token
        try {
          const refreshed = await refreshToken()
          
          if (refreshed) {
            // Retry the original request with new token
            originalRequest.headers.Authorization = `Bearer ${token.value}`
            return api(originalRequest)
          } else {
            // Refresh failed, force logout
            console.log('Token refresh failed, redirecting to login...')
            forceLogout()
            return Promise.reject(error)
          }
          
        } catch (refreshError) {
          console.error('Token refresh failed:', refreshError)
          forceLogout()
          return Promise.reject(error)
        }
      }
      
      console.error('API Error:', error.response?.data || error.message)
      throw error
    }
  )

  const forceLogout = () => {
    token.value = null
    user.value = null
    
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    
    delete api.defaults.headers.common['Authorization']
    
    // Stop monitoring token expiration
    stopTokenRefreshMonitoring()
    
    // Redirect to login page
    if (typeof window !== 'undefined') {
      window.location.href = '/login'
    }
  }
  
  const login = async (username, password) => {
    try {
      // Use a fresh instance for login to avoid auth headers
      const loginApi = axios.create({
        baseURL: API_BASE_URL,
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
        }
      })

      const response = await loginApi.post('/api/auth/login', {
        username,
        password
      })
      
      if (response.data.success) {
        token.value = response.data.token
        user.value = response.data.user
        
        localStorage.setItem('token', token.value)
        localStorage.setItem('user', JSON.stringify(user.value))
        
        // Set default authorization header
        api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
        
        // Start monitoring token expiration
        startTokenRefreshMonitoring()
        
        return { success: true }
      } else {
        return { success: false, message: response.data.message }
      }
    } catch (error) {
      console.error('Login error:', error)
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Login failed' 
      }
    }
  }
  
  const logout = () => {
    token.value = null
    user.value = null
    
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    
    delete api.defaults.headers.common['Authorization']
    
    // Stop monitoring token expiration
    stopTokenRefreshMonitoring()
  }
  
  const updateProfile = async (data) => {
    try {
      const response = await api.post('/api/auth/change-password', data)
      return response.data
    } catch (error) {
      console.error('Profile update error:', error)
      return { 
        success: false, 
        message: error.response?.data?.detail || 'Update failed' 
      }
    }
  }
  
  // Initialize authorization header if token exists
  if (token.value) {
    // Check if stored token is still valid
    if (isTokenExpired(token.value)) {
      console.log('Stored token is expired, clearing auth state')
      forceLogout()
    } else {
      api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
      // Start monitoring for existing valid tokens
      startTokenRefreshMonitoring()
    }
  }

  // Helper method to check if current token is about to expire
  const isCurrentTokenExpiring = () => {
    return isTokenExpired(token.value)
  }

  // Helper method to get current token expiration
  const getCurrentTokenExpiration = () => {
    return getTokenExpiration(token.value)
  }
  
  return {
    token,
    user,
    refreshing,
    isAuthenticated,
    isAdmin,
    isOperator,
    isExecutive,
    login,
    logout,
    updateProfile,
    isCurrentTokenExpiring,
    getCurrentTokenExpiration,
    refreshToken,
    api // Export the API instance for use in other components
  }
})
