import { Sparkles } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import type { ProfileUpdate } from '../api/types'
import { Notice } from '../components/Notice'
import { ProfileEditor } from '../components/ProfileEditor'
import { Spinner } from '../components/Spinner'
import { VersionHistory } from '../components/VersionHistory'
import { useMe } from '../hooks/useAuth'
import {
  useProfile,
  useProfileVersions,
  useRestoreProfileVersion,
  useUpdateProfile,
} from '../hooks/useProfile'
import { formatDateTime, sourceLabel } from '../lib/format'

export function ProfilePage() {
  const { data: user } = useMe()
  const profile = useProfile()
  const versions = useProfileVersions()
  const update = useUpdateProfile()
  const restore = useRestoreProfileVersion()
  const [notice, setNotice] = useState<string | null>(null)

  if (profile.isPending) return <Spinner />
  if (profile.isError)
    return <p role="alert">Impossible de charger votre profil. Réessayez plus tard.</p>
  const current = profile.data

  const save = async (data: ProfileUpdate) => {
    setNotice(null)
    const saved = await update.mutateAsync(data)
    setNotice(`Profil enregistré : version ${saved.version}.`)
  }

  const onRestore = (version: number) => {
    setNotice(null)
    restore.mutate(version, {
      onSuccess: (restored) =>
        setNotice(`Version ${version} restaurée : elle devient la version ${restored.version}.`),
    })
  }

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Mon profil</h1>
          <p className="lede">
            Ce profil sert de base à vos recommandations. Corrigez ce que l&apos;IA a mal compris,
            complétez le reste.
          </p>
        </div>
        {current && (
          <div className="status-badges" role="group" aria-label="État du profil">
            <span className="badge">Version {current.version}</span>
            <span className={current.source === 'llm' ? 'badge badge-ai' : 'badge'}>
              {current.source === 'llm' && <Sparkles size={14} aria-hidden="true" />}
              {sourceLabel(current.source)}
            </span>
            <span className="muted">Mis à jour le {formatDateTime(current.updated_at)}</span>
          </div>
        )}
      </header>

      {!current && (
        <Notice role="status">
          Aucun profil pour le moment. Renseignez-le ci-dessous : il servira de base à vos
          recommandations. Vous pouvez aussi <Link to="/import">importer votre CV</Link>.
        </Notice>
      )}
      {current?.source === 'llm' && (
        <Notice tone="warning">
          Ce profil a été extrait de votre CV par l&apos;IA : vérifiez les informations extraites et
          corrigez-les si besoin.
        </Notice>
      )}
      {notice && (
        <Notice tone="success" role="status">
          {notice}
        </Notice>
      )}
      {restore.isError && (
        <Notice tone="error" role="alert">
          {restore.error.message}
        </Notice>
      )}

      <ProfileEditor
        key={current?.id ?? 'new'}
        profile={current}
        ownerName={user?.full_name || user?.email || 'Mon profil'}
        onSave={save}
      >
        <section className="document doc-section">
          <h2 className="doc-head">Historique des versions</h2>
          {versions.isPending ? (
            <Spinner />
          ) : versions.isError ? (
            <p role="alert">Impossible de charger l&apos;historique.</p>
          ) : (
            <VersionHistory
              versions={versions.data}
              onRestore={onRestore}
              restoring={restore.isPending}
            />
          )}
        </section>
      </ProfileEditor>
    </div>
  )
}
