import { FileUp, LogOut, SlidersHorizontal, UserRound } from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router-dom'
import { useLogout, useMe } from '../hooks/useAuth'
import { Logo } from './Logo'

function initials(name: string): string {
  const parts = name
    .split('@')[0]
    .split(/[\s._-]+/)
    .filter(Boolean)
  return `${parts[0]?.[0] ?? '?'}${parts[1]?.[0] ?? ''}`.toUpperCase()
}

export function Layout() {
  const { data: user } = useMe()
  const logout = useLogout()
  const name = user?.full_name || user?.email || ''

  return (
    <div className="shell">
      <aside className="rail">
        <Link to="/profile" className="brand">
          <Logo />
          <span>Job Recommender</span>
        </Link>
        <nav className="rail-nav" aria-label="Navigation principale">
          <NavLink to="/profile">
            <UserRound size={20} aria-hidden="true" />
            <span>Profil</span>
          </NavLink>
          <NavLink to="/import">
            <FileUp size={20} aria-hidden="true" />
            <span>Importer</span>
          </NavLink>
          <NavLink to="/preferences">
            <SlidersHorizontal size={20} aria-hidden="true" />
            <span>Préférences</span>
          </NavLink>
        </nav>
        <div className="rail-user">
          <div className="rail-user-id">
            <span className="avatar" aria-hidden="true">
              {initials(name)}
            </span>
            <span className="rail-user-name">{name}</span>
          </div>
          <button
            type="button"
            className="secondary"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
          >
            <LogOut size={18} aria-hidden="true" />
            <span className="logout-label">Se déconnecter</span>
          </button>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
