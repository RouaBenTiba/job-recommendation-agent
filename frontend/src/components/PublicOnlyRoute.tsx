import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useMe } from '../hooks/useAuth'
import { Spinner } from './Spinner'

/** Login and registration pages: a signed-in candidate goes straight to the private area. */
export function PublicOnlyRoute() {
  const { data: user, isPending } = useMe()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from

  if (isPending) return <Spinner />
  if (user) return <Navigate to={from ?? '/profile'} replace />
  return <Outlet />
}
