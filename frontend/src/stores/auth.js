import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/composables/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem('token') || localStorage.getItem('auth_token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const isLoading = ref(false)
  const error = ref(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin || false)

  // Actions
  const login = async (credentials) => {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await api.post('/api/auth/login', credentials)
      
      token.value = response.data.access_token
      user.value = response.data.user
      
      // Store in localStorage (using 'token' for consistency)
      localStorage.setItem('token', token.value)
      localStorage.setItem('auth_token', token.value) // Keep both for compatibility
      localStorage.setItem('user', JSON.stringify(user.value))
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const register = async (userData) => {
    try {
      isLoading.value = true
      error.value = null
      
      const response = await api.post('/api/auth/register', userData)
      
      // Auto-login after registration
      await login({
        username: userData.username,
        password: userData.password
      })
      
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Registration failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  const logout = () => {
    token.value = null
    user.value = null
    
    // Remove from localStorage
    localStorage.removeItem('token')
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user')
  }

  const fetchUserInfo = async () => {
    try {
      const response = await api.get('/api/auth/me')
      user.value = response.data
      localStorage.setItem('user', JSON.stringify(user.value))
      return response.data
    } catch (err) {
      // If token is invalid, logout
      logout()
      throw err
    }
  }

  const updateUserSettings = async (settings) => {
    try {
      const response = await api.put('/api/auth/me', settings)
      user.value = response.data
      localStorage.setItem('user', JSON.stringify(user.value))
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || 'Settings update failed'
      throw err
    }
  }

  const initializeAuth = () => {
    // Auth is handled by the API interceptor
    // No need to set axios headers manually
  }

  const clearError = () => {
    error.value = null
  }

  return {
    // State
    token,
    user,
    isLoading,
    error,
    
    // Getters
    isAuthenticated,
    isAdmin,
    
    // Actions
    login,
    register,
    logout,
    fetchUserInfo,
    updateUserSettings,
    initializeAuth,
    clearError
  }
})