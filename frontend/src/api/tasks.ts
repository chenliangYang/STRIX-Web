import http from './http'

export interface TaskListParams {
  page?: number
  pageSize?: number
  name?: string
  target?: string
  scanMode?: string
  interactive?: boolean
  status?: string
  riskLevel?: string
  createdBy?: string
  createdAtStart?: string
  createdAtEnd?: string
}

export interface TaskFormData {
  name: string
  target: string
  scan_mode: string
  interactive?: boolean
  instruction?: string
}

export const getTasks = (params?: TaskListParams) => {
  return http.get('/tasks', { params })
}

export const getTask = (id: string) => {
  return http.get(`/tasks/${id}`)
}

export const createTask = (data: TaskFormData) => {
  return http.post('/tasks', data)
}

export const updateTask = (id: string, data: Partial<TaskFormData>) => {
  return http.put(`/tasks/${id}`, data)
}

export const deleteTask = (id: string) => {
  return http.delete(`/tasks/${id}`)
}

export const executeTask = (id: string) => {
  return http.post(`/tasks/${id}/execute`, {})
}

export const stopTask = (id: string) => {
  return http.post(`/tasks/${id}/stop`, {})
}
