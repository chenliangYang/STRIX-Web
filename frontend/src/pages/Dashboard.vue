<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>活跃项目 (7天内)</span>
          </template>
          <div class="stat-value">{{ summary.active_projects_7d }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>总资产扫描数</span>
          </template>
          <div class="stat-value">{{ summary.total_assets_scanned }}</div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <span>高危漏洞 (30天内)</span>
          </template>
          <div class="stat-value warning">{{ summary.high_risk_vulns_30d }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>项目状态分布</span>
          </template>
          <div ref="pieChartRef" style="height: 300px"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>最近扫描记录</span>
          </template>
          <el-table :data="recentScans" style="width: 100%">
            <el-table-column prop="task_name" label="任务名称" />
            <el-table-column prop="target" label="目标" width="150" show-overflow-tooltip />
            <el-table-column prop="scan_status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.scan_status)">
                  {{ getStatusLabel(row.scan_status) }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import * as echarts from 'echarts'
import { getDashboardSummary, getStatusDistribution, getRecentScans } from '@/api/dashboard'

const summary = reactive({
  active_projects_7d: 0,
  total_assets_scanned: 0,
  high_risk_vulns_30d: 0,
})

const statusDistribution = ref<any[]>([])
const recentScans = ref<any[]>([])
const pieChartRef = ref<HTMLElement>()

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

const initPieChart = () => {
  if (!pieChartRef.value) return

  const chart = echarts.init(pieChartRef.value)
  const option = {
    tooltip: {
      trigger: 'item',
    },
    legend: {
      bottom: '5%',
      left: 'center',
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
          },
        },
        data: statusDistribution.value.map((item) => ({
          name: item.label,
          value: item.count,
        })),
      },
    ],
  }
  chart.setOption(option)
}

const fetchDashboardData = async () => {
  try {
    const [summaryRes, distRes, recentRes] = await Promise.all([
      getDashboardSummary() as any,
      getStatusDistribution() as any,
      getRecentScans(10) as any,
    ])

    if (summaryRes.code === 0) {
      Object.assign(summary, summaryRes.data)
    }
    if (distRes.code === 0) {
      statusDistribution.value = distRes.data || []
      initPieChart()
    }
    if (recentRes.code === 0) {
      recentScans.value = recentRes.data?.items || []
    }
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<style scoped>
.dashboard {
  padding: 20px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  text-align: center;
  padding: 20px 0;
  color: #409eff;
}

.stat-value.warning {
  color: #f56c6c;
}
</style>
