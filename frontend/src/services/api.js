import axios from 'axios'
import { Base64 } from 'js-base64'

// Use the same origin in production, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (window.location.origin.includes('localhost') ? 'http://localhost:8003' : window.location.origin)

class ApiService {
  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    })

    // Helper function to check if token is expired
    this.isTokenExpired = (token) => {
      if (!token) return true
      
      try {
        const parts = token.split('.')
        if (parts.length !== 3) return true
        
        const payload = JSON.parse(Base64.decode(parts[1]))
        const currentTime = Math.floor(Date.now() / 1000)
        
        // Check if token expires within the next 5 minutes (300 seconds)
        return payload.exp <= (currentTime + 300)
      } catch (error) {
        console.error('Error decoding token:', error)
        return true
      }
    }

    // Request interceptor to add token
    this.api.interceptors.request.use(
      (config) => {
        console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`)
        
        const token = localStorage.getItem('token')
        
        // Check if token is expired before making request
        if (token && this.isTokenExpired(token)) {
          console.log('Token is expired or expiring soon, clearing auth state')
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          
          // Only redirect if we're not already on the login page
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          return Promise.reject(new Error('Token expired'))
        }
        
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor to handle errors
    this.api.interceptors.response.use(
      (response) => {
        return response.data
      },
      (error) => {
        // Handle 401 errors by clearing auth and redirecting
        if (error.response?.status === 401) {
          console.log('Authentication error - clearing auth state')
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          
          // Only redirect if we're not already on the login page
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
        }
        
        console.error('API Error:', error.response?.data || error.message)
        throw error
      }
    )
  }

  async healthCheck() {
    return this.api.get('/api/health')
  }

  async getForwardingOrdersData() {
    return this.api.get('/api/dashboard/forwarding-orders')
  }

  async getFirstMileTruckData() {
    return this.api.get('/api/dashboard/first-mile-truck')
  }

  async getLastMileTruckData(terminal) {
    return this.api.get(`/api/dashboard/last-mile-truck/${terminal}`)
  }

  async getStockpileData() {
    return this.api.get('/api/dashboard/stockpiles')
  }

  async getAllDashboardData() {
    return this.api.get('/api/dashboard/all')
  }

  async getDashboardData() {
    return this.api.get('/api/dashboard/all')
  }

  // Helper method to check if current token is expiring
  isCurrentTokenExpiring() {
    const token = localStorage.getItem('token')
    return this.isTokenExpired(token)
  }

  // Helper method to get current token expiration
  getCurrentTokenExpiration() {
    const token = localStorage.getItem('token')
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
}

export const apiService = new ApiService()
export default apiService
