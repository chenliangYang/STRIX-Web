<template>
  <div class="task-runs">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>任务运行记录</span>
          <el-button @click="$router.back()">返回任务列表</el-button>
        </div>
      </template>

      <el-table :data="runs" v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="run_no" label="运行编号" width="100">
          <template #default="{ row }">
            #{{ row.run_no }}
          </template>
        </el-table-column>
        <el-table-column prop="scan_mode" label="扫描模式" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="pid" label="PID" width="100">
          <template #default="{ row }">
            {{ row.pid || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="exit_code" label="退出码" width="80">
          <template #default="{ row }">
            {{ row.exit_code ?? '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180" />
        <el-table-column prop="ended_at" label="结束时间" width="180" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewRun(row)">
              查看详情
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
        @current-change="loadRuns"
        @size-change="loadRuns"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getTaskRuns } from '@/api/runs'

const route = useRoute()
const router = useRouter()
const taskId = route.params.id as string

const runs = ref<any[]>([])
const loading = ref(false)

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    queued: 'info',
    running: 'primary',
    stopping: 'warning',
    completed: 'success',
    failed: 'danger',
    stopped: 'warning',
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    queued: '排队中',
    running: '运行中',
    stopping: '停止中',
    completed: '已完成',
    failed: '失败',
    stopped: '已停止',
  }
  return map[status] || status
}

const loadRuns = async () => {
  loading.value = true
  try {
    const response = await getTaskRuns(taskId, pagination.page, pagination.pageSize) as any
    if (response.code === 0) {
      runs.value = response.data?.items || []
      pagination.total = response.data?.total || 0
    }
  } catch (error) {
    console.error('Failed to load runs:', error)
  } finally {
    loading.value = false
  }
}

const viewRun = (run: any) => {
  router.push(`/tasks/${taskId}/runs/${run.id}`)
}

onMounted(() => {
  loadRuns()
})
</script>

<style scoped>
.task-runs {
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
.task-runs :deep(.el-card) {
  background: rgba(22, 27, 34, 0.9) !important;
  border: 1px solid rgba(59, 130, 246, 0.2) !important;
}

.task-runs :deep(.el-card__header) {
  background: rgba(22, 27, 34, 0.9) !important;
  border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
  color: #f0f6fc !important;
}

.task-runs :deep(.el-card__body) {
  background: rgba(22, 27, 34, 0.9) !important;
  color: #e6edf3 !important;
}

/* Table */
.task-runs :deep(.el-table) {
  background: transparent !important;
  color: #e6edf3 !important;
}

.task-runs :deep(.el-table th) {
  background: rgba(59, 130, 246, 0.15) !important;
  color: #8b949e !important;
  border-color: rgba(59, 130, 246, 0.2) !important;
}

.task-runs :deep(.el-table td) {
  background: rgba(22, 27, 34, 0.8) !important;
  border-color: rgba(59, 130, 246, 0.15) !important;
  color: #e6edf3 !important;
}

.task-runs :deep(.el-table__body-wrapper tr:hover > td) {
  background: rgba(59, 130, 246, 0.1) !important;
}

/* Pagination */
.task-runs :deep(.el-pagination) {
  color: #e6edf3 !important;
}

.task-runs :deep(.el-pagination button),
.task-runs :deep(.el-pager li) {
  background: rgba(22, 27, 34, 0.8) !important;
  color: #e6edf3 !important;
}

.task-runs :deep(.el-pager li:hover),
.task-runs :deep(.el-pager li.is-active) {
  color: #58a6ff !important;
}
</style>
