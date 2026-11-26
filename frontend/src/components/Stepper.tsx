const STEPS = ['Importer', 'Analyser', 'Vérifier']

/** Where the candidate is in the import: a real sequence, so it is numbered. */
export function Stepper({ current }: { current: 1 | 2 | 3 }) {
  return (
    <ol className="stepper" aria-label="Étapes de l'import">
      {STEPS.map((label, index) => {
        const number = index + 1
        const state = number < current ? 'is-done' : number === current ? 'is-current' : ''
        return (
          <li key={label} className={state} aria-current={number === current ? 'step' : undefined}>
            <span className="stepper-number" aria-hidden="true">
              {number}
            </span>
            {label}
          </li>
        )
      })}
    </ol>
  )
}
