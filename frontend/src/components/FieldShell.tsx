import type { ReactNode } from 'react'

interface FieldShellProps {
  id: string
  label: string
  error?: string
  hint?: string
  children: ReactNode
}

/** Label, hint and error message around any input. */
export function FieldShell({ id, label, error, hint, children }: FieldShellProps) {
  return (
    <div className={error ? 'field field-invalid' : 'field'}>
      <label htmlFor={id}>{label}</label>
      {children}
      {hint && !error && (
        <p className="field-hint" id={`${id}-hint`}>
          {hint}
        </p>
      )}
      {error && (
        <p className="field-error" id={`${id}-error`} role="alert">
          {error}
        </p>
      )}
    </div>
  )
}
