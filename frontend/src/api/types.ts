export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface User {
  id: string
  username: string
  account: string
  role: 'admin' | 'user'
  department?: string
  status: 'enabled' | 'disabled'
  created_at: string
  last_login_at?: string
}

export interface Task {
  id: string
  name: string
  target: string
  scan_mode: 'quick' | 'standard' | 'deep'
  interactive: boolean
  created_by: string
  creator_name?: string
  created_at: string
  status: 'not_started' | 'running' | 'completed' | 'failed' | 'stopped'
  risk_level: 'unknown' | 'none' | 'low' | 'medium' | 'high'
}

export interface TaskRun {
  id: string
  task_id: string
  run_no: number
  scan_mode: string
  interactive: boolean
  status: 'queued' | 'running' | 'stopping' | 'completed' | 'failed' | 'stopped'
  pid?: number
  runner_node_id?: string
  exit_code?: number
  run_dir: string
  started_at?: string
  ended_at?: string
  error_message?: string
  created_by: string
  created_at: string
}

export interface Result {
  id: string
  task_id: string
  run_id: string
  project_name: string
  target: string
  scan_mode: string
  interactive: boolean
  status: 'completed' | 'failed' | 'stopped' | 'parse_failed'
  risk_level: 'unknown' | 'none' | 'low' | 'medium' | 'high'
  vulnerability_count: number
  started_at?: string
  ended_at?: string
  created_at: string
}

export interface Vulnerability {
  id: string
  result_id: string
  ordinal: number
  title: string
  severity: 'unknown' | 'none' | 'low' | 'medium' | 'high'
  vuln_type?: string
  affected_target?: string
  verified: boolean
  summary?: string
  markdown_artifact_id?: string
  created_at: string
}

export interface Whitelist {
  id: string
  name: string
  target_type: 'url' | 'domain' | 'ip' | 'repo'
  target_value: string
  target_normalized: string
  project?: string
  status: 'enabled' | 'disabled'
  created_by: string
  created_at: string
}

export interface AuditLog {
  id: string
  actor_id?: string
  actor_account?: string
  actor_role?: string
  action: string
  object_type?: string
  object_id?: string
  request_ip?: string
  result: 'success' | 'failed'
  remark?: string
  created_at: string
}

export interface DashboardSummary {
  active_projects_7d: number
  total_assets_scanned: number
  high_risk_vulns_30d: number
}

export interface StatusDistribution {
  status: string
  label: string
  count: number
}

export interface RecentScan {
  task_id: string
  task_name: string
  target: string
  creator: string
  created_at: string
  scan_status: string
  risk_level: string
}
