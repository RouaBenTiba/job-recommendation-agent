import type { QueryClient } from '@tanstack/react-query'

export const ME_KEY = ['me'] as const
export const SESSION_EXPIRED_KEY = ['session-expired'] as const

/** The session ended while the candidate was signed in (expired token, revoked, ...). */
export function markSessionExpired(client: QueryClient): void {
  if (client.getQueryData(ME_KEY)) client.setQueryData(SESSION_EXPIRED_KEY, true)
  client.setQueryData(ME_KEY, null)
  // Nothing private must stay in the cache once the session is over.
  client.removeQueries({
    predicate: (query) =>
      query.queryKey[0] !== ME_KEY[0] && query.queryKey[0] !== SESSION_EXPIRED_KEY[0],
  })
}
