import { fireEvent, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { mockApi, PROFILE, USER } from '../test/mockApi'
import { renderApp } from '../test/renderApp'

const CV = {
  id: 'cv-1',
  filename: 'cv.pdf',
  content_type: 'application/pdf',
  file_size_bytes: 1200,
  status: 'uploaded',
  error_message: null,
  created_at: '2026-11-05T10:00:00Z',
  updated_at: '2026-11-05T10:00:00Z',
}
const EXTRACTION = {
  cv_id: 'cv-1',
  status: 'parsed',
  method: 'text',
  page_count: 2,
  pages_read: 2,
  truncated: false,
  characters: 4120,
  text: 'ne doit jamais être conservé dans le navigateur',
}
const PDF = () => new File(['%PDF-1.4 contenu'], 'cv.pdf', { type: 'application/pdf' })

function importApi(extra: Parameters<typeof mockApi>[0] = {}) {
  return mockApi({
    'GET /auth/me': { json: USER },
    'POST /cvs': { status: 201, json: CV },
    'POST /cvs/cv-1/extract': { json: EXTRACTION },
    'POST /cvs/cv-1/profile': { status: 201, json: PROFILE },
    'GET /profile/versions': { json: [] },
    ...extra,
  })
}

const consent = (user: ReturnType<typeof renderApp>['user']) =>
  user.click(screen.getByLabelText(/J'accepte que mon CV soit analysé/))

const dropzone = () => screen.getByRole('group', { name: 'Zone de dépôt du CV' })

async function openImport(extra: Parameters<typeof mockApi>[0] = {}) {
  const api = importApi(extra)
  const app = renderApp('/import')
  await screen.findByRole('heading', { name: 'Importer mon CV' })
  return { api, ...app }
}

describe('consent and file choice', () => {
  it('blocks the drop zone until the candidate accepts the analysis by an AI service', async () => {
    const { user } = await openImport()
    expect(screen.getByRole('button', { name: 'Choisir un fichier' })).toBeDisabled()
    expect(screen.getByText(/Cochez la case/)).toBeInTheDocument()
    expect(screen.getByText(/Google Gemini/)).toBeInTheDocument()

    await consent(user)
    expect(screen.getByRole('button', { name: 'Choisir un fichier' })).toBeEnabled()
  })

  it('shows the three steps, starting at the first', async () => {
    await openImport()
    const steps = within(screen.getByRole('list', { name: "Étapes de l'import" })).getAllByRole(
      'listitem',
    )
    expect(steps.map((step) => step.textContent)).toEqual(['1Importer', '2Analyser', '3Vérifier'])
    expect(steps[0]).toHaveAttribute('aria-current', 'step')
  })

  it.each([
    [
      'a Word document',
      new File(['x'], 'cv.docx', { type: 'application/msword' }),
      'Seuls les fichiers PDF sont acceptés.',
    ],
    ['an empty file', new File([], 'cv.pdf', { type: 'application/pdf' }), 'Le fichier est vide.'],
    [
      'a file over 5 MB',
      new File([new ArrayBuffer(5 * 1024 * 1024 + 1)], 'big.pdf', { type: 'application/pdf' }),
      'Le fichier dépasse la taille maximale de 5 Mo.',
    ],
  ])('refuses %s without calling the server', async (_name, file, message) => {
    const { api, user } = await openImport()
    await consent(user)
    fireEvent.change(screen.getByLabelText('Fichier PDF du CV'), { target: { files: [file] } })

    expect(await screen.findByText(message)).toBeInTheDocument()
    expect(api.to('POST', '/cvs')).toHaveLength(0)
  })

  it('refuses several dropped files', async () => {
    const { api, user } = await openImport()
    await consent(user)
    fireEvent.drop(dropzone(), { dataTransfer: { files: [PDF(), PDF()] } })

    expect(await screen.findByText('Importez un seul fichier à la fois.')).toBeInTheDocument()
    expect(api.to('POST', '/cvs')).toHaveLength(0)
  })
})

describe('analysis', () => {
  it('uploads, reads, analyses, then shows the extracted profile to check', async () => {
    const { api, user } = await openImport()
    await consent(user)
    await user.upload(screen.getByLabelText('Fichier PDF du CV'), PDF())

    expect(
      await screen.findByText(/Analyse terminée : 2 pages lues, 4.120 caractères/),
    ).toBeInTheDocument()
    expect(api.calls.map((call) => `${call.method} ${call.path}`)).toEqual([
      'GET /auth/me',
      'POST /cvs',
      'POST /cvs/cv-1/extract',
      'POST /cvs/cv-1/profile',
    ])
    expect((api.to('POST', '/cvs')[0].formData?.get('file') as File).name).toBe('cv.pdf')
    // the profile is editable, and the candidate is told to check it
    expect(screen.getByLabelText('Résumé')).toHaveValue(PROFILE.summary)
    expect(screen.getByText(/vérifiez chaque section/)).toBeInTheDocument()
    const stepper = screen.getByRole('list', { name: "Étapes de l'import" })
    expect(within(stepper).getByText('Vérifier').closest('li')).toHaveAttribute(
      'aria-current',
      'step',
    )
  })

  it('also accepts a file dropped on the zone', async () => {
    const { api, user } = await openImport()
    await consent(user)
    fireEvent.drop(dropzone(), { dataTransfer: { files: [PDF()] } })

    expect(await screen.findByText(/Analyse terminée/)).toBeInTheDocument()
    expect(api.to('POST', '/cvs')).toHaveLength(1)
  })

  it('shows which step is running while the AI works', async () => {
    let release: () => void = () => {}
    const gate = new Promise<void>((resolve) => (release = resolve))
    const { user } = await openImport({
      'POST /cvs/cv-1/profile': async () => {
        await gate
        return { status: 201, json: PROFILE }
      },
    })
    await consent(user)
    await user.upload(screen.getByLabelText('Fichier PDF du CV'), PDF())

    const aiStep = (await screen.findByText("Analyse par l'IA")).closest('li')
    expect(aiStep).toHaveAttribute('aria-current', 'step')
    expect(screen.getByText('Lecture du texte du PDF').closest('li')).toHaveClass('progress-done')
    expect(screen.getByText('cv.pdf')).toBeInTheDocument()
    expect(screen.getByText('1 Ko')).toBeInTheDocument()

    release()
    expect(await screen.findByText(/Analyse terminée/)).toBeInTheDocument()
  })

  it('never keeps the text of the CV in the page', async () => {
    const { user } = await openImport()
    await consent(user)
    await user.upload(screen.getByLabelText('Fichier PDF du CV'), PDF())
    await screen.findByText(/Analyse terminée/)
    expect(document.body).not.toHaveTextContent('ne doit jamais être conservé')
  })

  it('warns when only the first pages were read', async () => {
    const { user } = await openImport({
      'POST /cvs/cv-1/extract': {
        json: { ...EXTRACTION, truncated: true, pages_read: 10, page_count: 25 },
      },
    })
    await consent(user)
    await user.upload(screen.getByLabelText('Fichier PDF du CV'), PDF())
    expect(await screen.findByText(/Seules les 10 premières pages sur 25/)).toBeInTheDocument()
  })
})

describe('failures', () => {
  it('explains a PDF with no readable text and offers another file, not a retry', async () => {
    const { api, user } = await openImport({
      'POST /cvs/cv-1/extract': {
        status: 422,
        json: { code: 'error', detail: 'Aucun texte exploitable dans ce PDF.' },
      },
    })
    await consent(user)
    await user.upload(screen.getByLabelText('Fichier PDF du CV'), PDF())

    expect(await screen.findByText('Aucun texte exploitable dans ce PDF.')).toBeInTheDocument()
    expect(screen.getByText('Lecture du texte du PDF').closest('li')).toHaveClass('progress-failed')
    expect(screen.queryByRole('button', { name: 'Réessayer' })).not.toBeInTheDocument()
    expect(api.to('POST', '/cvs/cv-1/profile')).toHaveLength(0)

    await user.click(screen.getByRole('button', { name: 'Choisir un autre fichier' }))
    expect(screen.getByLabelText(/J'accepte/)).toBeInTheDocument()
  })

  it('retries only the AI step when the service is unavailable', async () => {
    let attempts = 0
    const { api, user } = await openImport({
      'POST /cvs/cv-1/profile': () => {
        attempts += 1
        return attempts === 1
          ? {
              status: 503,
              json: { code: 'service_unavailable', detail: 'Le service est indisponible.' },
            }
          : { status: 201, json: PROFILE }
      },
    })
    await consent(user)
    await user.upload(screen.getByLabelText('Fichier PDF du CV'), PDF())
    expect(await screen.findByText('Le service est indisponible.')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Réessayer' }))
    expect(await screen.findByText(/Analyse terminée/)).toBeInTheDocument()
    expect(api.to('POST', '/cvs')).toHaveLength(1) // the file is not uploaded twice
    expect(api.to('POST', '/cvs/cv-1/extract')).toHaveLength(1)
    expect(api.to('POST', '/cvs/cv-1/profile')).toHaveLength(2)
  })

  it('shows a refusal of the server on the file choice screen', async () => {
    const { api, user } = await openImport({
      'POST /cvs': {
        status: 413,
        json: {
          code: 'payload_too_large',
          detail: 'Le fichier dépasse la taille maximale de 5 Mo.',
        },
      },
    })
    await consent(user)
    await user.upload(screen.getByLabelText('Fichier PDF du CV'), PDF())

    expect(
      await screen.findByText('Le fichier dépasse la taille maximale de 5 Mo.'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Choisir un fichier' })).toBeEnabled()
    expect(api.to('POST', '/cvs/cv-1/extract')).toHaveLength(0)
  })
})

describe('checking and saving the corrections', () => {
  it('saves only what the candidate corrected, as a new version', async () => {
    const { api, user } = await openImport({
      'PATCH /profile': {
        json: {
          ...PROFILE,
          id: 'profile-4',
          version: 4,
          source: 'manual',
          summary: 'Résumé corrigé',
        },
      },
    })
    await consent(user)
    await user.upload(screen.getByLabelText('Fichier PDF du CV'), PDF())
    const summary = await screen.findByLabelText('Résumé')
    await user.clear(summary)
    await user.type(summary, 'Résumé corrigé')
    await user.click(screen.getByRole('button', { name: 'Enregistrer' }))

    expect(await screen.findByText(/Corrections enregistrées : version 4\./)).toBeInTheDocument()
    expect(api.to('PATCH', '/profile')[0].json).toEqual({ summary: 'Résumé corrigé' })
    expect(screen.getByRole('link', { name: 'Voir mon profil' })).toHaveAttribute(
      'href',
      '/profile',
    )
    expect(await screen.findByLabelText('Résumé')).toHaveValue('Résumé corrigé')
  })

  it('lets the candidate import another CV', async () => {
    const { user } = await openImport()
    await consent(user)
    await user.upload(screen.getByLabelText('Fichier PDF du CV'), PDF())
    await screen.findByText(/Analyse terminée/)
    await user.click(screen.getByRole('button', { name: 'Importer un autre CV' }))
    expect(screen.getByLabelText(/J'accepte/)).toBeInTheDocument()
  })
})
