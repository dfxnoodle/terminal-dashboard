import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

// Use the same origin in production, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (window.location.origin.includes('localhost') ? 'http://localhost:8003' : window.location.origin)

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token'))
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isOperator = computed(() => user.value?.role === 'operator' || isAdmin.value)
  const isExecutive = computed(() => user.value?.role === 'executive' || isOperator.value)
  
  const login = async (username, password) => {
    try {
      const response = await api.post('/api/auth/login', {
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
    api.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
  }
  
  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    isOperator,
    isExecutive,
    login,
    logout,
    updateProfile,
    api // Export the API instance for use in other components
  }
})
