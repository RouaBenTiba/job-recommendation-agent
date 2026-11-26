import { request } from './client'
import type { User } from './types'

export interface RegisterData {
  email: string
  password: string
  full_name?: string
}

export const register = (data: RegisterData) =>
  request<User>('/auth/register', { method: 'POST', json: data })

/** OAuth2 password flow: the backend expects a form with `username` (the email). */
export const login = (email: string, password: string) =>
  request<{ access_token: string }>('/auth/login', {
    method: 'POST',
    form: { username: email, password },
  })

export const logout = () => request<void>('/auth/logout', { method: 'POST' })

export const fetchMe = () => request<User>('/auth/me')
