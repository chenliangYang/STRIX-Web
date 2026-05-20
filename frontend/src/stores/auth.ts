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
  const isLoading = ref(false)
  const initError = ref<string | null>(null)

  // isLoggedIn: 只要有 token 就认为是登录状态
  // user 信息是异步加载的，不应阻塞登录状态判断
  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const currentUserId = computed(() => user.value?.id || '')
  const currentRole = computed(() => user.value?.role || '')
  const isUserLoaded = computed(() => !!user.value)

  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  const setUser = (newUser: User) => {
    user.value = newUser
  }

  const clearAuth = () => {
    token.value = null
    user.value = null
    isLoading.value = false
    localStorage.removeItem('token')
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
    clearAuth()
  }

  const fetchUser = async () => {
    if (!token.value) {
      clearAuth()
      throw new Error('No token')
    }

    if (isLoading.value) {
      return // Already loading
    }

    isLoading.value = true
    initError.value = null

    try {
      const response = await apiGetMe() as any
      if (response.code === 0) {
        setUser(response.data)
      } else {
        clearAuth()
        throw new Error('Failed to fetch user')
      }
    } catch (error: any) {
      initError.value = error.message
      clearAuth()
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // Initialize user if token exists (called once on app startup)
  const initAuth = () => {
    if (token.value && !user.value && !isLoading.value) {
      fetchUser()
    }
  }

  return {
    token,
    user,
    isLoading,
    initError,
    isLoggedIn,
    isAdmin,
    isUserLoaded,
    currentUserId,
    currentRole,
    setToken,
    setUser,
    clearAuth,
    login,
    logout,
    fetchUser,
    initAuth,
  }
})
