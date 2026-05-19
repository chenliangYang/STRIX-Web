<template>
  <div class="audit-logs">
    <el-card>
      <template #header>
        <span>审计日志</span>
      </template>

      <div class="filters">
        <el-input
          v-model="filters.actor"
          placeholder="操作者"
          style="width: 150px"
          clearable
          @keyup.enter="loadLogs"
        />
        <el-select
          v-model="filters.action"
          placeholder="操作类型"
          style="width: 150px"
          clearable
        >
          <el-option label="登录" value="login" />
          <el-option label="登出" value="logout" />
          <el-option label="创建任务" value="create_task" />
          <el-option label="执行任务" value="execute_task" />
          <el-option label="停止任务" value="stop_task" />
          <el-option label="查看结果" value="view_result" />
        </el-select>
        <el-select
          v-model="filters.result"
          placeholder="结果"
          style="width: 120px"
          clearable
        >
          <el-option label="成功" value="success" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-button @click="loadLogs">搜索</el-button>
      </div>

      <el-table :data="logs" v-loading="loading" style="margin-top: 20px">
        <el-table-column prop="created_at" label="时间" width="180" />
        <el-table-column prop="actor_account" label="操作者" width="120" />
        <el-table-column prop="actor_role" label="角色" width="80">
          <template #default="{ row }">
            {{ row.actor_role === 'admin' ? '管理员' : '用户' }}
          </template>
        </el-table-column>
        <el-table-column prop="action" label="操作" width="120">
          <template #default="{ row }">
            {{ getActionLabel(row.action) }}
          </template>
        </el-table-column>
        <el-table-column prop="object_type" label="对象类型" width="100" />
        <el-table-column prop="object_id" label="对象ID" width="200" show-overflow-tooltip />
        <el-table-column prop="result" label="结果" width="80">
          <template #default="{ row }">
            <el-tag :type="row.result === 'success' ? 'success' : 'danger'" size="small">
              {{ row.result === 'success' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="request_ip" label="IP地址" width="140" />
        <el-table-column prop="remark" label="备注" min-width="200" show-overflow-tooltip />
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        style="margin-top: 20px"
        @current-change="loadLogs"
        @size-change="loadLogs"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getAuditLogs } from '@/api/system'

const logs = ref<any[]>([])
const loading = ref(false)

const filters = reactive({
  actor: '',
  action: '',
  result: '',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

const getActionLabel = (action: string) => {
  const map: Record<string, string> = {
    login: '登录',
    logout: '登出',
    create_task: '创建任务',
    update_task: '更新任务',
    delete_task: '删除任务',
    execute_task: '执行任务',
    stop_task: '停止任务',
    view_result: '查看结果',
    download_artifact: '下载产物',
    create_whitelist: '创建白名单',
    update_whitelist: '更新白名单',
    delete_whitelist: '删除白名单',
    enable_whitelist: '启用白名单',
    disable_whitelist: '禁用白名单',
    create_user: '创建用户',
    update_user: '更新用户',
    delete_user: '删除用户',
    enable_user: '启用用户',
    disable_user: '禁用用户',
    reset_password: '重置密码',
  }
  return map[action] || action
}

const loadLogs = async () => {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      pageSize: pagination.pageSize,
    }
    if (filters.actor) params.actor = filters.actor
    if (filters.action) params.action = filters.action
    if (filters.result) params.result = filters.result

    const response = await getAuditLogs(params) as any
    if (response.code === 0) {
      logs.value = response.data?.items || []
      pagination.total = response.data?.total || 0
    }
  } catch (error) {
    console.error('Failed to load audit logs:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.audit-logs {
  padding: 20px;
}

.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}
</style>
