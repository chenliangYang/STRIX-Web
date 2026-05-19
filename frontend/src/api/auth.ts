import http from './http'

export interface LoginRequest {
  account: string
  password: string
  role: string
}

export interface LoginResponse {
  token: string
  user: {
    id: string
    username: string
    account: string
    role: string
  }
}

export const login = (data: LoginRequest) => {
  return http.post<{ data: LoginResponse }>('/auth/login', data)
}

export const getMe = () => {
  return http.get('/auth/me')
}

export const logout = () => {
  return http.post('/auth/logout')
}
