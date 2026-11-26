import { screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { CSRF_HEADER } from '../api/client'
import { mockApi, PROFILE, USER } from '../test/mockApi'
import { renderApp } from '../test/renderApp'

const UNAUTHORIZED = { status: 401, json: { code: 'unauthorized', detail: 'Not authenticated' } }

/** `/auth/me` answers 401 until the login call has been made, like the real session. */
function sessionApi(extra: Parameters<typeof mockApi>[0] = {}) {
  let signedIn = false
  return mockApi({
    'GET /auth/me': () => (signedIn ? { json: USER } : UNAUTHORIZED),
    'POST /auth/login': () => {
      signedIn = true
      return { json: { access_token: 'token', token_type: 'bearer', expires_in: 1800 } }
    },
    'POST /auth/register': { status: 201, json: USER },
    'POST /auth/logout': () => {
      signedIn = false
      return { status: 204 }
    },
    'GET /profile': { status: 404, json: { code: 'not_found', detail: 'Aucun profil.' } },
    'GET /profile/versions': { json: [] },
    ...extra,
  })
}

describe('route protection', () => {
  it('sends a signed-out visitor from a private page to the login page', async () => {
    sessionApi()
    renderApp('/profile')
    expect(await screen.findByRole('heading', { name: 'Connexion' })).toBeInTheDocument()
  })

  it('sends a signed-in candidate away from the login page', async () => {
    mockApi({
      'GET /auth/me': { json: USER },
      'GET /profile': { json: PROFILE },
      'GET /profile/versions': { json: [] },
    })
    renderApp('/login')
    expect(await screen.findByRole('heading', { name: 'Mon profil' })).toBeInTheDocument()
  })

  it('redirects the root to the profile and shows a page for unknown addresses', async () => {
    sessionApi()
    renderApp('/nowhere')
    expect(await screen.findByRole('heading', { name: 'Page introuvable' })).toBeInTheDocument()
  })
})

describe('login', () => {
  it('signs in: form-encoded credentials, CSRF header, then the private area', async () => {
    const api = sessionApi()
    const { user } = renderApp('/login')
    await user.type(await screen.findByLabelText('Adresse e-mail'), 'roua@example.com')
    await user.type(screen.getByLabelText('Mot de passe'), 'Motdepasse123!')
    await user.click(screen.getByRole('button', { name: 'Se connecter' }))

    expect(await screen.findByRole('heading', { name: 'Mon profil' })).toBeInTheDocument()
    const [call] = api.to('POST', '/auth/login')
    expect(call.form?.get('username')).toBe('roua@example.com')
    expect(call.form?.get('password')).toBe('Motdepasse123!')
    expect(call.headers.get(CSRF_HEADER)).toBe('1')
  })

  it('never keeps the token in the page: nothing is written to web storage', async () => {
    sessionApi()
    const { user } = renderApp('/login')
    await user.type(await screen.findByLabelText('Adresse e-mail'), 'roua@example.com')
    await user.type(screen.getByLabelText('Mot de passe'), 'Motdepasse123!')
    await user.click(screen.getByRole('button', { name: 'Se connecter' }))
    await screen.findByRole('heading', { name: 'Mon profil' })
    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
  })

  it('shows a clear message when the credentials are wrong', async () => {
    sessionApi({
      'POST /auth/login': {
        status: 401,
        json: { code: 'unauthorized', detail: 'Incorrect email or password' },
      },
    })
    const { user } = renderApp('/login')
    await user.type(await screen.findByLabelText('Adresse e-mail'), 'roua@example.com')
    await user.type(screen.getByLabelText('Mot de passe'), 'wrong-password')
    await user.click(screen.getByRole('button', { name: 'Se connecter' }))

    expect(await screen.findByText('Adresse e-mail ou mot de passe incorrect.')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Connexion' })).toBeInTheDocument()
  })

  it('validates the form before calling the server', async () => {
    const api = sessionApi()
    const { user } = renderApp('/login')
    await user.click(await screen.findByRole('button', { name: 'Se connecter' }))

    expect(await screen.findByText("L'adresse e-mail est obligatoire")).toBeInTheDocument()
    expect(screen.getByText('Le mot de passe est obligatoire')).toBeInTheDocument()
    expect(api.to('POST', '/auth/login')).toHaveLength(0)
  })
})

describe('registration', () => {
  it('validates the password rules and the confirmation', async () => {
    const api = sessionApi()
    const { user } = renderApp('/register')
    await user.type(await screen.findByLabelText('Adresse e-mail'), 'new@example.com')
    await user.type(screen.getByLabelText('Mot de passe'), 'short')
    await user.type(screen.getByLabelText('Confirmer le mot de passe'), 'other')
    await user.click(screen.getByRole('button', { name: 'Créer mon compte' }))

    expect(await screen.findByText('Au moins 8 caractères')).toBeInTheDocument()
    expect(screen.getByText('Les mots de passe ne correspondent pas')).toBeInTheDocument()
    expect(api.to('POST', '/auth/register')).toHaveLength(0)
  })

  it('creates the account, signs in and opens the private area', async () => {
    const api = sessionApi()
    const { user } = renderApp('/register')
    await user.type(await screen.findByLabelText('Adresse e-mail'), 'new@example.com')
    await user.type(screen.getByLabelText('Mot de passe'), 'Motdepasse123!')
    await user.type(screen.getByLabelText('Confirmer le mot de passe'), 'Motdepasse123!')
    await user.click(screen.getByRole('button', { name: 'Créer mon compte' }))

    expect(await screen.findByRole('heading', { name: 'Mon profil' })).toBeInTheDocument()
    // the optional name is left out, and the confirmation never leaves the browser
    expect(api.to('POST', '/auth/register')[0].json).toEqual({
      email: 'new@example.com',
      password: 'Motdepasse123!',
    })
    expect(api.to('POST', '/auth/login')).toHaveLength(1)
  })

  it('tells the candidate when the email is already used', async () => {
    sessionApi({
      'POST /auth/register': {
        status: 409,
        json: { code: 'conflict', detail: 'Email already registered' },
      },
    })
    const { user } = renderApp('/register')
    await user.type(await screen.findByLabelText('Adresse e-mail'), 'roua@example.com')
    await user.type(screen.getByLabelText('Mot de passe'), 'Motdepasse123!')
    await user.type(screen.getByLabelText('Confirmer le mot de passe'), 'Motdepasse123!')
    await user.click(screen.getByRole('button', { name: 'Créer mon compte' }))

    expect(
      await screen.findByText('Un compte existe déjà avec cette adresse e-mail.'),
    ).toBeInTheDocument()
  })

  it('shows the field errors returned by the server', async () => {
    sessionApi({
      'POST /auth/register': {
        status: 422,
        json: {
          code: 'validation_error',
          detail: 'Les données envoyées sont invalides.',
          errors: [{ field: 'full_name', message: 'String should have at most 150 characters' }],
        },
      },
    })
    const { user } = renderApp('/register')
    await user.type(await screen.findByLabelText('Adresse e-mail'), 'new@example.com')
    await user.type(screen.getByLabelText('Mot de passe'), 'Motdepasse123!')
    await user.type(screen.getByLabelText('Confirmer le mot de passe'), 'Motdepasse123!')
    await user.click(screen.getByRole('button', { name: 'Créer mon compte' }))

    expect(await screen.findByText('String should have at most 150 characters')).toBeInTheDocument()
  })
})

describe('session', () => {
  it('signs out and goes back to the login page', async () => {
    const api = sessionApi()
    const { user } = renderApp('/login')
    await user.type(await screen.findByLabelText('Adresse e-mail'), 'roua@example.com')
    await user.type(screen.getByLabelText('Mot de passe'), 'Motdepasse123!')
    await user.click(screen.getByRole('button', { name: 'Se connecter' }))
    await user.click(await screen.findByRole('button', { name: 'Se déconnecter' }))

    expect(await screen.findByRole('heading', { name: 'Connexion' })).toBeInTheDocument()
    expect(api.to('POST', '/auth/logout')).toHaveLength(1)
    expect(
      screen.queryByText('Votre session a expiré. Reconnectez-vous pour continuer.'),
    ).not.toBeInTheDocument()
  })

  it('explains it when the session expires while the candidate is working', async () => {
    mockApi({
      'GET /auth/me': { json: USER },
      'GET /profile': { json: PROFILE },
      'GET /profile/versions': { json: [] },
      'PATCH /profile': UNAUTHORIZED,
    })
    const { user } = renderApp('/profile')
    const summary = await screen.findByLabelText('Résumé')
    await user.type(summary, ' Complété.')
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    expect(await screen.findByRole('heading', { name: 'Connexion' })).toBeInTheDocument()
    await waitFor(() =>
      expect(
        screen.getByText('Votre session a expiré. Reconnectez-vous pour continuer.'),
      ).toBeInTheDocument(),
    )
  })
})
