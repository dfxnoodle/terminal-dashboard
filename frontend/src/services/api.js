import axios from 'axios'

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

    // Request interceptor
    this.api.interceptors.request.use(
      (config) => {
        console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`)
        
        // Add auth token from localStorage for dashboard requests
        const token = localStorage.getItem('token')
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        
        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.api.interceptors.response.use(
      (response) => {
        return response.data
      },
      (error) => {
        // Handle 401 errors by redirecting to login
        if (error.response?.status === 401) {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          window.location.href = '/login'
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
}

export const apiService = new ApiService()
export default apiService
