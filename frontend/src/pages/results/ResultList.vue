<template>
  <div class="result-list">
    <el-card>
      <template #header>
        <span>结果列表</span>
      </template>

      <div class="filters">
        <el-input
          v-model="filters.taskName"
          placeholder="任务名称"
          style="width: 200px"
          clearable
        />
        <el-select
          v-model="filters.status"
          placeholder="状态"
          style="width: 150px"
          clearable
        >
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
          <el-option label="停止" value="stopped" />
        </el-select>
        <el-select
          v-model="filters.riskLevel"
          placeholder="风险等级"
          style="width: 150px"
          clearable
        >
          <el-option label="无风险" value="none" />
          <el-option label="低危" value="low" />
          <el-option label="中危" value="medium" />
          <el-option label="高危" value="high" />
        </el-select>
        <el-button @click="loadResults">搜索</el-button>
      </div>

      <el-table :data="results" v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="task_name" label="任务名称" min-width="150" />
        <el-table-column prop="target" label="目标" min-width="200" show-overflow-tooltip />
        <el-table-column prop="scan_mode" label="扫描模式" width="100" />
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
        <el-table-column prop="vulnerability_count" label="漏洞数" width="80">
          <template #default="{ row }">
            <span :class="{ danger: row.vulnerability_count > 0 }">
              {{ row.vulnerability_count }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="started_at" label="开始时间" width="180" />
        <el-table-column prop="ended_at" label="结束时间" width="180" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">
              详情
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
        @current-change="loadResults"
        @size-change="loadResults"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import http from '@/api/http'
import type { Result } from '@/api/types'

const router = useRouter()

const results = ref<Result[]>([])
const loading = ref(false)

const filters = reactive({
  taskName: '',
  status: '',
  riskLevel: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    completed: 'success',
    failed: 'danger',
    stopped: 'warning',
    parse_failed: 'danger',
  }
  return map[status] || 'info'
}

const getStatusLabel = (status: string) => {
  const map: Record<string, string> = {
    completed: '已完成',
    failed: '失败',
    stopped: '已停止',
    parse_failed: '解析失败',
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

const loadResults = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      pageSize: pagination.pageSize,
      ...filters,
    }
    const response = await http.get('/results', { params }) as any
    if (response.code === 0) {
      results.value = response.data?.items || []
      pagination.total = response.data?.total || 0
    }
  } catch (error) {
    console.error('Failed to load results:', error)
  } finally {
    loading.value = false
  }
}

const viewDetail = (row: Result) => {
  router.push(`/results/${row.id}`)
}

onMounted(() => {
  loadResults()
})
</script>

<style scoped>
.result-list {
  padding: 20px;
}

.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.danger {
  color: #f56c6c;
  font-weight: bold;
}
</style>
