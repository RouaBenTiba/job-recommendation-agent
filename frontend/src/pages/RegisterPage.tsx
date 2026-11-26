import { zodResolver } from '@hookform/resolvers/zod'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { isApiError } from '../api/client'
import { AuthShell } from '../components/AuthShell'
import { Notice } from '../components/Notice'
import { TextField } from '../components/TextField'
import { useRegister } from '../hooks/useAuth'
import { registerSchema, type RegisterValues } from '../lib/schemas'
import { applyServerErrors } from '../lib/serverErrors'

export function RegisterPage() {
  const registerAccount = useRegister()
  const [formError, setFormError] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) })

  const onSubmit = async (values: RegisterValues) => {
    setFormError(null)
    try {
      await registerAccount.mutateAsync({
        email: values.email,
        password: values.password,
        ...(values.full_name ? { full_name: values.full_name } : {}),
      })
    } catch (error) {
      if (!isApiError(error)) throw error
      if (error.status === 409) {
        setError('email', {
          type: 'server',
          message: 'Un compte existe déjà avec cette adresse e-mail.',
        })
      } else if (!applyServerErrors(setError, error.fieldErrors)) {
        setFormError(error.message)
      }
    }
  }

  return (
    <AuthShell
      title="Créer un compte"
      subtitle="Créez votre compte, puis complétez votre profil."
      footer={
        <>
          Déjà inscrite ? <Link to="/login">Se connecter</Link>
        </>
      }
    >
      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <TextField
          label="Nom complet (facultatif)"
          autoComplete="name"
          error={errors.full_name?.message}
          {...register('full_name')}
        />
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
          autoComplete="new-password"
          hint="Entre 8 et 128 caractères."
          error={errors.password?.message}
          {...register('password')}
        />
        <TextField
          label="Confirmer le mot de passe"
          type="password"
          autoComplete="new-password"
          error={errors.confirmPassword?.message}
          {...register('confirmPassword')}
        />
        {formError && (
          <Notice tone="error" role="alert">
            {formError}
          </Notice>
        )}
        <button type="submit" className="wide" disabled={registerAccount.isPending}>
          {registerAccount.isPending ? 'Création…' : 'Créer mon compte'}
        </button>
      </form>
    </AuthShell>
  )
}
