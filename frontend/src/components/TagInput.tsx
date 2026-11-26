import { X } from 'lucide-react'
import { useId, useState, type KeyboardEvent } from 'react'
import { FieldShell } from './FieldShell'

interface TagInputProps {
  label: string
  value: string[]
  onChange: (value: string[]) => void
  error?: string
  hint?: string
  placeholder?: string
}

/** A list of short labels: type one and press Enter or comma to add it. */
export function TagInput({ label, value, onChange, error, hint, placeholder }: TagInputProps) {
  const id = useId()
  const [draft, setDraft] = useState('')

  const add = (raw: string) => {
    const known = new Set(value.map((tag) => tag.toLowerCase()))
    const added: string[] = []
    for (const part of raw.split(',')) {
      const tag = part.trim()
      if (tag && !known.has(tag.toLowerCase())) {
        known.add(tag.toLowerCase())
        added.push(tag)
      }
    }
    if (added.length > 0) onChange([...value, ...added])
    setDraft('')
  }

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault() // Enter must not submit the whole form
      add(draft)
    } else if (event.key === 'Backspace' && draft === '' && value.length > 0) {
      onChange(value.slice(0, -1))
    }
  }

  return (
    <FieldShell id={id} label={label} error={error} hint={hint}>
      {value.length > 0 && (
        <ul className="tags" aria-label={label}>
          {value.map((tag) => (
            <li key={tag} className="tag">
              <span>{tag}</span>
              <button
                type="button"
                aria-label={`Retirer ${tag}`}
                onClick={() => onChange(value.filter((item) => item !== tag))}
              >
                <X size={14} aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      )}
      <input
        id={id}
        value={draft}
        placeholder={placeholder ?? 'Ajouter puis Entrée'}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={onKeyDown}
        onBlur={() => add(draft)}
      />
    </FieldShell>
  )
}
