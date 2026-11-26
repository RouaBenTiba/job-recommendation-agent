import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <main className="center-page">
      <h1>Page introuvable</h1>
      <p className="muted">Cette adresse n&apos;existe pas, ou elle a été déplacée.</p>
      <Link to="/profile" className="button-link">
        Retourner à mon profil
      </Link>
    </main>
  )
}
