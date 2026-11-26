import { isApiError, request } from './client'
import type { Profile, ProfileUpdate, ProfileVersion } from './types'

/** `null` when the candidate has no profile yet (the backend answers 404). */
export async function getProfile(): Promise<Profile | null> {
  try {
    return await request<Profile>('/profile')
  } catch (error) {
    if (isApiError(error, 404)) return null
    throw error
  }
}

export const updateProfile = (data: ProfileUpdate) =>
  request<Profile>('/profile', { method: 'PATCH', json: data })

export const listProfileVersions = () => request<ProfileVersion[]>('/profile/versions')

export const restoreProfileVersion = (version: number) =>
  request<Profile>(`/profile/versions/${version}/restore`, { method: 'POST' })
