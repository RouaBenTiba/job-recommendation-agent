import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getPreferences, savePreferences } from '../api/preferences'

export const PREFERENCES_KEY = ['preferences'] as const

export const usePreferences = () => useQuery({ queryKey: PREFERENCES_KEY, queryFn: getPreferences })

export function useSavePreferences() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: savePreferences,
    onSuccess: (preferences) => client.setQueryData(PREFERENCES_KEY, preferences),
  })
}
