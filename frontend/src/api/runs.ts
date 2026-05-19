import http from './http'

export interface RunListParams {
  page?: number
  pageSize?: number
  taskId?: string
}

export const getRuns = (taskId: string, params?: RunListParams) => {
  return http.get(`/tasks/${taskId}/runs`, { params })
}

export const getRun = (runId: string) => {
  return http.get(`/runs/${runId}`)
}

export const getRunEvents = (runId: string, params?: { afterSeq?: number; limit?: number }) => {
  return http.get(`/runs/${runId}/events`, { params })
}

export const getRunArtifacts = (runId: string) => {
  return http.get(`/runs/${runId}/artifacts`)
}
