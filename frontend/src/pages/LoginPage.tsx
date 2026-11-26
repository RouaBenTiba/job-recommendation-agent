import { zodResolver } from '@hookform/resolvers/zod'
import { useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { isApiError } from '../api/client'
import { AuthShell } from '../components/AuthShell'
import { Notice } from '../components/Notice'
import { TextField } from '../components/TextField'
import { useLogin } from '../hooks/useAuth'
import { loginSchema, type LoginValues } from '../lib/schemas'
import { SESSION_EXPIRED_KEY } from '../lib/session'

export function LoginPage() {
  const client = useQueryClient()
  const sessionExpired = client.getQueryData(SESSION_EXPIRED_KEY) === true
  const login = useLogin()
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginValues>({ resolver: zodResolver(loginSchema) })

  const message = login.error
    ? isApiError(login.error, 401)
      ? 'Adresse e-mail ou mot de passe incorrect.'
      : login.error.message
    : null

  return (
    <AuthShell
      title="Connexion"
      subtitle="Retrouvez votre profil et vos préférences."
      footer={
        <>
          Pas encore de compte ? <Link to="/register">Créer un compte</Link>
        </>
      }
    >
      {sessionExpired && (
        <Notice tone="warning" role="status">
          Votre session a expiré. Reconnectez-vous pour continuer.
        </Notice>
      )}
      <form onSubmit={handleSubmit((values) => login.mutate(values))} noValidate>
        <TextField
          label="Adresse e-mail"
          type="email"
          autoComplete="email"
          error={errors.email?.message}
          {...register('email')}
        />
        <TextField
          label="Mot de passe"
          type="password"
          autoComplete="current-password"
          error={errors.password?.message}
          {...register('password')}
        />
        {message && (
          <Notice tone="error" role="alert">
            {message}
          </Notice>
        )}
        <button type="submit" className="wide" disabled={login.isPending}>
          {login.isPending ? 'Connexion…' : 'Se connecter'}
        </button>
      </form>
    </AuthShell>
  )
}
