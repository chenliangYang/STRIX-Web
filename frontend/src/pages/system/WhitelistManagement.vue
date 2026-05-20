<template>
  <div class="whitelist-management">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>白名单管理</span>
          <el-button type="primary" @click="openCreateDialog">
            新建白名单
          </el-button>
        </div>
      </template>

      <div class="filters">
        <el-input
          v-model="filters.name"
          placeholder="名称"
          style="width: 150px"
          clearable
          @keyup.enter="loadWhitelists"
        />
        <el-select
          v-model="filters.targetType"
          placeholder="目标类型"
          style="width: 150px"
          clearable
        >
          <el-option label="URL" value="url" />
          <el-option label="域名" value="domain" />
          <el-option label="IP" value="ip" />
          <el-option label="仓库" value="repo" />
        </el-select>
        <el-select
          v-model="filters.status"
          placeholder="状态"
          style="width: 120px"
          clearable
        >
          <el-option label="启用" value="enabled" />
          <el-option label="禁用" value="disabled" />
        </el-select>
        <el-button @click="loadWhitelists">搜索</el-button>
      </div>

      <el-table :data="whitelists" v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="target_type" label="类型" width="100">
          <template #default="{ row }">
            {{ getTypeLabel(row.target_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="target_value" label="目标值" min-width="200" show-overflow-tooltip />
        <el-table-column prop="project" label="项目" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'enabled' ? 'success' : 'info'">
              {{ row.status === 'enabled' ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button
              size="small"
              :type="row.status === 'enabled' ? 'warning' : 'success'"
              @click="toggleStatus(row)"
            >
              {{ row.status === 'enabled' ? '禁用' : '启用' }}
            </el-button>
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
        @current-change="loadWhitelists"
        @size-change="loadWhitelists"
      />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="showDialog"
      :title="editingWhitelist ? '编辑白名单' : '新建白名单'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="目标类型" prop="target_type">
          <el-select v-model="form.target_type" style="width: 100%">
            <el-option label="URL" value="url" />
            <el-option label="域名" value="domain" />
            <el-option label="IP" value="ip" />
            <el-option label="仓库" value="repo" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标值" prop="target_value">
          <el-input v-model="form.target_value" placeholder="请输入目标值" />
        </el-form-item>
        <el-form-item label="项目" prop="project">
          <el-input v-model="form.project" placeholder="可选" />
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
  getWhitelists,
  createWhitelist,
  updateWhitelist,
  deleteWhitelist,
  enableWhitelist,
  disableWhitelist,
} from '@/api/system'

const whitelists = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editingWhitelist = ref<any>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

const filters = reactive({
  name: '',
  targetType: '',
  status: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const form = reactive({
  name: '',
  target_type: 'url',
  target_value: '',
  project: '',
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  target_type: [{ required: true, message: '请选择目标类型', trigger: 'change' }],
  target_value: [{ required: true, message: '请输入目标值', trigger: 'blur' }],
}

const getTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    url: 'URL',
    domain: '域名',
    ip: 'IP',
    repo: '仓库',
  }
  return map[type] || type
}

const loadWhitelists = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      pageSize: pagination.pageSize,
    }
    if (filters.name) params.name = filters.name
    if (filters.targetType) params.targetType = filters.targetType
    if (filters.status) params.status = filters.status

    const response = await getWhitelists(params) as any
    if (response.code === 0) {
      whitelists.value = response.data?.items || []
      pagination.total = response.data?.total || 0
    }
  } catch (error) {
    console.error('Failed to load whitelists:', error)
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  editingWhitelist.value = null
  Object.assign(form, {
    name: '',
    target_type: 'url',
    target_value: '',
    project: '',
  })
  showDialog.value = true
}

const openEditDialog = (whitelist: any) => {
  editingWhitelist.value = whitelist
  Object.assign(form, {
    name: whitelist.name,
    target_type: whitelist.target_type,
    target_value: whitelist.target_value,
    project: whitelist.project || '',
  })
  showDialog.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      const data = {
        name: form.name,
        target_type: form.target_type,
        target_value: form.target_value,
        project: form.project || undefined,
      }

      let response: any
      if (editingWhitelist.value) {
        response = await updateWhitelist(editingWhitelist.value.id, data)
      } else {
        response = await createWhitelist(data)
      }

      if (response.code === 0) {
        ElMessage.success(editingWhitelist.value ? '更新成功' : '创建成功')
        showDialog.value = false
        loadWhitelists()
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

const toggleStatus = (whitelist: any) => {
  const action = whitelist.status === 'enabled' ? '禁用' : '启用'
  ElMessageBox.confirm(`确定要${action}该白名单吗?`, '提示', {
    type: 'warning',
  }).then(async () => {
    try {
      let response: any
      if (whitelist.status === 'enabled') {
        response = await disableWhitelist(whitelist.id)
      } else {
        response = await enableWhitelist(whitelist.id)
      }
      if (response.code === 0) {
        ElMessage.success(`${action}成功`)
        loadWhitelists()
      }
    } catch (error) {
      ElMessage.error(`${action}失败`)
    }
  }).catch(() => {})
}

const handleDelete = (whitelist: any) => {
  ElMessageBox.confirm('确定要删除该白名单吗?', '提示', {
    type: 'warning',
  }).then(async () => {
    try {
      const response = await deleteWhitelist(whitelist.id) as any
      if (response.code === 0) {
        ElMessage.success('删除成功')
        loadWhitelists()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  loadWhitelists()
})
</script>

<style scoped>
.whitelist-management {
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

.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* Card */
.whitelist-management :deep(.el-card) {
  background: rgba(22, 27, 34, 0.9) !important;
  border: 1px solid rgba(59, 130, 246, 0.2) !important;
}

.whitelist-management :deep(.el-card__header) {
  background: rgba(22, 27, 34, 0.9) !important;
  border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
  color: #f0f6fc !important;
}

.whitelist-management :deep(.el-card__body) {
  background: rgba(22, 27, 34, 0.9) !important;
  color: #e6edf3 !important;
}

/* Table */
.whitelist-management :deep(.el-table) {
  background: transparent !important;
  color: #e6edf3 !important;
}

.whitelist-management :deep(.el-table th) {
  background: rgba(59, 130, 246, 0.15) !important;
  color: #8b949e !important;
  border-color: rgba(59, 130, 246, 0.2) !important;
}

.whitelist-management :deep(.el-table td) {
  background: rgba(22, 27, 34, 0.8) !important;
  border-color: rgba(59, 130, 246, 0.15) !important;
  color: #e6edf3 !important;
}

.whitelist-management :deep(.el-table__body-wrapper tr:hover > td) {
  background: rgba(59, 130, 246, 0.1) !important;
}

/* Pagination */
.whitelist-management :deep(.el-pagination) {
  color: #e6edf3 !important;
}

.whitelist-management :deep(.el-pagination button),
.whitelist-management :deep(.el-pager li) {
  background: rgba(22, 27, 34, 0.8) !important;
  color: #e6edf3 !important;
}

.whitelist-management :deep(.el-pager li:hover),
.whitelist-management :deep(.el-pager li.is-active) {
  color: #58a6ff !important;
}

/* Dialog */
.whitelist-management :deep(.el-dialog) {
  background: rgba(22, 27, 34, 0.98) !important;
}

.whitelist-management :deep(.el-dialog__title) {
  color: #f0f6fc !important;
}

.whitelist-management :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
}

.whitelist-management :deep(.el-dialog__body) {
  background: rgba(22, 27, 34, 0.98) !important;
  color: #e6edf3 !important;
}

/* Form */
.whitelist-management :deep(.el-form-item__label) {
  color: #8b949e !important;
}

.whitelist-management :deep(.el-input__wrapper) {
  background: rgba(13, 17, 23, 0.8) !important;
  box-shadow: none !important;
  border: 1px solid rgba(59, 130, 246, 0.3) !important;
}

.whitelist-management :deep(.el-input__inner) {
  color: #e6edf3 !important;
}

/* Select */
.whitelist-management :deep(.el-select .el-input__wrapper) {
  background: rgba(13, 17, 23, 0.8) !important;
}

.whitelist-management :deep(.el-select-dropdown) {
  background: rgba(22, 27, 34, 0.98) !important;
  border: 1px solid rgba(59, 130, 246, 0.2) !important;
}

.whitelist-management :deep(.el-select-dropdown__item) {
  color: #e6edf3 !important;
}

.whitelist-management :deep(.el-select-dropdown__item:hover) {
  background: rgba(59, 130, 246, 0.1) !important;
}
</style>
