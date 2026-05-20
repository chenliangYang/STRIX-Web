import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

// Public routes that don't require authentication
const publicRoutes = ['/login', '/403']

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/403',
    name: 'Forbidden',
    component: () => import('@/pages/403.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/dashboard',
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/pages/Dashboard.vue'),
        meta: { title: '首页', roles: ['admin', 'user'] },
      },
      {
        path: 'tasks',
        name: 'TaskList',
        component: () => import('@/pages/tasks/TaskList.vue'),
        meta: { title: '任务管理', roles: ['admin', 'user'] },
      },
      {
        path: 'tasks/:id/runs',
        name: 'TaskRuns',
        component: () => import('@/pages/tasks/TaskRuns.vue'),
        meta: { title: '运行记录', roles: ['admin', 'user'] },
      },
      {
        path: 'tasks/:id/runs/:runId',
        name: 'RunDetail',
        component: () => import('@/pages/tasks/RunDetail.vue'),
        meta: { title: '运行详情', roles: ['admin', 'user'] },
      },
      {
        path: 'results',
        name: 'ResultList',
        component: () => import('@/pages/results/ResultList.vue'),
        meta: { title: '结果列表', roles: ['admin', 'user'] },
      },
      {
        path: 'results/:id',
        name: 'ResultDetail',
        component: () => import('@/pages/results/ResultDetail.vue'),
        meta: { title: '结果详情', roles: ['admin', 'user'] },
      },
      // System management routes - admin only
      {
        path: 'system/users',
        name: 'UserManagement',
        component: () => import('@/pages/system/UserManagement.vue'),
        meta: { title: '用户管理', roles: ['admin'] },
      },
      {
        path: 'system/whitelists',
        name: 'WhitelistManagement',
        component: () => import('@/pages/system/WhitelistManagement.vue'),
        meta: { title: '白名单管理', roles: ['admin'] },
      },
      {
        path: 'system/audit-logs',
        name: 'AuditLogs',
        component: () => import('@/pages/system/AuditLogs.vue'),
        meta: { title: '审计日志', roles: ['admin'] },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Store reference for route guard
let resolveAuthInit: (() => void) | null = null
const authInitPromise = new Promise<void>((resolve) => {
  resolveAuthInit = resolve
})

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // Initialize auth if needed
  if (authStore.token && !authStore.user && !authStore.isLoading) {
    authStore.fetchUser().finally(() => {
      if (resolveAuthInit) {
        resolveAuthInit()
        resolveAuthInit = null
      }
    })
  }

  // If auth is loading, wait for it
  if (authStore.token && authStore.isLoading) {
    await authInitPromise
  }

  // Allow public routes without authentication
  if (publicRoutes.includes(to.path)) {
    // If already logged in, redirect to home
    if (to.path === '/login' && authStore.isLoggedIn) {
      next('/dashboard')
      return
    }
    next()
    return
  }

  // No token -> redirect to login
  if (!authStore.token) {
    next(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
    return
  }

  // Token exists but user info loading failed -> redirect to login
  if (authStore.initError && !authStore.user) {
    next(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
    return
  }

  // Token exists, user info is loading -> wait for it
  if (authStore.isLoading) {
    await new Promise((resolve) => setTimeout(resolve, 100))
    return router.beforeEach((_t, _f, n) => { n() }) // Skip this guard
  }

  // Token exists but no user info yet -> fetch and wait
  if (authStore.token && !authStore.user) {
    try {
      await authStore.fetchUser()
    } catch (error) {
      next(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
      return
    }
  }

  // Now we have both token and user info
  if (!authStore.user) {
    next(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
    return
  }

  // Check role-based access
  const requiredRoles = to.meta.roles as string[] | undefined
  if (requiredRoles && requiredRoles.length > 0) {
    const userRole = authStore.user.role
    if (!requiredRoles.includes(userRole)) {
      ElMessage.error('您没有权限访问此页面')
      next('/dashboard')
      return
    }
  }

  next()
})

export default router
