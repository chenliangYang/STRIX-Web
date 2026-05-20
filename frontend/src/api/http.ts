import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// Store original console.error for debugging
const originalError = console.error.bind(console)

http.interceptors.request.use(
  (config) => {
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

http.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const status = error.response?.status
    const responseData = error.response?.data

    // Handle 401 - Unauthorized
    if (status === 401) {
      // Clear auth state
      localStorage.removeItem('token')

      // Redirect to login
      const currentPath = window.location.pathname
      window.location.href = `/login?redirect=${encodeURIComponent(currentPath)}`
      return Promise.reject(new Error('登录已过期，请重新登录'))
    }

    // Handle 403 - Forbidden
    if (status === 403) {
      const message = responseData?.detail || '您没有权限访问此资源'
      ElMessage.error(message)

      // If already on login page, don't redirect
      if (window.location.pathname !== '/login') {
        router.push('/dashboard')
      }
      return Promise.reject(error)
    }

    // Handle other errors
    if (status === 404) {
      const message = responseData?.detail || '资源不存在'
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

export default http
