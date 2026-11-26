import { Check, Circle, X } from 'lucide-react'
import type { ImportStage } from '../hooks/useCvImport'

const STAGES: { stage: ImportStage; label: string }[] = [
  { stage: 'upload', label: 'Téléversement du fichier' },
  { stage: 'extract', label: 'Lecture du texte du PDF' },
  { stage: 'profile', label: "Analyse par l'IA" },
]

interface AnalysisProgressProps {
  stage: ImportStage
  failed: boolean
}

/** The three steps of the analysis and where they stand. */
export function AnalysisProgress({ stage, failed }: AnalysisProgressProps) {
  const current = STAGES.findIndex((item) => item.stage === stage)
  return (
    <ol className="progress-steps" aria-live="polite">
      {STAGES.map((item, index) => {
        const state =
          index < current ? 'done' : index > current ? 'pending' : failed ? 'failed' : 'active'
        const text = { done: 'terminé', pending: 'à venir', failed: 'échec', active: 'en cours' }[
          state
        ]
        return (
          <li
            key={item.stage}
            className={`progress-${state}`}
            aria-current={state === 'active' ? 'step' : undefined}
          >
            <span className="progress-icon" aria-hidden="true">
              {state === 'done' && <Check size={16} />}
              {state === 'failed' && <X size={16} />}
              {state === 'pending' && <Circle size={10} />}
            </span>
            <span>{item.label}</span>
            <span className="visually-hidden">{text}</span>
          </li>
        )
      })}
    </ol>
  )
}
