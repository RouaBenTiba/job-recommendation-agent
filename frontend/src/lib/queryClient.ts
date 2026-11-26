import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query'
import { isApiError } from '../api/client'
import { markSessionExpired } from './session'

export function createQueryClient(): QueryClient {
  const handleError = (error: Error) => {
    // A 401 on any request means the session is over: the router sends the candidate back to /login.
    if (isApiError(error, 401)) markSessionExpired(client)
  }
  const client = new QueryClient({
    queryCache: new QueryCache({ onError: handleError }),
    mutationCache: new MutationCache({ onError: handleError }),
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        // Client errors (401, 404, 422...) will not change by retrying.
        retry: (failureCount, error) =>
          !(isApiError(error) && error.status >= 400 && error.status < 500) && failureCount < 2,
      },
    },
  })
  return client
}
