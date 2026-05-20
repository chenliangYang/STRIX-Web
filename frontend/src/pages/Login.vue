<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2 class="login-title">AI 渗透测试平台</h2>
      </template>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="账号" prop="account">
          <el-input v-model="form.account" placeholder="请输入账号" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  account: '',
  password: '',
  role: 'admin',
})

const rules = {
  account: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const result = await authStore.login(form.account, form.password, form.role)
      if (result.success) {
        ElMessage.success('登录成功')
        router.push('/dashboard')
      } else {
        ElMessage.error(result.message || '登录失败')
      }
    } catch (error: any) {
      ElMessage.error(error.message || '登录失败')
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-container {
  width: 100%;
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1a1f35 0%, #0d1117 50%, #161b22 100%);
}

.login-card {
  width: 400px;
  background: rgba(22, 27, 34, 0.95) !important;
  border: 1px solid rgba(59, 130, 246, 0.3) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
}

.login-title {
  text-align: center;
  margin: 0;
  color: #f0f6fc;
}

/* Card Header */
.login-card :deep(.el-card__header) {
  background: rgba(22, 27, 34, 0.95) !important;
  border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
  padding: 20px;
}

.login-card :deep(.el-card__body) {
  background: rgba(22, 27, 34, 0.95) !important;
  padding: 30px 20px;
}

/* Form */
.login-card :deep(.el-form-item__label) {
  color: #8b949e !important;
}

.login-card :deep(.el-form-item__error) {
  color: #f85149 !important;
}

.login-card :deep(.el-input__wrapper) {
  background: rgba(13, 17, 23, 0.8) !important;
  box-shadow: none !important;
  border: 1px solid rgba(59, 130, 246, 0.3) !important;
}

.login-card :deep(.el-input__wrapper:hover) {
  border-color: rgba(59, 130, 246, 0.5) !important;
}

.login-card :deep(.el-input__wrapper.is-focus) {
  border-color: #58a6ff !important;
}

.login-card :deep(.el-input__inner) {
  color: #e6edf3 !important;
}

.login-card :deep(.el-input__inner::placeholder) {
  color: #6e7681 !important;
}

/* Select */
.login-card :deep(.el-select) {
  width: 100%;
}

.login-card :deep(.el-select .el-input__wrapper) {
  background: rgba(13, 17, 23, 0.8) !important;
}

.login-card :deep(.el-select-dropdown) {
  background: rgba(22, 27, 34, 0.98) !important;
  border: 1px solid rgba(59, 130, 246, 0.2) !important;
}

.login-card :deep(.el-select-dropdown__item) {
  color: #e6edf3 !important;
}

.login-card :deep(.el-select-dropdown__item:hover) {
  background: rgba(59, 130, 246, 0.1) !important;
}

.login-card :deep(.el-select-dropdown__item.selected) {
  color: #58a6ff !important;
}

/* Button */
.login-card :deep(.el-button--primary) {
  background: #58a6ff !important;
  border-color: #58a6ff !important;
}

.login-card :deep(.el-button--primary:hover) {
  background: #79b8ff !important;
  border-color: #79b8ff !important;
}
</style>
