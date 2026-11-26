import { screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockApi, NO_PREFERENCES, USER } from '../test/mockApi'
import { renderApp } from '../test/renderApp'

const SAVED = {
  id: 'pref-1',
  contract_types: ['internship'],
  locations: ['Tunis'],
  domains: [],
  remote_ok: true,
  willing_to_relocate: false,
  updated_at: '2026-11-03T08:00:00Z',
}

function preferencesApi(extra: Parameters<typeof mockApi>[0] = {}) {
  return mockApi({
    'GET /auth/me': { json: USER },
    'GET /preferences': { json: NO_PREFERENCES },
    ...extra,
  })
}

describe('preferences page', () => {
  it('shows empty preferences by default and disables saving', async () => {
    preferencesApi()
    renderApp('/preferences')
    expect(await screen.findByRole('heading', { name: 'Mes préférences' })).toBeInTheDocument()
    expect(screen.getByLabelText('Stage')).not.toBeChecked()
    expect(screen.getByLabelText('Télétravail accepté')).not.toBeChecked()
    expect(screen.getByRole('button', { name: 'Enregistrer' })).toBeDisabled()
  })

  it('shows saved preferences', async () => {
    preferencesApi({ 'GET /preferences': { json: SAVED } })
    renderApp('/preferences')
    expect(await screen.findByLabelText('Stage')).toBeChecked()
    expect(screen.getByLabelText('Alternance')).not.toBeChecked()
    expect(screen.getByLabelText('Télétravail accepté')).toBeChecked()
    expect(screen.getByRole('list', { name: 'Localisations' })).toHaveTextContent('Tunis')
  })

  it('replaces the preferences with a complete payload', async () => {
    const api = preferencesApi({ 'PUT /preferences': { json: SAVED } })
    const { user } = renderApp('/preferences')
    await user.click(await screen.findByLabelText('Stage'))
    await user.type(screen.getByLabelText('Localisations', { selector: 'input' }), 'Tunis{Enter}')
    await user.click(screen.getByLabelText('Télétravail accepté'))
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    expect(await screen.findByText('Préférences enregistrées.')).toBeInTheDocument()
    expect(api.to('PUT', '/preferences')[0].json).toEqual({
      contract_types: ['internship'],
      locations: ['Tunis'],
      domains: [],
      remote_ok: true,
      willing_to_relocate: false,
    })
    expect(screen.getByRole('button', { name: 'Enregistrer' })).toBeDisabled()
  })

  it('can clear a choice', async () => {
    const api = preferencesApi({
      'GET /preferences': { json: SAVED },
      'PUT /preferences': { json: NO_PREFERENCES },
    })
    const { user } = renderApp('/preferences')
    await user.click(await screen.findByLabelText('Stage'))
    await user.click(screen.getByRole('button', { name: 'Retirer Tunis' }))
    await user.click(screen.getByLabelText('Télétravail accepté'))
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    await screen.findByText('Préférences enregistrées.')
    expect(api.to('PUT', '/preferences')[0].json).toEqual({
      contract_types: [],
      locations: [],
      domains: [],
      remote_ok: false,
      willing_to_relocate: false,
    })
  })

  it('shows the errors returned by the server', async () => {
    preferencesApi({
      'PUT /preferences': {
        status: 422,
        json: {
          code: 'validation_error',
          detail: 'Les données envoyées sont invalides.',
          errors: [{ field: 'locations.0', message: 'Server says: invalid place' }],
        },
      },
    })
    const { user } = renderApp('/preferences')
    await user.type(
      await screen.findByLabelText('Localisations', { selector: 'input' }),
      'Tunis{Enter}',
    )
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    expect(await screen.findByText('Server says: invalid place')).toBeInTheDocument()
    expect(screen.getByText('Corrigez les champs signalés.')).toBeInTheDocument()
  })

  it('limits a list to 20 places before calling the server', async () => {
    const api = preferencesApi()
    const { user } = renderApp('/preferences')
    const places = await screen.findByLabelText('Localisations', { selector: 'input' })
    await user.type(places, Array.from({ length: 21 }, (_, i) => `Ville${i}`).join(',') + ',')
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    expect(await screen.findByText('20 éléments maximum')).toBeInTheDocument()
    expect(api.to('PUT', '/preferences')).toHaveLength(0)
  })
})

describe('switches and tiles', () => {
  it('exposes the two settings as switches with a short name', async () => {
    preferencesApi({ 'GET /preferences': { json: SAVED } })
    renderApp('/preferences')
    expect(await screen.findByRole('switch', { name: 'Télétravail accepté' })).toBeChecked()
    expect(screen.getByRole('switch', { name: 'Prête à déménager' })).not.toBeChecked()
    expect(screen.getByText('Les offres à distance seront prises en compte.')).toBeInTheDocument()
  })

  it('offers the five contract types as choices', async () => {
    preferencesApi()
    renderApp('/preferences')
    const group = await screen.findByRole('group', { name: 'Types de contrat recherchés' })
    expect(
      within(group)
        .getAllByRole('checkbox')
        .map((box) => box.closest('label')?.textContent),
    ).toEqual([
      'Stage',
      'Alternance',
      'Temps plein (CDI)',
      'Temps partiel',
      'Contrat (CDD, freelance)',
    ])
  })
})
