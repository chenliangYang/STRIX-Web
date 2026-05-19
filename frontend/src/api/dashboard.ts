import http from './http'

export const getDashboardSummary = () => {
  return http.get('/dashboard/summary')
}

export const getStatusDistribution = () => {
  return http.get('/dashboard/status-distribution')
}

export const getRecentScans = (limit?: number) => {
  return http.get('/dashboard/recent-scans', { params: { limit } })
}
