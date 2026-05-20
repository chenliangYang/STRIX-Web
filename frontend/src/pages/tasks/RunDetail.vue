<template>
  <div class="run-detail">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>运行详情 - #{{ runDetail?.run_no || '' }}</span>
          <div>
            <el-tag v-if="runDetail?.status" :type="getStatusType(runDetail.status)">
              {{ getStatusLabel(runDetail.status) }}
            </el-tag>
            <el-button @click="$router.back()" style="margin-left: 10px">返回</el-button>
          </div>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="运行编号">#{{ runDetail?.run_no }}</el-descriptions-item>
        <el-descriptions-item label="扫描模式">{{ runDetail?.scan_mode }}</el-descriptions-item>
        <el-descriptions-item label="PID">{{ runDetail?.pid || '-' }}</el-descriptions-item>
        <el-descriptions-item label="退出码">{{ runDetail?.exit_code ?? '-' }}</el-descriptions-item>
        <el-descriptions-item label="开始时间">{{ runDetail?.started_at || '-' }}</el-descriptions-item>
        <el-descriptions-item label="结束时间">{{ runDetail?.ended_at || '-' }}</el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <div class="events-header">
          <span>实时事件</span>
          <el-tag v-if="wsConnected" type="success" size="small">WebSocket 已连接</el-tag>
          <el-tag v-else type="info" size="small">WebSocket 未连接</el-tag>
        </div>
      </template>
      <div class="events-container" ref="eventsContainer">
        <div
          v-for="event in events"
          :key="event.seq"
          class="event-item"
          :class="'event-' + event.event_type"
        >
          <div class="event-header">
            <span class="event-time">{{ formatTime(event._timestamp || event.event_time) }}</span>
            <span class="event-type" :class="'type-' + event.event_type">
              {{ getEventTypeLabel(event.event_type) }}
            </span>
          </div>
          <pre class="event-payload">{{ JSON.stringify(event.payload_json || event.data, null, 2) }}</pre>
        </div>
        <el-empty v-if="events.length === 0 && !isRunning" description="暂无事件" />
        <div v-if="events.length === 0 && isRunning" class="waiting-events">
          <el-icon class="is-loading"><Loading /></el-icon>
          等待接收事件...
        </div>
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
            <el-button size="small" @click="downloadArtifact(row)">下载</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="artifacts.length === 0" description="暂无产物" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'
import http from '@/api/http'
import type { TaskRun, RunEvent, ArtifactItem } from '@/api/types'

const route = useRoute()
const taskId = route.params.id as string
const runId = route.params.runId as string

const runDetail = ref<any>(null)
const events = ref<any[]>([])
const artifacts = ref<ArtifactItem[]>([])
const eventsContainer = ref<HTMLElement>()
const wsConnected = ref(false)
let ws: WebSocket | null = null
let pollInterval: ReturnType<typeof setInterval> | null = null
let lastSeq = 0

const isRunning = computed(() => {
  return runDetail.value?.status === 'running' || runDetail.value?.status === 'queued'
})

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

const getEventTypeLabel = (type: string) => {
  const map: Record<string, string> = {
    scan_start: '扫描开始',
    port_scan: '端口扫描',
    scan_phase: '扫描阶段',
    vulnerability_found: '发现漏洞',
    scan_progress: '扫描进度',
    scan_complete: '扫描完成',
    scan_error: '扫描错误',
    status_change: '状态变更',
    strix_event: 'STRIX事件',
  }
  return map[type] || type
}

const formatTime = (time: string) => {
  if (!time) return ''
  try {
    return new Date(time).toLocaleTimeString('zh-CN')
  } catch {
    return time
  }
}

const formatSize = (bytes?: number) => {
  if (!bytes) return '-'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

const scrollToBottom = () => {
  nextTick(() => {
    if (eventsContainer.value) {
      eventsContainer.value.scrollTop = eventsContainer.value.scrollHeight
    }
  })
}

const connectWebSocket = () => {
  const token = localStorage.getItem('token')
  if (!token || !runId) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/runs/${runId}/events?token=${token}`

  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    wsConnected.value = true
    console.log('WebSocket connected')
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'strix_event' && data.data) {
        const seq = data.seq || (lastSeq + 1)
        events.value.push({
          seq: seq,
          event_type: data.data.type || 'unknown',
          _timestamp: data.timestamp,
          payload_json: data.data,
        })
        lastSeq = Math.max(lastSeq, seq)
        scrollToBottom()
      } else if (data.type === 'status_change') {
        if (runDetail.value) {
          runDetail.value.status = data.data?.status || runDetail.value.status
        }
        loadRunDetail()
      }
    } catch (e) {
      console.error('Failed to parse WebSocket message:', e)
    }
  }

  ws.onclose = () => {
    wsConnected.value = false
    console.log('WebSocket disconnected')
    if (isRunning.value) {
      setTimeout(connectWebSocket, 3000)
    }
  }

  ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    wsConnected.value = false
  }
}

const pollEvents = async () => {
  if (!runId) return
  try {
    const response = await http.get(`/runs/${runId}/events?seq_after=${lastSeq}`) as any
    if (response.code === 0 && response.data) {
      const newEvents = Array.isArray(response.data) ? response.data : response.data.items || []
      for (const event of newEvents) {
        if (event.seq > lastSeq) {
          events.value.push(event)
          lastSeq = Math.max(lastSeq, event.seq)
        }
      }
      if (newEvents.length > 0) {
        scrollToBottom()
      }
    }
  } catch (error) {
    console.error('Failed to poll events:', error)
  }
}

const loadRunDetail = async () => {
  try {
    const response = await http.get(`/runs/${runId}`) as any
    if (response.code === 0) {
      runDetail.value = response.data

      if (runDetail.value?.status !== 'running' && runDetail.value?.status !== 'queued') {
        stopPolling()
      }
    }
  } catch (error) {
    console.error('Failed to load run detail:', error)
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

const startPolling = () => {
  pollInterval = setInterval(pollEvents, 2000)
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

onMounted(async () => {
  await loadRunDetail()

  if (isRunning.value) {
    connectWebSocket()
    startPolling()
  }

  loadArtifacts()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
    ws = null
  }
  stopPolling()
})
</script>

<style scoped>
.run-detail {
  padding: 20px;
  background: #0d1117;
  min-height: 100%;
}

.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.events-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #f0f6fc;
}

.events-container {
  max-height: 500px;
  overflow-y: auto;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: rgba(13, 17, 23, 0.8);
  border-radius: 8px;
  padding: 8px;
}

.event-item {
  padding: 12px;
  border-bottom: 1px solid rgba(59, 130, 246, 0.15);
  border-left: 3px solid transparent;
}

.event-item.event-scan_start {
  border-left-color: #58a6ff;
}

.event-item.event-vulnerability_found {
  border-left-color: #f85149;
}

.event-item.event-scan_complete {
  border-left-color: #3fb950;
}

.event-item.event-scan_error {
  border-left-color: #d29922;
}

.event-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.event-time {
  color: #8b949e;
  font-size: 12px;
}

.event-type {
  font-weight: bold;
  font-size: 13px;
  color: #e6edf3;
}

.type-scan_start { color: #58a6ff; }
.type-port_scan { color: #8b949e; }
.type-vulnerability_found { color: #f85149; }
.type-scan_progress { color: #d29922; }
.type-scan_complete { color: #3fb950; }
.type-scan_error { color: #f85149; }

.event-payload {
  margin: 0;
  padding: 10px;
  background: rgba(22, 27, 34, 0.8);
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  color: #e6edf3;
}

.waiting-events {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: #8b949e;
}

/* Card */
.run-detail :deep(.el-card) {
  background: rgba(22, 27, 34, 0.9) !important;
  border: 1px solid rgba(59, 130, 246, 0.2) !important;
}

.run-detail :deep(.el-card__header) {
  background: rgba(22, 27, 34, 0.9) !important;
  border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
  color: #f0f6fc !important;
}

.run-detail :deep(.el-card__body) {
  background: rgba(22, 27, 34, 0.9) !important;
  color: #e6edf3 !important;
}

/* Descriptions */
.run-detail :deep(.el-descriptions__label),
.run-detail :deep(.el-descriptions__content),
.run-detail :deep(.el-descriptions-item__cell) {
  background: rgba(22, 27, 34, 0.6) !important;
  color: #e6edf3 !important;
  border-color: rgba(59, 130, 246, 0.2) !important;
}

/* Table */
.run-detail :deep(.el-table) {
  background: transparent !important;
  color: #e6edf3 !important;
}

.run-detail :deep(.el-table th) {
  background: rgba(59, 130, 246, 0.15) !important;
  color: #8b949e !important;
  border-color: rgba(59, 130, 246, 0.2) !important;
}

.run-detail :deep(.el-table td) {
  background: rgba(22, 27, 34, 0.8) !important;
  border-color: rgba(59, 130, 246, 0.15) !important;
  color: #e6edf3 !important;
}

.run-detail :deep(.el-table__body-wrapper tr:hover > td) {
  background: rgba(59, 130, 246, 0.1) !important;
}
</style>
