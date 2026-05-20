import http from './http'

export interface RunDetail {
  id: string
  task_id: string
  run_no: number
  scan_mode: string
  interactive: boolean
  status: string
  pid?: number
  exit_code?: number
  run_dir: string
  strix_run_dir?: string
  started_at?: string
  ended_at?: string
  error_message?: string
  created_by: string
  created_at: string
  updated_at?: string
}

export interface RunEvent {
  id: string
  run_id: string
  seq: number
  event_type: string
  event_time?: string
  payload_json: Record<string, any>
  source_file?: string
  source_offset?: number
  created_at: string
}

export const getRun = (runId: string) => {
  return http.get(`/runs/${runId}`)
}

export const getRunEvents = (runId: string, seqAfter: number = 0, limit: number = 100) => {
  return http.get(`/runs/${runId}/events`, {
    params: { seq_after: seqAfter, limit }
  })
}

export const stopRun = (runId: string) => {
  return http.post(`/runs/${runId}/stop`, {})
}

export const getTaskRuns = (taskId: string, page: number = 1, pageSize: number = 20) => {
  return http.get(`/tasks/${taskId}/runs`, {
    params: { page, pageSize }
  })
}
