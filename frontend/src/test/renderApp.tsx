import { QueryClientProvider } from '@tanstack/react-query'
import { render } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'
import { createQueryClient } from '../lib/queryClient'

export function renderApp(route = '/') {
  const client = createQueryClient()
  // Same behaviour as production, without waiting for retries.
  client.setDefaultOptions({ queries: { retry: false, staleTime: 30_000 } })
  render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[route]}>
        <App />
      </MemoryRouter>
    </QueryClientProvider>,
  )
  return { client, user: userEvent.setup() }
}
