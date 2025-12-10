import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('chatbot_token') || null)
  const user = ref(null)
  const isAuthenticated = ref(!!token.value)
  
  const login = async (username, password) => {
    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      })
      
      if (!response.ok) {
        throw new Error('Неверные учетные данные')
      }
      
      const data = await response.json()
      setToken(data.access_token)
      return data
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }
  
  const register = async (username, password) => {
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ username, password })
      })
      
      if (!response.ok) {
        throw new Error('Ошибка регистрации')
      }
      
      const data = await response.json()
      setToken(data.access_token)
      return data
    } catch (error) {
      console.error('Registration error:', error)
      throw error
    }
  }
  
  const logout = () => {
    localStorage.removeItem('chatbot_token')
    token.value = null
    user.value = null
    isAuthenticated.value = false
  }
  
  const setToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('chatbot_token', newToken)
    isAuthenticated.value = true
  }
  
  const verifyToken = async () => {
    if (!token.value) return false
    
    try {
      const response = await fetch('/api/auth/verify', {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        user.value = data.user
        return true
      } else {
        logout()
        return false
      }
    } catch (error) {
      console.error('Token verification error:', error)
      logout()
      return false
    }
  }
  
  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    logout,
    verifyToken
  }
})
