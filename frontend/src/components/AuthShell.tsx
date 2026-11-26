import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Logo } from './Logo'

interface AuthShellProps {
  title: string
  subtitle: string
  children: ReactNode
  footer: ReactNode
}

/** Sign-in and sign-up pages: a brand panel on the left, the form on the right. */
export function AuthShell({ title, subtitle, children, footer }: AuthShellProps) {
  return (
    <div className="auth">
      <aside className="auth-brand">
        <Link to="/login" className="brand">
          <Logo />
          <span>Job Recommender</span>
        </Link>
        <div>
          <p className="auth-headline">Un profil juste, des offres qui vous correspondent.</p>
          <p className="auth-lede">
            Importez votre CV, vérifiez ce que l&apos;IA en a compris et corrigez-le. Vos
            recommandations s&apos;appuient sur ce profil.
          </p>
        </div>
        <ol className="auth-steps">
          <li>Importez votre CV au format PDF</li>
          <li>Vérifiez et corrigez le profil extrait</li>
          <li>Indiquez vos préférences de contrat et de lieu</li>
        </ol>
      </aside>
      <main className="auth-main">
        <div className="auth-panel">
          <h1>{title}</h1>
          <p className="lede">{subtitle}</p>
          {children}
          <p className="auth-footer">{footer}</p>
        </div>
      </main>
    </div>
  )
}
