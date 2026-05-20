<template>
  <div class="result-detail">
    <el-card>
      <template #header>
        <div class="header-actions">
          <span>结果详情</span>
          <el-button @click="$router.back()">返回</el-button>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="任务名称">
          {{ resultDetail?.task_name || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="风险等级">
          <el-tag :type="getRiskType(resultDetail?.risk_level)">
            {{ getRiskLabel(resultDetail?.risk_level) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="目标">
          {{ resultDetail?.target || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="扫描模式">
          {{ resultDetail?.scan_mode || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(resultDetail?.status)">
            {{ getStatusLabel(resultDetail?.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="漏洞数">
          {{ resultDetail?.vulnerability_count || 0 }}
        </el-descriptions-item>
        <el-descriptions-item label="开始时间">
          {{ resultDetail?.started_at || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="结束时间">
          {{ resultDetail?.ended_at || '-' }}
        </el-descriptions-item>
      </el-descriptions>

      <div v-if="resultDetail?.summary" style="margin-top: 20px">
        <h4>摘要</h4>
        <p>{{ resultDetail.summary }}</p>
      </div>
    </el-card>

    <el-card style="margin-top: 20px">
      <template #header>
        <span>漏洞列表 ({{ vulnerabilities.length }})</span>
      </template>

      <el-table :data="vulnerabilities">
        <el-table-column prop="ordinal" label="序号" width="60" />
        <el-table-column prop="title" label="漏洞标题" min-width="200" />
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <el-tag :type="getSeverityType(row.severity)" size="small">
              {{ getSeverityLabel(row.severity) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="vuln_type" label="漏洞类型" width="120" />
        <el-table-column prop="verified" label="已验证" width="80">
          <template #default="{ row }">
            <el-tag :type="row.verified ? 'success' : 'info'" size="small">
              {{ row.verified ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" @click="viewMarkdown(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="vulnerabilities.length === 0" description="未发现漏洞" />
    </el-card>

    <!-- Markdown Dialog -->
    <el-dialog v-model="showMarkdownDialog" title="漏洞详情" width="80%">
      <div v-if="currentMarkdown" class="markdown-content">
        <h2>{{ currentMarkdown.title }}</h2>
        <div v-html="renderedMarkdown"></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import markdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
import http from '@/api/http'
import type { Result, Vulnerability, VulnerabilityMarkdown } from '@/api/types'

const route = useRoute()
const resultId = route.params.id as string

const resultDetail = ref<Result | null>(null)
const vulnerabilities = ref<Vulnerability[]>([])
const showMarkdownDialog = ref(false)
const currentMarkdown = ref<VulnerabilityMarkdown | null>(null)

const md = markdownIt()

const renderedMarkdown = computed(() => {
  if (!currentMarkdown.value?.markdown) return ''
  const html = md.render(currentMarkdown.value.markdown)
  return DOMPurify.sanitize(html)
})

const getStatusType = (status?: string) => {
  const map: Record<string, string> = {
    completed: 'success',
    failed: 'danger',
    stopped: 'warning',
    parse_failed: 'danger',
  }
  return map[status || ''] || 'info'
}

const getStatusLabel = (status?: string) => {
  const map: Record<string, string> = {
    completed: '已完成',
    failed: '失败',
    stopped: '已停止',
    parse_failed: '解析失败',
  }
  return map[status || ''] || status
}

const getRiskType = (level?: string) => {
  const map: Record<string, string> = {
    unknown: 'info',
    none: 'success',
    low: 'success',
    medium: 'warning',
    high: 'danger',
  }
  return map[level || ''] || 'info'
}

const getRiskLabel = (level?: string) => {
  const map: Record<string, string> = {
    unknown: '未知',
    none: '无',
    low: '低危',
    medium: '中危',
    high: '高危',
  }
  return map[level || ''] || level
}

const getSeverityType = (severity?: string) => {
  const map: Record<string, string> = {
    unknown: 'info',
    none: 'success',
    low: 'success',
    medium: 'warning',
    high: 'danger',
  }
  return map[severity || ''] || 'info'
}

const getSeverityLabel = (severity?: string) => {
  const map: Record<string, string> = {
    unknown: '未知',
    none: '无',
    low: '低危',
    medium: '中危',
    high: '高危',
  }
  return map[severity || ''] || severity
}

const loadResultDetail = async () => {
  try {
    const response = await http.get(`/results/${resultId}`) as any
    if (response.code === 0) {
      resultDetail.value = response.data
    }
  } catch (error) {
    console.error('Failed to load result detail:', error)
  }
}

const loadVulnerabilities = async () => {
  try {
    const response = await http.get(`/results/${resultId}/vulnerabilities`) as any
    if (response.code === 0) {
      vulnerabilities.value = response.data?.items || []
    }
  } catch (error) {
    console.error('Failed to load vulnerabilities:', error)
  }
}

const viewMarkdown = async (vuln: Vulnerability) => {
  try {
    const response = await http.get(`/results/vulnerabilities/${vuln.id}/markdown`) as any
    if (response.code === 0) {
      currentMarkdown.value = {
        ...response.data,
        markdown: response.data.content  // API returns 'content', frontend expects 'markdown'
      }
      showMarkdownDialog.value = true
    } else {
      ElMessage.error('获取漏洞详情失败')
    }
  } catch (error) {
    ElMessage.error('获取漏洞详情失败')
  }
}

onMounted(() => {
  loadResultDetail()
  loadVulnerabilities()
})
</script>

<style scoped>
.result-detail {
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

/* Card 样式 */
.result-detail :deep(.el-card) {
  background: rgba(22, 27, 34, 0.9) !important;
  border: 1px solid rgba(59, 130, 246, 0.2) !important;
}

.result-detail :deep(.el-card__header) {
  background: rgba(22, 27, 34, 0.9) !important;
  border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
  color: #f0f6fc !important;
}

.result-detail :deep(.el-card__body) {
  background: rgba(22, 27, 34, 0.9) !important;
  color: #e6edf3 !important;
}

/* Descriptions 样式 */
.result-detail :deep(.el-descriptions) {
  background: transparent !important;
}

.result-detail :deep(.el-descriptions__label) {
  background: rgba(59, 130, 246, 0.1) !important;
  color: #8b949e !important;
  border-color: rgba(59, 130, 246, 0.2) !important;
}

.result-detail :deep(.el-descriptions__content) {
  background: transparent !important;
  color: #e6edf3 !important;
  border-color: rgba(59, 130, 246, 0.2) !important;
}

.result-detail :deep(.el-descriptions-item) {
  border-color: rgba(59, 130, 246, 0.2) !important;
}

.result-detail :deep(.el-descriptions-item__cell) {
  background: transparent !important;
}

/* 摘要区域 */
.result-detail :deep(.summary-section) {
  color: #e6edf3 !important;
}

.result-detail h4 {
  color: #f0f6fc !important;
}

.result-detail p {
  color: #e6edf3 !important;
}

/* Table in ResultDetail */
.result-detail :deep(.el-table) {
  background: transparent !important;
  color: #e6edf3 !important;
}

.result-detail :deep(.el-table th) {
  background: rgba(59, 130, 246, 0.15) !important;
  color: #8b949e !important;
  border-color: rgba(59, 130, 246, 0.2) !important;
}

.result-detail :deep(.el-table td) {
  background: rgba(22, 27, 34, 0.8) !important;
  border-color: rgba(59, 130, 246, 0.15) !important;
  color: #e6edf3 !important;
}

.result-detail :deep(.el-table__body-wrapper tr:hover > td) {
  background: rgba(59, 130, 246, 0.1) !important;
}

/* Dialog */
.result-detail :deep(.el-dialog) {
  background: rgba(22, 27, 34, 0.98) !important;
}

.result-detail :deep(.el-dialog__title) {
  color: #f0f6fc !important;
}

.result-detail :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(59, 130, 246, 0.2) !important;
}

.result-detail :deep(.el-dialog__body) {
  background: rgba(22, 27, 34, 0.98) !important;
  color: #e6edf3 !important;
}

/* Markdown 内容 */
.markdown-content {
  max-height: 60vh;
  overflow-y: auto;
  padding: 16px;
  background: rgba(13, 17, 23, 0.8);
  border-radius: 8px;
}

.markdown-content h2 {
  margin-bottom: 20px;
  color: #f0f6fc !important;
}
</style>
