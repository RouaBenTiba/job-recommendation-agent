import { fireEvent, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockApi, PROFILE, USER, VERSIONS } from '../test/mockApi'
import { renderApp } from '../test/renderApp'

const NO_PROFILE = {
  status: 404,
  json: { code: 'not_found', detail: 'Aucun profil pour le moment.' },
}

function profileApi(extra: Parameters<typeof mockApi>[0] = {}) {
  return mockApi({
    'GET /auth/me': { json: USER },
    'GET /profile': { json: PROFILE },
    'GET /profile/versions': { json: VERSIONS },
    ...extra,
  })
}

describe('profile page', () => {
  it('shows the current profile in an editable form', async () => {
    profileApi()
    renderApp('/profile')

    expect(await screen.findByLabelText('Résumé')).toHaveValue(
      'Étudiante ingénieure en informatique.',
    )
    const state = within(screen.getByRole('group', { name: 'État du profil' }))
    expect(state.getByText('Version 2')).toBeInTheDocument()
    expect(state.getByText("Extrait par l'IA")).toBeInTheDocument()
    expect(screen.getByText(/vérifiez les informations extraites/)).toBeInTheDocument()
    const education = screen.getByRole('group', { name: 'Formation 1' })
    expect(within(education).getByLabelText('Établissement')).toHaveValue('ENIT')
    expect(within(education).getByLabelText('Début (année)')).toHaveValue('2023')
    const experience = screen.getByRole('group', { name: 'Expérience 1' })
    expect(within(experience).getByLabelText('Entreprise')).toHaveValue('Société Exemple')
    expect(screen.getByRole('list', { name: 'Technologies' })).toHaveTextContent('Docker')
  })

  it('cannot be saved while nothing changed', async () => {
    profileApi()
    renderApp('/profile')
    expect(await screen.findByRole('button', { name: 'Enregistrer' })).toBeDisabled()
  })

  it('sends only the modified field, then shows the new version', async () => {
    const api = profileApi({
      'PATCH /profile': {
        json: { ...PROFILE, id: 'profile-3', version: 3, summary: 'Nouveau résumé' },
      },
    })
    const { user } = renderApp('/profile')
    const summary = await screen.findByLabelText('Résumé')
    await user.clear(summary)
    await user.type(summary, 'Nouveau résumé')
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    expect(await screen.findByText('Profil enregistré : version 3.')).toBeInTheDocument()
    expect(api.to('PATCH', '/profile')).toHaveLength(1)
    expect(api.to('PATCH', '/profile')[0].json).toEqual({ summary: 'Nouveau résumé' })
    expect(await screen.findByLabelText('Résumé')).toHaveValue('Nouveau résumé')
    expect(screen.getByRole('button', { name: 'Enregistrer' })).toBeDisabled()
  })

  it('adds a tag with Enter without submitting the form, and removes one', async () => {
    const api = profileApi({ 'PATCH /profile': { json: PROFILE } })
    const { user } = renderApp('/profile')
    const skills = await screen.findByLabelText('Compétences', { selector: 'input' })
    await user.type(skills, 'Rigueur{Enter}')
    expect(api.to('PATCH', '/profile')).toHaveLength(0)
    await user.click(screen.getByRole('button', { name: 'Retirer Travail en équipe' }))
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    await screen.findByText(/Profil enregistré/)
    expect(api.to('PATCH', '/profile')[0].json).toEqual({ skills: ['Rigueur'] })
  })

  it('ignores a duplicate tag whatever its case', async () => {
    profileApi()
    const { user } = renderApp('/profile')
    const technologies = await screen.findByLabelText('Technologies', { selector: 'input' })
    await user.type(technologies, 'python{Enter}')
    expect(screen.getByRole('list', { name: 'Technologies' }).querySelectorAll('li')).toHaveLength(
      2,
    )
  })

  it('adds and removes an education entry', async () => {
    const api = profileApi({ 'PATCH /profile': { json: PROFILE } })
    const { user } = renderApp('/profile')
    await user.click(await screen.findByRole('button', { name: 'Ajouter une formation' }))
    const added = screen.getByRole('group', { name: 'Formation 2' })
    await user.type(within(added).getByLabelText('Établissement'), 'FST')
    await user.type(within(added).getByLabelText('Début (année)'), '2019')
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    await screen.findByText(/Profil enregistré/)
    expect(api.to('PATCH', '/profile')[0].json).toEqual({
      education: [
        {
          school: 'ENIT',
          degree: 'Cycle ingénieur',
          field_of_study: null,
          start_year: 2023,
          end_year: 2026,
        },
        { school: 'FST', degree: null, field_of_study: null, start_year: 2019, end_year: null },
      ],
    })
  })

  it('blocks invalid input before calling the server', async () => {
    const api = profileApi()
    const { user } = renderApp('/profile')
    fireEvent.change(await screen.findByLabelText('Résumé'), {
      target: { value: 'x'.repeat(2001) },
    })
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    expect(await screen.findByText('2000 caractères maximum')).toBeInTheDocument()
    expect(api.to('PATCH', '/profile')).toHaveLength(0)
  })

  it('requires the school of a new education entry', async () => {
    const api = profileApi()
    const { user } = renderApp('/profile')
    await user.click(await screen.findByRole('button', { name: 'Ajouter une formation' }))
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    expect(await screen.findByText("L'établissement est obligatoire")).toBeInTheDocument()
    expect(api.to('PATCH', '/profile')).toHaveLength(0)
  })

  it('shows the errors returned by the server under the right fields', async () => {
    profileApi({
      'PATCH /profile': {
        status: 422,
        json: {
          code: 'validation_error',
          detail: 'Les données envoyées sont invalides.',
          errors: [
            { field: 'skills.0', message: 'Server says: invalid skill' },
            { field: 'experiences.0.company', message: 'Server says: invalid company' },
          ],
        },
      },
    })
    const { user } = renderApp('/profile')
    const summary = await screen.findByLabelText('Résumé')
    await user.type(summary, ' !')
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    expect(await screen.findByText('Server says: invalid skill')).toBeInTheDocument()
    expect(screen.getByText('Server says: invalid company')).toBeInTheDocument()
    expect(screen.getByText('Corrigez les champs signalés.')).toBeInTheDocument()
  })

  it('cancels the modifications', async () => {
    profileApi()
    const { user } = renderApp('/profile')
    const summary = await screen.findByLabelText('Résumé')
    await user.type(summary, ' modifié')
    await user.click(screen.getByRole('button', { name: 'Annuler les modifications' }))
    expect(screen.getByLabelText('Résumé')).toHaveValue('Étudiante ingénieure en informatique.')
  })

  it('lets a candidate without profile create one', async () => {
    const api = profileApi({
      'GET /profile': NO_PROFILE,
      'GET /profile/versions': { json: [] },
      'PATCH /profile': { json: { ...PROFILE, id: 'profile-1', version: 1, source: 'manual' } },
    })
    const { user } = renderApp('/profile')
    expect(await screen.findByText(/Aucun profil pour le moment/)).toBeInTheDocument()
    expect(screen.getByText('Aucune version pour le moment.')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Technologies', { selector: 'input' }), 'Python{Enter}')
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    expect(await screen.findByText('Profil enregistré : version 1.')).toBeInTheDocument()
    expect(api.to('PATCH', '/profile')[0].json).toEqual({ technologies: ['Python'] })
  })
})

describe('version history', () => {
  it('lists the versions, the current one first, without a restore button on it', async () => {
    profileApi()
    renderApp('/profile')
    const items = await screen
      .findAllByRole('listitem')
      .then((all) => all.filter((li) => /^Version \d/.test(li.textContent ?? '')))
    expect(items.map((li) => li.textContent)).toEqual([
      expect.stringContaining('Version 2Courante'),
      expect.stringContaining('Version 1'),
    ])
    expect(within(items[0]).queryByRole('button')).not.toBeInTheDocument()
    expect(within(items[1]).getByRole('button', { name: 'Restaurer' })).toBeInTheDocument()
  })

  it('asks for confirmation, then restores the chosen version', async () => {
    const api = profileApi({
      'POST /profile/versions/1/restore': {
        status: 201,
        json: { ...PROFILE, id: 'profile-3', version: 3, summary: 'Ancien résumé' },
      },
    })
    const { user } = renderApp('/profile')
    await user.click(await screen.findByRole('button', { name: 'Restaurer' }))
    expect(api.to('POST', '/profile/versions/1/restore')).toHaveLength(0) // nothing yet
    await user.click(screen.getByRole('button', { name: 'Confirmer la restauration' }))

    expect(
      await screen.findByText('Version 1 restaurée : elle devient la version 3.'),
    ).toBeInTheDocument()
    expect(api.to('POST', '/profile/versions/1/restore')).toHaveLength(1)
    expect(await screen.findByLabelText('Résumé')).toHaveValue('Ancien résumé')
  })

  it('lets the candidate change her mind', async () => {
    const api = profileApi()
    const { user } = renderApp('/profile')
    await user.click(await screen.findByRole('button', { name: 'Restaurer' }))
    await user.click(screen.getByRole('button', { name: 'Annuler' }))
    expect(screen.getByRole('button', { name: 'Restaurer' })).toBeInTheDocument()
    expect(api.to('POST', '/profile/versions/1/restore')).toHaveLength(0)
  })
})

describe('live preview', () => {
  const sheet = () => within(screen.getByRole('article', { name: 'Aperçu du CV' }))

  it('shows the profile as a CV, with the name of the candidate', async () => {
    profileApi()
    renderApp('/profile')
    await screen.findByLabelText('Résumé')

    expect(sheet().getByText('Roua')).toBeInTheDocument()
    expect(sheet().getByText('Profil, version 2')).toBeInTheDocument()
    expect(sheet().getByText('Étudiante ingénieure en informatique.')).toBeInTheDocument()
    expect(sheet().getByText('Docker')).toBeInTheDocument()
    expect(sheet().getByText('ENIT')).toBeInTheDocument()
    expect(sheet().getByText('Stagiaire, Société Exemple')).toBeInTheDocument()
  })

  it('updates while the candidate types, before anything is saved', async () => {
    const api = profileApi()
    const { user } = renderApp('/profile')
    const summary = await screen.findByLabelText('Résumé')
    await user.clear(summary)
    await user.type(summary, 'Un résumé tout neuf')
    await user.type(
      screen.getByLabelText('Technologies', { selector: 'input' }),
      'Kubernetes{Enter}',
    )

    expect(sheet().getByText('Un résumé tout neuf')).toBeInTheDocument()
    expect(sheet().getByText('Kubernetes')).toBeInTheDocument()
    expect(api.to('PATCH', '/profile')).toHaveLength(0)
  })

  it('invites the candidate to fill the empty sections', async () => {
    profileApi({ 'GET /profile': NO_PROFILE, 'GET /profile/versions': { json: [] } })
    renderApp('/profile')
    await screen.findByText(/Aucun profil pour le moment/)

    expect(sheet().getByText('Nouveau profil')).toBeInTheDocument()
    expect(sheet().getByText('Votre résumé apparaîtra ici.')).toBeInTheDocument()
    expect(sheet().getByText('Vos stages et emplois apparaîtront ici.')).toBeInTheDocument()
  })

  it('counts the sections that are filled in and names the missing ones', async () => {
    profileApi({ 'GET /profile': NO_PROFILE, 'GET /profile/versions': { json: [] } })
    const { user } = renderApp('/profile')
    expect(
      await screen.findByRole('img', { name: '0 sections sur 5 renseignées' }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/À compléter : Résumé, Compétences, Technologies, Formation, Expériences\./),
    ).toBeInTheDocument()

    await user.type(screen.getByLabelText('Compétences', { selector: 'input' }), 'Rigueur{Enter}')
    expect(screen.getByRole('img', { name: '1 sections sur 5 renseignées' })).toBeInTheDocument()
  })

  it('shows a complete profile as complete', async () => {
    profileApi()
    renderApp('/profile')
    expect(
      await screen.findByRole('img', { name: '5 sections sur 5 renseignées' }),
    ).toBeInTheDocument()
    expect(screen.getByText(/Votre profil est complet\./)).toBeInTheDocument()
  })

  it('says whether there are unsaved changes', async () => {
    profileApi()
    const { user } = renderApp('/profile')
    expect(await screen.findByText('Aucune modification')).toBeInTheDocument()
    await user.type(screen.getByLabelText('Résumé'), ' !')
    expect(screen.getByText('Modifications non enregistrées')).toBeInTheDocument()
  })
})
