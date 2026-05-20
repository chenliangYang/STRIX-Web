import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/Login.vue'),
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
        meta: { title: '首页' },
      },
      {
        path: 'tasks',
        name: 'TaskList',
        component: () => import('@/pages/tasks/TaskList.vue'),
        meta: { title: '任务管理' },
      },
      {
        path: 'tasks/:id/runs',
        name: 'TaskRuns',
        component: () => import('@/pages/tasks/TaskRuns.vue'),
        meta: { title: '运行记录' },
      },
      {
        path: 'tasks/:id/runs/:runId',
        name: 'RunDetail',
        component: () => import('@/pages/tasks/RunDetail.vue'),
        meta: { title: '运行详情' },
      },
      {
        path: 'results',
        name: 'ResultList',
        component: () => import('@/pages/results/ResultList.vue'),
        meta: { title: '结果列表' },
      },
      {
        path: 'results/:id',
        name: 'ResultDetail',
        component: () => import('@/pages/results/ResultDetail.vue'),
        meta: { title: '结果详情' },
      },
      {
        path: 'system/users',
        name: 'UserManagement',
        component: () => import('@/pages/system/UserManagement.vue'),
        meta: { title: '用户管理', requiresAdmin: true },
      },
      {
        path: 'system/whitelists',
        name: 'WhitelistManagement',
        component: () => import('@/pages/system/WhitelistManagement.vue'),
        meta: { title: '白名单管理', requiresAdmin: true },
      },
      {
        path: 'system/audit-logs',
        name: 'AuditLogs',
        component: () => import('@/pages/system/AuditLogs.vue'),
        meta: { title: '审计日志', requiresAdmin: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth !== false && !authStore.isLoggedIn) {
    next('/login')
    return
  }

  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/dashboard')
    return
  }

  next()
})

export default router
