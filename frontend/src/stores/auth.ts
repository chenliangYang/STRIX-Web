import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, logout as apiLogout, getMe as apiGetMe } from '@/api/auth'

interface User {
  id: string
  username: string
  account: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const setUser = (newUser: User) => {
    user.value = newUser
  }

  const login = async (account: string, password: string, role: string) => {
    try {
      const response = await apiLogin({ account, password, role }) as any
      if (response.code === 0) {
        setToken(response.data.token)
        setUser(response.data.user)
        return { success: true }
      } else {
        return { success: false, message: response.message }
      }
    } catch (error: any) {
      return { success: false, message: error.response?.data?.message || '登录失败' }
    }
  }

  const logout = async () => {
    try {
      await apiLogout()
    } catch (error) {
      // Ignore logout errors
    }
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  const fetchUser = async () => {
    if (!token.value) return
    try {
      const response = await apiGetMe() as any
      if (response.code === 0) {
        setUser(response.data)
      }
    } catch (error) {
      // Token invalid, clear it
      logout()
    }
  }

  // Initialize user if token exists
  if (token.value) {
    fetchUser()
  }

  return {
    token,
    user,
    isLoggedIn,
    isAdmin,
    setToken,
    setUser,
    login,
    logout,
    fetchUser,
  }
})
