<template>
  <div class="admin-layout">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="logo">
        <span v-if="!sidebarCollapsed">STRIX Web</span>
        <span v-else>SW</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="sidebarCollapsed"
        :router="true"
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/tasks">
          <span>任务管理</span>
        </el-menu-item>
        <el-menu-item index="/results">
          <span>结果列表</span>
        </el-menu-item>
        <el-sub-menu v-if="authStore.isAdmin" index="system">
          <template #title>
            <span>系统管理</span>
          </template>
          <el-menu-item index="/system/users">用户管理</el-menu-item>
          <el-menu-item index="/system/whitelists">白名单管理</el-menu-item>
          <el-menu-item index="/system/audit-logs">审计日志</el-menu-item>
        </el-sub-menu>
      </el-menu>
    </aside>
    <div class="main-container">
      <header class="header">
        <div class="header-left">
          <el-button
            text
            @click="sidebarCollapsed = !sidebarCollapsed"
          >
            <span v-if="sidebarCollapsed">展开</span>
            <span v-else>收起</span>
          </el-button>
        </div>
        <div class="header-right">
          <span class="user-info">
            {{ authStore.user?.username }} ({{ authStore.user?.role === 'admin' ? '管理员' : '用户' }})
          </span>
          <el-button type="danger" size="small" @click="handleLogout">
            退出登录
          </el-button>
        </div>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const sidebarCollapsed = ref(false)
const activeMenu = computed(() => route.path)

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  height: 100vh;
}

.sidebar {
  width: 200px;
  background: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.sidebar.collapsed {
  width: 64px;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 18px;
  font-weight: bold;
  background: #2b3a4a;
}

.sidebar-menu {
  border-right: none;
  background: #304156;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 200px;
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-info {
  color: #666;
}

.content {
  flex: 1;
  overflow: auto;
  background: #f0f2f5;
}
</style>
