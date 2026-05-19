import http from './http'

export interface ResultListParams {
  page?: number
  pageSize?: number
  projectName?: string
  status?: string
  riskLevel?: string
  createdBy?: string
  startedAtStart?: string
  startedAtEnd?: string
  sortBy?: string
  sortOrder?: string
}

export const getResults = (params?: ResultListParams) => {
  return http.get('/results', { params })
}

export const getResult = (resultId: string) => {
  return http.get(`/results/${resultId}`)
}

export const getResultVulnerabilities = (resultId: string, params?: { page?: number; pageSize?: number }) => {
  return http.get(`/results/${resultId}/vulnerabilities`, { params })
}

export const getVulnerabilityMarkdown = (vulnId: string) => {
  return http.get(`/vulnerabilities/${vulnId}/markdown`)
}
