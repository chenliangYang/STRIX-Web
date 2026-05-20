<template>
  <div class="dashboard">
    <!-- Header -->
    <div class="dashboard-header">
      <div class="header-content">
        <h1 class="dashboard-title">
          <span class="title-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </span>
          渗透测试管理平台
        </h1>
        <div class="header-time">
          <span class="time-label">数据更新于</span>
          <span class="time-value">{{ currentTime }}</span>
        </div>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card stat-card-primary">
        <div class="stat-card-bg"></div>
        <div class="stat-card-content">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-label">活跃项目</div>
            <div class="stat-value" ref="projectsRef">{{ summary.active_projects_7d }}</div>
            <div class="stat-sub">7天内有活动</div>
          </div>
          <div class="stat-trend trend-up">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              <polyline points="17 6 23 6 23 12"/>
            </svg>
          </div>
        </div>
      </div>

      <div class="stat-card stat-card-success">
        <div class="stat-card-bg"></div>
        <div class="stat-card-content">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-label">总扫描次数</div>
            <div class="stat-value">{{ summary.total_assets_scanned }}</div>
            <div class="stat-sub">已完成扫描</div>
          </div>
          <div class="stat-trend trend-up">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
              <polyline points="17 6 23 6 23 12"/>
            </svg>
          </div>
        </div>
      </div>

      <div class="stat-card stat-card-danger">
        <div class="stat-card-bg"></div>
        <div class="stat-card-content">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
              <line x1="12" y1="9" x2="12" y2="13"/>
              <line x1="12" y1="17" x2="12.01" y2="17"/>
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-label">高危漏洞</div>
            <div class="stat-value danger">{{ summary.high_risk_vulns_30d }}</div>
            <div class="stat-sub">30天内发现</div>
          </div>
          <div class="stat-trend trend-down">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 18 13.5 8.5 8.5 13.5 1 6"/>
              <polyline points="17 18 23 18 23 12"/>
            </svg>
          </div>
        </div>
      </div>

      <div class="stat-card stat-card-info">
        <div class="stat-card-bg"></div>
        <div class="stat-card-content">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
              <polyline points="22 4 12 14.01 9 11.01"/>
            </svg>
          </div>
          <div class="stat-info">
            <div class="stat-label">系统状态</div>
            <div class="stat-value success">正常</div>
            <div class="stat-sub">所有服务在线</div>
          </div>
          <div class="stat-indicator"></div>
        </div>
      </div>
    </div>

    <!-- Charts Section -->
    <div class="charts-grid">
      <!-- Status Distribution -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">
            <span class="chart-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21.21 15.89A10 10 0 1 1 8 2.83"/>
                <path d="M22 12A10 10 0 0 0 12 2v10z"/>
              </svg>
            </span>
            扫描状态分布
          </h3>
        </div>
        <div class="chart-body">
          <div class="pie-chart-container">
            <div ref="pieChartRef" class="pie-chart"></div>
            <div class="pie-center">
              <div class="pie-center-value">{{ totalScans }}</div>
              <div class="pie-center-label">总扫描</div>
            </div>
          </div>
          <div class="pie-legend">
            <div
              v-for="(item, index) in statusDistribution"
              :key="item.status"
              class="legend-item"
            >
              <span class="legend-dot" :style="{ background: chartColors[index] }"></span>
              <span class="legend-label">{{ item.label }}</span>
              <span class="legend-value">{{ item.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Scans -->
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">
            <span class="chart-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </span>
            最近扫描记录
          </h3>
          <router-link to="/tasks" class="chart-more">查看全部</router-link>
        </div>
        <div class="chart-body">
          <el-table
            :data="recentScans"
            style="width: 100%"
            :header-cell-style="{ background: 'transparent', color: '#8b949e' }"
            :row-style="{ background: 'transparent' }"
            class="dashboard-table"
          >
            <el-table-column prop="task_name" label="任务名称" min-width="120">
              <template #default="{ row }">
                <span class="task-name">{{ row.task_name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="target" label="目标" width="140">
              <template #default="{ row }">
                <span class="target-url">{{ row.target }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="scan_status" label="状态" width="90" align="center">
              <template #default="{ row }">
                <span class="status-badge" :class="'status-' + row.scan_status">
                  {{ getStatusLabel(row.scan_status) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="risk_level" label="风险" width="80" align="center">
              <template #default="{ row }">
                <span class="risk-badge" :class="'risk-' + row.risk_level">
                  {{ getRiskLabel(row.risk_level) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="creator" label="创建人" width="90" align="center" />
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { getDashboardSummary, getStatusDistribution, getRecentScans } from '@/api/dashboard'

const summary = ref({
  active_projects_7d: 0,
  total_assets_scanned: 0,
  high_risk_vulns_30d: 0,
})

const statusDistribution = ref<any[]>([])
const recentScans = ref<any[]>([])
const pieChartRef = ref<HTMLElement>()
const projectsRef = ref<HTMLElement>()
const currentTime = ref('')
let chartInstance: echarts.ECharts | null = null
let timeInterval: number | null = null

const chartColors = ['#409eff', '#67c23a', '#f56c6c', '#e6a23c', '#909399']

const totalScans = computed(() => {
  return statusDistribution.value.reduce((sum, item) => sum + item.count, 0)
})

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

const getRiskLabel = (level: string) => {
  const map: Record<string, string> = {
    unknown: '未知',
    low: '低危',
    medium: '中危',
    high: '高危',
    critical: '严重',
  }
  return map[level] || level
}

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

const initPieChart = () => {
  if (!pieChartRef.value) return

  if (chartInstance) {
    chartInstance.dispose()
  }

  chartInstance = echarts.init(pieChartRef.value)

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(30, 35, 45, 0.95)',
      borderColor: '#3b82f6',
      textStyle: {
        color: '#e6edf3',
      },
      formatter: '{b}: {c} ({d}%)',
    },
    color: chartColors,
    series: [
      {
        type: 'pie',
        radius: ['55%', '80%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#1a1f2e',
          borderWidth: 3,
        },
        label: {
          show: false,
        },
        emphasis: {
          scale: true,
          scaleSize: 10,
          itemStyle: {
            shadowBlur: 20,
            shadowColor: 'rgba(64, 158, 255, 0.5)',
          },
        },
        animationType: 'scale',
        animationEasing: 'elasticOut',
        data: statusDistribution.value.map((item, index) => ({
          name: item.label,
          value: item.count,
          itemStyle: {
            color: chartColors[index % chartColors.length],
          },
        })),
      },
    ],
  }

  chartInstance.setOption(option)
}

const fetchDashboardData = async () => {
  try {
    const [summaryRes, distRes, recentRes] = await Promise.all([
      getDashboardSummary() as any,
      getStatusDistribution() as any,
      getRecentScans(10) as any,
    ])

    if (summaryRes.code === 0) {
      summary.value = summaryRes.data
    }
    if (distRes.code === 0) {
      statusDistribution.value = distRes.data || []
      setTimeout(() => initPieChart(), 100)
    }
    if (recentRes.code === 0) {
      recentScans.value = recentRes.data?.items || []
    }
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
}

onMounted(() => {
  updateTime()
  timeInterval = window.setInterval(updateTime, 1000)
  fetchDashboardData()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.dashboard {
  padding: 24px;
  background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #1a1f2e 100%);
  min-height: 100vh;
  color: #e6edf3;
}

/* Header */
.dashboard-header {
  margin-bottom: 32px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 28px;
  font-weight: 600;
  color: #f0f6fc;
  margin: 0;
}

.title-icon {
  display: flex;
  width: 40px;
  height: 40px;
  color: #3b82f6;
}

.title-icon svg {
  width: 100%;
  height: 100%;
}

.header-time {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.time-label {
  font-size: 12px;
  color: #8b949e;
}

.time-value {
  font-size: 14px;
  color: #58a6ff;
  font-family: 'JetBrains Mono', monospace;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  position: relative;
  background: rgba(22, 27, 34, 0.8);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 8px 32px rgba(59, 130, 246, 0.2);
}

.stat-card-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 100px;
  background: linear-gradient(180deg, rgba(59, 130, 246, 0.1) 0%, transparent 100%);
  pointer-events: none;
}

.stat-card-content {
  position: relative;
  display: flex;
  align-items: center;
  padding: 20px;
  gap: 16px;
}

.stat-card-primary .stat-card-bg {
  background: linear-gradient(180deg, rgba(59, 130, 246, 0.15) 0%, transparent 100%);
}

.stat-card-success .stat-card-bg {
  background: linear-gradient(180deg, rgba(103, 194, 58, 0.15) 0%, transparent 100%);
}

.stat-card-danger .stat-card-bg {
  background: linear-gradient(180deg, rgba(245, 108, 108, 0.15) 0%, transparent 100%);
}

.stat-card-info .stat-card-bg {
  background: linear-gradient(180deg, rgba(144, 147, 153, 0.15) 0%, transparent 100%);
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.15);
}

.stat-card-primary .stat-icon {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.stat-card-success .stat-icon {
  background: rgba(103, 194, 58, 0.15);
  color: #67c23a;
}

.stat-card-danger .stat-icon {
  background: rgba(245, 108, 108, 0.15);
  color: #f56c6c;
}

.stat-card-info .stat-icon {
  background: rgba(144, 147, 153, 0.15);
  color: #909399;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 13px;
  color: #8b949e;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #f0f6fc;
  line-height: 1.2;
}

.stat-value.danger {
  color: #f56c6c;
}

.stat-value.success {
  font-size: 20px;
  color: #67c23a;
}

.stat-sub {
  font-size: 12px;
  color: #6e7681;
  margin-top: 4px;
}

.stat-trend {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.stat-trend svg {
  width: 20px;
  height: 20px;
}

.trend-up {
  background: rgba(103, 194, 58, 0.15);
  color: #67c23a;
}

.trend-down {
  background: rgba(245, 108, 108, 0.15);
  color: #f56c6c;
}

.stat-indicator {
  width: 10px;
  height: 10px;
  background: #67c23a;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(103, 194, 58, 0.7); }
  70% { box-shadow: 0 0 0 10px rgba(103, 194, 58, 0); }
  100% { box-shadow: 0 0 0 0 rgba(103, 194, 58, 0); }
}

/* Charts Grid */
.charts-grid {
  display: grid;
  grid-template-columns: 1fr 1.5fr;
  gap: 20px;
  margin-bottom: 24px;
}

.chart-card {
  background: rgba(22, 27, 34, 0.8);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 16px;
  overflow: hidden;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(59, 130, 246, 0.1);
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #f0f6fc;
  margin: 0;
}

.chart-icon {
  display: flex;
  width: 20px;
  height: 20px;
  color: #3b82f6;
}

.chart-icon svg {
  width: 100%;
  height: 100%;
}

.chart-more {
  font-size: 13px;
  color: #58a6ff;
  text-decoration: none;
  transition: color 0.2s;
}

.chart-more:hover {
  color: #79bbff;
}

.chart-body {
  padding: 20px;
}

/* Pie Chart */
.pie-chart-container {
  position: relative;
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.pie-chart {
  width: 200px;
  height: 200px;
}

.pie-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  background: rgba(22, 27, 34, 0.95);
  width: 90px;
  height: 90px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border: 2px solid rgba(59, 130, 246, 0.3);
}

.pie-center-value {
  font-size: 24px;
  font-weight: 700;
  color: #f0f6fc;
}

.pie-center-label {
  font-size: 12px;
  color: #8b949e;
}

.pie-legend {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-label {
  flex: 1;
  font-size: 13px;
  color: #8b949e;
}

.legend-value {
  font-size: 14px;
  font-weight: 600;
  color: #f0f6fc;
}

/* Dashboard Table */
.dashboard-table {
  background: transparent !important;
}

.dashboard-table :deep(.el-table) {
  background: transparent;
  color: #e6edf3;
}

.dashboard-table :deep(.el-table tr) {
  background: transparent;
}

.dashboard-table :deep(.el-table th) {
  background: rgba(59, 130, 246, 0.1);
  color: #8b949e;
  font-weight: 600;
  border: none;
}

.dashboard-table :deep(.el-table td) {
  background: transparent;
  border-bottom: 1px solid rgba(59, 130, 246, 0.1);
}

.dashboard-table :deep(.el-table tbody tr:hover td) {
  background: rgba(59, 130, 246, 0.1);
}

.task-name {
  font-weight: 500;
  color: #f0f6fc;
}

.target-url {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: #8b949e;
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-not_started {
  background: rgba(144, 147, 153, 0.2);
  color: #909399;
}

.status-running {
  background: rgba(64, 158, 255, 0.2);
  color: #409eff;
}

.status-completed {
  background: rgba(103, 194, 58, 0.2);
  color: #67c23a;
}

.status-failed {
  background: rgba(245, 108, 108, 0.2);
  color: #f56c6c;
}

.status-stopped {
  background: rgba(230, 162, 60, 0.2);
  color: #e6a23c;
}

.risk-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.risk-unknown {
  background: rgba(144, 147, 153, 0.2);
  color: #909399;
}

.risk-low {
  background: rgba(103, 194, 58, 0.2);
  color: #67c23a;
}

.risk-medium {
  background: rgba(230, 162, 60, 0.2);
  color: #e6a23c;
}

.risk-high {
  background: rgba(245, 108, 108, 0.2);
  color: #f56c6c;
}

.risk-critical {
  background: rgba(255, 0, 0, 0.2);
  color: #ff0000;
}

/* Responsive */
@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>
