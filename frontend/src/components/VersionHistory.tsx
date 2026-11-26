import { RotateCcw } from 'lucide-react'
import { useState } from 'react'
import type { ProfileVersion } from '../api/types'
import { formatDateTime, sourceLabel } from '../lib/format'

interface VersionHistoryProps {
  versions: ProfileVersion[]
  onRestore: (version: number) => void
  restoring: boolean
}

export function VersionHistory({ versions, onRestore, restoring }: VersionHistoryProps) {
  const [confirming, setConfirming] = useState<number | null>(null)
  const sorted = [...versions].sort((a, b) => b.version - a.version)

  if (sorted.length === 0) return <p className="muted">Aucune version pour le moment.</p>

  return (
    <ul className="versions">
      {sorted.map((item) => (
        <li key={item.id} className={item.is_current ? 'is-current' : undefined}>
          <div>
            <strong>Version {item.version}</strong>
            {item.is_current && <span className="badge badge-current">Courante</span>}
            <span className="version-meta">
              {sourceLabel(item.source)}, {formatDateTime(item.created_at)}
            </span>
          </div>
          {!item.is_current &&
            (confirming === item.version ? (
              <div
                className="confirm"
                role="group"
                aria-label={`Restaurer la version ${item.version}`}
              >
                <span>Elle deviendra une nouvelle version courante.</span>
                <button
                  type="button"
                  disabled={restoring}
                  onClick={() => {
                    setConfirming(null)
                    onRestore(item.version)
                  }}
                >
                  Confirmer la restauration
                </button>
                <button type="button" className="secondary" onClick={() => setConfirming(null)}>
                  Annuler
                </button>
              </div>
            ) : (
              <button
                type="button"
                className="secondary"
                onClick={() => setConfirming(item.version)}
              >
                <RotateCcw size={16} aria-hidden="true" />
                Restaurer
              </button>
            ))}
        </li>
      ))}
    </ul>
  )
}
