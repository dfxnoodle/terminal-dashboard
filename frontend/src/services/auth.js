class AuthService {
  constructor() {
    this.tokenKey = 'dashboard_auth_token'
    this.userKey = 'dashboard_auth_user'
  }

  async login(username, password) {
    try {
      // Get credentials from environment variables via backend
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          // Store authentication state
          localStorage.setItem(this.tokenKey, data.token || 'authenticated')
          localStorage.setItem(this.userKey, JSON.stringify({ username }))
          return true
        }
      }
      
      return false
    } catch (error) {
      console.error('Login error:', error)
      throw new Error('Network error occurred')
    }
  }

  logout() {
    localStorage.removeItem(this.tokenKey)
    localStorage.removeItem(this.userKey)
  }

  isAuthenticated() {
    const token = localStorage.getItem(this.tokenKey)
    return !!token
  }

  getUser() {
    const userStr = localStorage.getItem(this.userKey)
    return userStr ? JSON.parse(userStr) : null
  }

  getToken() {
    return localStorage.getItem(this.tokenKey)
  }
}

export const authService = new AuthService()
