<template>
  <div class="user-management">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>用户管理</span>
          <el-button type="primary" @click="openCreateDialog">
            新建用户
          </el-button>
        </div>
      </template>

      <el-table :data="users" v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="account" label="账号" width="150" />
        <el-table-column prop="role" label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
              {{ row.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="department" label="部门" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'enabled' ? 'success' : 'danger'">
              {{ row.status === 'enabled' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="280">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button
              size="small"
              :type="row.status === 'enabled' ? 'warning' : 'success'"
              @click="toggleStatus(row)"
            >
              {{ row.status === 'enabled' ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" @click="resetPassword(row)">重置密码</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 20px"
        @current-change="loadUsers"
        @size-change="loadUsers"
      />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="showDialog"
      :title="editingUser ? '编辑用户' : '新建用户'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="账号" prop="account">
          <el-input v-model="form.account" placeholder="请输入账号" :disabled="!!editingUser" />
        </el-form-item>
        <el-form-item v-if="!editingUser" label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="form.role" style="width: 100%">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-input v-model="form.department" placeholder="请输入部门" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import {
  getUsers,
  createUser,
  updateUser,
  deleteUser,
  enableUser,
  disableUser,
  resetUserPassword,
} from '@/api/system'

const users = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editingUser = ref<any>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const form = reactive({
  username: '',
  account: '',
  password: '',
  role: 'user',
  department: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  account: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

const loadUsers = async () => {
  loading.value = true
  try {
    const response = await getUsers({
      page: pagination.page,
      pageSize: pagination.pageSize,
    }) as any
    if (response.code === 0) {
      users.value = response.data?.items || []
      pagination.total = response.data?.total || 0
    }
  } catch (error) {
    console.error('Failed to load users:', error)
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  editingUser.value = null
  Object.assign(form, {
    username: '',
    account: '',
    password: '',
    role: 'user',
    department: '',
  })
  showDialog.value = true
}

const openEditDialog = (user: any) => {
  editingUser.value = user
  Object.assign(form, {
    username: user.username,
    account: user.account,
    password: '',
    role: user.role,
    department: user.department || '',
  })
  showDialog.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      let response: any

      if (editingUser.value) {
        const data: any = {
          username: form.username,
          role: form.role,
          department: form.department || undefined,
        }
        response = await updateUser(editingUser.value.id, data)
      } else {
        response = await createUser({
          username: form.username,
          account: form.account,
          password: form.password,
          role: form.role,
          department: form.department || undefined,
        })
      }

      if (response.code === 0) {
        ElMessage.success(editingUser.value ? '更新成功' : '创建成功')
        showDialog.value = false
        loadUsers()
      } else {
        ElMessage.error(response.message || '操作失败')
      }
    } catch (error: any) {
      ElMessage.error(error.response?.data?.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const toggleStatus = (user: any) => {
  const action = user.status === 'enabled' ? '禁用' : '启用'
  ElMessageBox.confirm(`确定要${action}该用户吗?`, '提示', {
    type: 'warning',
  }).then(async () => {
    try {
      let response: any
      if (user.status === 'enabled') {
        response = await disableUser(user.id)
      } else {
        response = await enableUser(user.id)
      }
      if (response.code === 0) {
        ElMessage.success(`${action}成功`)
        loadUsers()
      }
    } catch (error) {
      ElMessage.error(`${action}失败`)
    }
  }).catch(() => {})
}

const resetPassword = (user: any) => {
  ElMessageBox.confirm('确定要重置该用户密码吗?', '提示', {
    type: 'warning',
  }).then(async () => {
    try {
      const response = await resetUserPassword(user.id) as any
      if (response.code === 0) {
        ElMessage.success('密码已重置为: 123456')
      }
    } catch (error) {
      ElMessage.error('重置失败')
    }
  }).catch(() => {})
}

const handleDelete = (user: any) => {
  ElMessageBox.confirm('确定要删除该用户吗?', '提示', {
    type: 'warning',
  }).then(async () => {
    try {
      const response = await deleteUser(user.id) as any
      if (response.code === 0) {
        ElMessage.success('删除成功')
        loadUsers()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.user-management {
  padding: 20px;
  background: #0d1117;
  min-height: 100%;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #f0f6fc;
}

/* Card */
.user-management :deep(.el-card) {
  background: rgba(22, 27, 34, 0.9) !important;
  border: 1px solid rgba(59, 130, 246, 0.2) !important;
}

.user-management :deep(.el-card__header) {
  background: rgba(22, 27, 34, 0.9) !important;
  border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
  color: #f0f6fc !important;
}

.user-management :deep(.el-card__body) {
  background: rgba(22, 27, 34, 0.9) !important;
  color: #e6edf3 !important;
}

/* Table */
.user-management :deep(.el-table) {
  background: transparent !important;
  color: #e6edf3 !important;
}

.user-management :deep(.el-table th) {
  background: rgba(59, 130, 246, 0.15) !important;
  color: #8b949e !important;
  border-color: rgba(59, 130, 246, 0.2) !important;
}

.user-management :deep(.el-table td) {
  background: rgba(22, 27, 34, 0.8) !important;
  border-color: rgba(59, 130, 246, 0.15) !important;
  color: #e6edf3 !important;
}

.user-management :deep(.el-table__body-wrapper tr:hover > td) {
  background: rgba(59, 130, 246, 0.1) !important;
}

/* Pagination */
.user-management :deep(.el-pagination) {
  color: #e6edf3 !important;
}

.user-management :deep(.el-pagination button) {
  background: rgba(22, 27, 34, 0.8) !important;
  color: #e6edf3 !important;
}

.user-management :deep(.el-pager li) {
  background: rgba(22, 27, 34, 0.8) !important;
  color: #e6edf3 !important;
}

.user-management :deep(.el-pager li:hover) {
  color: #58a6ff !important;
}

.user-management :deep(.el-pager li.is-active) {
  color: #58a6ff !important;
}

/* Dialog */
.user-management :deep(.el-dialog) {
  background: rgba(22, 27, 34, 0.98) !important;
}

.user-management :deep(.el-dialog__title) {
  color: #f0f6fc !important;
}

.user-management :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
}

.user-management :deep(.el-dialog__body) {
  background: rgba(22, 27, 34, 0.98) !important;
  color: #e6edf3 !important;
}

/* Form */
.user-management :deep(.el-form-item__label) {
  color: #8b949e !important;
}

.user-management :deep(.el-input__wrapper) {
  background: rgba(13, 17, 23, 0.8) !important;
  box-shadow: none !important;
  border: 1px solid rgba(59, 130, 246, 0.3) !important;
}

.user-management :deep(.el-input__inner) {
  color: #e6edf3 !important;
}

.user-management :deep(.el-input__inner::placeholder) {
  color: #6e7681 !important;
}

/* Select */
.user-management :deep(.el-select) {
  width: 100%;
}

.user-management :deep(.el-select .el-input__wrapper) {
  background: rgba(13, 17, 23, 0.8) !important;
}

.user-management :deep(.el-select-dropdown) {
  background: rgba(22, 27, 34, 0.98) !important;
  border: 1px solid rgba(59, 130, 246, 0.2) !important;
}

.user-management :deep(.el-select-dropdown__item) {
  color: #e6edf3 !important;
}

.user-management :deep(.el-select-dropdown__item:hover) {
  background: rgba(59, 130, 246, 0.1) !important;
}

.user-management :deep(.el-select-dropdown__item.selected) {
  color: #58a6ff !important;
}
</style>
