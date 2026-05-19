import http from './http'

// User APIs
export interface UserFormData {
  username: string
  account: string
  password?: string
  role: string
  department?: string
}

export const getUsers = (params?: { page?: number; pageSize?: number; role?: string; status?: string }) => {
  return http.get('/users', { params })
}

export const getUser = (userId: string) => {
  return http.get(`/users/${userId}`)
}

export const createUser = (data: UserFormData) => {
  return http.post('/users', data)
}

export const updateUser = (userId: string, data: Partial<UserFormData>) => {
  return http.put(`/users/${userId}`, data)
}

export const deleteUser = (userId: string) => {
  return http.delete(`/users/${userId}`)
}

export const enableUser = (userId: string) => {
  return http.post(`/users/${userId}/enable`)
}

export const disableUser = (userId: string) => {
  return http.post(`/users/${userId}/disable`)
}

export const resetUserPassword = (userId: string) => {
  return http.post(`/users/${userId}/reset-password`)
}

// Whitelist APIs
export interface WhitelistFormData {
  name: string
  target_type: string
  target_value: string
  project?: string
}

export const getWhitelists = (params?: { page?: number; pageSize?: number; name?: string; targetType?: string; status?: string }) => {
  return http.get('/whitelists', { params })
}

export const getWhitelist = (id: string) => {
  return http.get(`/whitelists/${id}`)
}

export const createWhitelist = (data: WhitelistFormData) => {
  return http.post('/whitelists', data)
}

export const updateWhitelist = (id: string, data: Partial<WhitelistFormData>) => {
  return http.put(`/whitelists/${id}`, data)
}

export const deleteWhitelist = (id: string) => {
  return http.delete(`/whitelists/${id}`)
}

export const enableWhitelist = (id: string) => {
  return http.post(`/whitelists/${id}/enable`)
}

export const disableWhitelist = (id: string) => {
  return http.post(`/whitelists/${id}/disable`)
}

export const checkWhitelist = (target: string) => {
  return http.post('/whitelists/check', { target })
}

// Audit Log APIs
export interface AuditLogParams {
  page?: number
  pageSize?: number
  actor?: string
  action?: string
  result?: string
  createdAtStart?: string
  createdAtEnd?: string
}

export const getAuditLogs = (params?: AuditLogParams) => {
  return http.get('/audit-logs', { params })
}
