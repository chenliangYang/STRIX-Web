<template>
  <div class="run-detail">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>运行详情</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务名称">
          {{ runDetail?.task_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="运行状态">
          <el-tag :type="getStatusType(runDetail?.status)">
            {{ getStatusLabel(runDetail?.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="运行编号">#{{ runDetail?.run_no }}</el-descriptions-item>
        <el-descriptions-item label="扫描模式">
          {{ runDetail?.scan_mode }}
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ runDetail?.started_at || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="结束时间">
          {{ runDetail?.ended_at || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>实时事件</span>
      </template>
      <div class="events-container">
        <div
          v-for="event in events"
          :key="event.id"
          class="event-item"
        >
          <span class="event-time">{{ event.event_time }}</span>
          <span class="event-type">{{ event.event_type }}</span>
          <pre class="event-payload">{{ JSON.stringify(event.payload_json, null, 2) }}</pre>
        </div>
        <el-empty v-if="events.length === 0" description="暂无事件" />
      </div>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>产物列表</span>
      </template>
      <el-table :data="artifacts">
        <el-table-column prop="file_name" label="文件名" />
        <el-table-column prop="artifact_type" label="类型" width="120" />
        <el-table-column prop="size_bytes" label="大小" width="120">
          <template #default="{ row }">
            {{ formatSize(row.size_bytes) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="downloadArtifact(row)">
              下载
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="artifacts.length === 0" description="暂无产物" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import http from '@/api/http'
import type { TaskRun, RunEvent, ArtifactItem } from '@/api/types'

const route = useRoute()
const taskId = route.params.id as string
const runId = route.params.runId as string

const runDetail = ref<any>(null)
const events = ref<RunEvent[]>([])
const artifacts = ref<ArtifactItem[]>([])

const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    queued: 'info',
    running: 'primary',
    stopping: 'warning',
    completed: 'success',
    failed: 'danger',
    stopped: 'warning',
  }
  return map[status || ''] || 'info'
}

const getStatusLabel = (status?: string) => {
  const map: Record<string, string> = {
    queued: '排队中',
    running: '运行中',
    stopping: '停止中',
    completed: '已完成',
    failed: '失败',
    stopped: '已停止',
  }
  return map[status || ''] || status
}

const formatSize = (bytes?: number) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const loadRunDetail = async () => {
  try {
    const response = await http.get(`/runs/${runId}`) as any
    if (response.code === 0) {
      runDetail.value = response.data
    }
  } catch (error) {
    console.error('Failed to load run detail:', error)
  }
}

const loadEvents = async () => {
  try {
    const response = await http.get(`/runs/${runId}/events`) as any
    if (response.code === 0) {
      events.value = response.data?.items || []
    }
  } catch (error) {
    console.error('Failed to load events:', error)
  }
}

const loadArtifacts = async () => {
  try {
    const response = await http.get(`/runs/${runId}/artifacts`) as any
    if (response.code === 0) {
      artifacts.value = response.data || []
    }
  } catch (error) {
    console.error('Failed to load artifacts:', error)
  }
}

const downloadArtifact = (artifact: ArtifactItem) => {
  window.open(`/api/artifacts/${artifact.id}/download`, '_blank')
}

onMounted(() => {
  loadRunDetail()
  loadEvents()
  loadArtifacts()
})
</script>

<style scoped>
.run-detail {
  padding: 20px;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.events-container {
  max-height: 400px;
  overflow-y: auto;
}

.event-item {
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.event-time {
  color: #999;
  margin-right: 10px;
}

.event-type {
  font-weight: bold;
  margin-right: 10px;
}

.event-payload {
  margin-top: 5px;
  padding: 10px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}
</style>
