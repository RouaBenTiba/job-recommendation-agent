import { FileText } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { Profile, ProfileUpdate } from '../api/types'
import { AnalysisProgress } from '../components/AnalysisProgress'
import { CvDropzone } from '../components/CvDropzone'
import { Notice } from '../components/Notice'
import { ProfileEditor } from '../components/ProfileEditor'
import { Stepper } from '../components/Stepper'
import { useMe } from '../hooks/useAuth'
import { useCvImport } from '../hooks/useCvImport'
import { useUpdateProfile } from '../hooks/useProfile'
import { formatFileSize, validateCvFiles } from '../lib/cvFile'

export function ImportPage() {
  const { data: user } = useMe()
  const { state, start, retry, reset } = useCvImport()
  const update = useUpdateProfile()
  const [consent, setConsent] = useState(false)
  const [fileError, setFileError] = useState<string | null>(null)
  const [saved, setSaved] = useState<Profile | null>(null)

  const choosing = state.phase === 'idle' || (state.phase === 'failed' && state.stage === 'upload')
  const step = state.phase === 'done' ? 3 : choosing ? 1 : 2

  const onFiles = (files: File[]) => {
    const problem = validateCvFiles(files)
    setFileError(problem)
    if (!problem) start(files[0])
  }

  const save = async (data: ProfileUpdate) => {
    setSaved(await update.mutateAsync(data))
  }

  const startOver = () => {
    setSaved(null)
    setFileError(null)
    reset()
  }

  return (
    <div className={state.phase === 'done' ? 'page' : 'page page-narrow'}>
      <header className="page-head">
        <div>
          <h1>Importer mon CV</h1>
          <p className="lede">
            Déposez votre CV : l&apos;IA en extrait un profil que vous pouvez ensuite vérifier et
            corriger.
          </p>
        </div>
      </header>
      <Stepper current={step} />

      {choosing && (
        <section className="document doc-section">
          <Notice>
            Votre CV est lu par le serveur puis envoyé à un service d&apos;IA (Google Gemini) pour
            en extraire le profil. N&apos;importez que des documents que vous souhaitez partager.
          </Notice>
          <label className="consent">
            <input
              type="checkbox"
              checked={consent}
              onChange={(event) => setConsent(event.target.checked)}
            />
            <span>J&apos;accepte que mon CV soit analysé par un service d&apos;IA.</span>
          </label>
          {state.phase === 'failed' && (
            <Notice tone="error" role="alert">
              {state.message}
            </Notice>
          )}
          {fileError && (
            <Notice tone="error" role="alert">
              {fileError}
            </Notice>
          )}
          <CvDropzone onFiles={onFiles} disabled={!consent} />
          {!consent && (
            <p className="field-hint">Cochez la case ci-dessus pour activer le dépôt.</p>
          )}
        </section>
      )}

      {(state.phase === 'running' || (state.phase === 'failed' && state.stage !== 'upload')) && (
        <section className="document doc-section">
          <div className="file-chip">
            <FileText size={20} aria-hidden="true" />
            <div>
              <strong>{state.file.name}</strong>
              <span className="muted">{formatFileSize(state.file.size)}</span>
            </div>
          </div>
          <AnalysisProgress stage={state.stage} failed={state.phase === 'failed'} />
          {state.phase === 'failed' && (
            <>
              <Notice tone="error" role="alert">
                {state.message}
              </Notice>
              <div className="form-actions">
                {state.retryable && (
                  <button type="button" onClick={retry}>
                    Réessayer
                  </button>
                )}
                <button type="button" className="secondary" onClick={startOver}>
                  Choisir un autre fichier
                </button>
              </div>
            </>
          )}
        </section>
      )}

      {state.phase === 'done' && (
        <>
          <Notice tone="success" role="status">
            Analyse terminée : {state.extraction.pages_read} page
            {state.extraction.pages_read > 1 ? 's' : ''} lue
            {state.extraction.pages_read > 1 ? 's' : ''},{' '}
            {state.extraction.characters.toLocaleString('fr-FR')} caractères.
          </Notice>
          {state.extraction.truncated && (
            <Notice tone="warning">
              Seules les {state.extraction.pages_read} premières pages sur{' '}
              {state.extraction.page_count} ont été lues : vérifiez que rien d&apos;important ne
              manque.
            </Notice>
          )}
          <Notice tone="warning">
            Voici ce que l&apos;IA a compris de votre CV : vérifiez chaque section et corrigez ce
            qui est inexact.
          </Notice>
          {saved && (
            <Notice tone="success" role="status">
              Corrections enregistrées : version {saved.version}.{' '}
              <Link to="/profile">Voir mon profil</Link>
            </Notice>
          )}
          <ProfileEditor
            key={(saved ?? state.profile).id}
            profile={saved ?? state.profile}
            ownerName={user?.full_name || user?.email || 'Mon profil'}
            onSave={save}
          />
          <div className="form-actions">
            <button type="button" className="secondary" onClick={startOver}>
              Importer un autre CV
            </button>
          </div>
        </>
      )}
    </div>
  )
}
