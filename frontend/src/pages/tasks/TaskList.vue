<template>
  <div class="task-list">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>任务列表</span>
          <el-button type="primary" @click="openCreateDialog">
            新建任务
          </el-button>
        </div>
      </template>

      <div class="filters">
        <el-input
          v-model="filters.name"
          placeholder="任务名称"
          style="width: 200px"
          clearable
          @keyup.enter="loadTasks"
        />
        <el-input
          v-model="filters.target"
          placeholder="目标地址"
          style="width: 200px"
          clearable
          @keyup.enter="loadTasks"
        />
        <el-select
          v-model="filters.scanMode"
          placeholder="扫描模式"
          style="width: 150px"
          clearable
        >
          <el-option label="快速扫描" value="quick" />
          <el-option label="标准扫描" value="standard" />
          <el-option label="深度扫描" value="deep" />
        </el-select>
        <el-select
          v-model="filters.status"
          placeholder="状态"
          style="width: 150px"
          clearable
        >
          <el-option label="未开始" value="not_started" />
          <el-option label="扫描中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
          <el-option label="已停止" value="stopped" />
        </el-select>
        <el-button @click="loadTasks">搜索</el-button>
      </div>

      <el-table :data="tasks" v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="name" label="任务名称" min-width="150" />
        <el-table-column prop="target" label="目标" min-width="200" show-overflow-tooltip />
        <el-table-column prop="scan_mode" label="扫描模式" width="100">
          <template #default="{ row }">
            {{ getScanModeLabel(row.scan_mode) }}
          </template>
        </el-table-column>
        <el-table-column prop="interactive" label="交互模式" width="100">
          <template #default="{ row }">
            <el-tag :type="row.interactive ? 'warning' : 'info'" size="small">
              {{ row.interactive ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="risk_level" label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag :type="getRiskType(row.risk_level)" size="small">
              {{ getRiskLabel(row.risk_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="['not_started', 'failed', 'stopped'].includes(row.status)"
              type="primary"
              size="small"
              @click="handleExecute(row)"
            >
              执行
            </el-button>
            <el-button
              v-if="row.status === 'running'"
              type="danger"
              size="small"
              @click="handleStop(row)"
            >
              停止
            </el-button>
            <el-button
              v-if="row.status === 'completed' || row.status === 'failed' || row.status === 'stopped'"
              type="success"
              size="small"
              @click="viewRunDetail(row)"
            >
              查看详情
            </el-button>
            <el-button size="small" @click="openEditDialog(row)">编辑</el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(row)"
              :disabled="row.status === 'running'"
            >
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
        @current-change="loadTasks"
        @size-change="loadTasks"
      />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="showDialog"
      :title="editingTask ? '编辑任务' : '新建任务'"
      width="600px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="目标地址" prop="target">
          <el-input v-model="form.target" placeholder="请输入目标地址 (URL/IP/域名)" />
        </el-form-item>
        <el-form-item label="扫描模式" prop="scan_mode">
          <el-select v-model="form.scan_mode" style="width: 100%">
            <el-option label="快速扫描" value="quick" />
            <el-option label="标准扫描" value="standard" />
            <el-option label="深度扫描" value="deep" />
          </el-select>
        </el-form-item>
        <el-form-item label="交互模式" prop="interactive">
          <el-switch v-model="form.interactive" />
        </el-form-item>
        <el-form-item label="扫描指令" prop="instruction">
          <el-input
            v-model="form.instruction"
            type="textarea"
            :rows="3"
            placeholder="可选，指定扫描重点"
          />
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
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import { getTasks, createTask, updateTask, deleteTask, executeTask, stopTask } from '@/api/tasks'

const router = useRouter()

const tasks = ref<any[]>([])
const loading = ref(false)
const showDialog = ref(false)
const editingTask = ref<any>(null)
const submitting = ref(false)
const formRef = ref<FormInstance>()

// Polling for running tasks
const runningTaskIds = ref<Set<string>>(new Set())
let pollTimer: ReturnType<typeof setInterval> | null = null

const filters = reactive({
  name: '',
  target: '',
  scanMode: '',
  status: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const form = reactive({
  name: '',
  target: '',
  scan_mode: 'standard',
  interactive: false,
  instruction: '',
})

const rules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  target: [{ required: true, message: '请输入目标地址', trigger: 'blur' }],
  scan_mode: [{ required: true, message: '请选择扫描模式', trigger: 'change' }],
}

const getScanModeLabel = (mode: string) => {
  const map: Record<string, string> = {
    quick: '快速',
    standard: '标准',
    deep: '深度',
  }
  return map[mode] || mode
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    not_started: 'info',
    running: 'primary',
    completed: 'success',
    failed: 'danger',
    stopped: 'warning',
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    not_started: '未开始',
    running: '扫描中',
    completed: '已完成',
    failed: '失败',
    stopped: '已停止',
  }
  return map[status] || status
}

const getRiskType = (level: string) => {
  const map: Record<string, string> = {
    unknown: 'info',
    none: 'success',
    low: 'success',
    medium: 'warning',
    high: 'danger',
  }
  return map[level] || 'info'
}

const getRiskLabel = (level: string) => {
  const map: Record<string, string> = {
    unknown: '未知',
    none: '无',
    low: '低危',
    medium: '中危',
    high: '高危',
  }
  return map[level] || level
}

const loadTasks = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      pageSize: pagination.pageSize,
    }
    if (filters.name) params.name = filters.name
    if (filters.target) params.target = filters.target
    if (filters.scanMode) params.scanMode = filters.scanMode
    if (filters.status) params.status = filters.status

    const response = await getTasks(params) as any
    if (response.code === 0) {
      tasks.value = response.data?.items || []
      pagination.total = response.data?.total || 0

      // Check for running tasks and update polling set
      const newRunningIds = new Set<string>()
      for (const task of tasks.value) {
        if (task.status === 'running') {
          newRunningIds.add(task.id)
        }
      }
      runningTaskIds.value = newRunningIds
    }
  } catch (error) {
    console.error('Failed to load tasks:', error)
  } finally {
    loading.value = false
  }
}

// Start polling if there are running tasks
const startPolling = () => {
  if (pollTimer) return // Already polling

  // Poll every 2 seconds for running tasks
  pollTimer = setInterval(async () => {
    if (runningTaskIds.value.size === 0) {
      if (pollTimer) {
        clearInterval(pollTimer)
        pollTimer = null
      }
      return
    }

    try {
      // Only fetch running tasks
      const params = {
        page: 1,
        pageSize: 100,
        status: 'running',
      }
      const response = await getTasks(params) as any
      if (response.code === 0 && response.data?.items) {
        const updatedTasks = response.data.items

        // Update tasks in the list
        for (const updated of updatedTasks) {
          const idx = tasks.value.findIndex(t => t.id === updated.id)
          if (idx !== -1) {
            tasks.value[idx] = { ...tasks.value[idx], ...updated }
          }

          // Remove from running set if no longer running
          if (updated.status !== 'running') {
            runningTaskIds.value.delete(updated.id)
          }
        }
      }
    } catch (error) {
      console.error('Polling error:', error)
    }
  }, 2000)
}

// Stop polling
const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const openCreateDialog = () => {
  editingTask.value = null
  Object.assign(form, {
    name: '',
    target: '',
    scan_mode: 'standard',
    interactive: false,
    instruction: '',
  })
  showDialog.value = true
}

const openEditDialog = (task: any) => {
  editingTask.value = task
  Object.assign(form, {
    name: task.name,
    target: task.target,
    scan_mode: task.scan_mode,
    interactive: task.interactive,
    instruction: task.instruction || '',
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
        target: form.target,
        scan_mode: form.scan_mode,
        interactive: form.interactive,
        instruction: form.instruction || undefined,
      }

      let response: any
      if (editingTask.value) {
        response = await updateTask(editingTask.value.id, data)
      } else {
        response = await createTask(data)
      }

      if (response.code === 0) {
        ElMessage.success(editingTask.value ? '更新成功' : '创建成功')
        showDialog.value = false
        loadTasks()
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

const handleExecute = async (task: any) => {
  try {
    const response = await executeTask(task.id) as any
    if (response.code === 0) {
      ElMessage.success('任务已开始执行')
      loadTasks()
      startPolling()
    } else {
      ElMessage.error(response.message || '执行失败')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.message || '执行失败')
  }
}

const viewRunDetail = (task: any) => {
  router.push(`/tasks/${task.id}/runs`)
}

const handleStop = async (task: any) => {
  ElMessageBox.confirm('确定要停止该任务吗?', '提示', {
    type: 'warning',
  }).then(async () => {
    try {
      const response = await stopTask(task.id) as any
      if (response.code === 0) {
        ElMessage.success('任务已停止')
        loadTasks()
      }
    } catch (error) {
      ElMessage.error('停止失败')
    }
  }).catch(() => {})
}

const handleDelete = (task: any) => {
  ElMessageBox.confirm('确定要删除该任务吗?', '提示', {
    type: 'warning',
  }).then(async () => {
    try {
      const response = await deleteTask(task.id) as any
      if (response.code === 0) {
        ElMessage.success('删除成功')
        loadTasks()
      }
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  loadTasks()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.task-list {
  padding: 20px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
