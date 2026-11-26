import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useMe } from '../hooks/useAuth'
import { Spinner } from './Spinner'

/** Private area: anyone who is not signed in is sent to the login page. */
export function ProtectedRoute() {
  const { data: user, isPending, isError } = useMe()
  const location = useLocation()

  if (isPending) return <Spinner />
  if (isError) return <p role="alert">Impossible de vérifier votre session. Réessayez plus tard.</p>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}
