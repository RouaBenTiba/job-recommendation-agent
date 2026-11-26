import { request } from './client'
import type { Preferences, PreferencesUpdate } from './types'

export const getPreferences = () => request<Preferences>('/preferences')

export const savePreferences = (data: PreferencesUpdate) =>
  request<Preferences>('/preferences', { method: 'PUT', json: data })
