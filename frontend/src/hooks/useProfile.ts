import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getProfile,
  listProfileVersions,
  restoreProfileVersion,
  updateProfile,
} from '../api/profile'
import type { Profile } from '../api/types'

export const PROFILE_KEY = ['profile'] as const
export const VERSIONS_KEY = ['profile-versions'] as const

export const useProfile = () => useQuery({ queryKey: PROFILE_KEY, queryFn: getProfile })

export const useProfileVersions = () =>
  useQuery({ queryKey: VERSIONS_KEY, queryFn: listProfileVersions })

function useProfileWriter() {
  const client = useQueryClient()
  return (profile: Profile) => {
    client.setQueryData(PROFILE_KEY, profile)
    void client.invalidateQueries({ queryKey: VERSIONS_KEY })
  }
}

export function useUpdateProfile() {
  const store = useProfileWriter()
  return useMutation({ mutationFn: updateProfile, onSuccess: store })
}

export function useRestoreProfileVersion() {
  const store = useProfileWriter()
  return useMutation({ mutationFn: restoreProfileVersion, onSuccess: store })
}
