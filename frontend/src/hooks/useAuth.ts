import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { fetchMe, login, logout, register, type RegisterData } from '../api/auth'
import { isApiError } from '../api/client'
import { ME_KEY, SESSION_EXPIRED_KEY, markSessionExpired } from '../lib/session'

/** The signed-in candidate, `null` when nobody is signed in, `undefined` while loading. */
export function useMe() {
  const client = useQueryClient()
  return useQuery({
    queryKey: ME_KEY,
    queryFn: async () => {
      try {
        return await fetchMe()
      } catch (error) {
        if (isApiError(error, 401)) {
          markSessionExpired(client)
          return null
        }
        throw error
      }
    },
  })
}

export function useLogin() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      await login(credentials.email, credentials.password) // the backend sets the session cookie
      return fetchMe()
    },
    onSuccess: (user) => {
      client.setQueryData(SESSION_EXPIRED_KEY, false)
      client.setQueryData(ME_KEY, user)
    },
  })
}

export function useRegister() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: async (data: RegisterData) => {
      await register(data)
      await login(data.email, data.password)
      return fetchMe()
    },
    onSuccess: (user) => {
      client.setQueryData(SESSION_EXPIRED_KEY, false)
      client.setQueryData(ME_KEY, user)
    },
  })
}

export function useLogout() {
  const client = useQueryClient()
  return useMutation({
    mutationFn: logout,
    onSettled: () => {
      // Even if the call failed (expired session), the candidate leaves the private area.
      client.setQueryData(ME_KEY, null)
      client.removeQueries({ predicate: (query) => query.queryKey[0] !== ME_KEY[0] })
    },
  })
}
