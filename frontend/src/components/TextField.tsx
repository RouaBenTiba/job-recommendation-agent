import { useId, type InputHTMLAttributes, type Ref, type TextareaHTMLAttributes } from 'react'
import { FieldShell } from './FieldShell'

interface CommonProps {
  label: string
  error?: string
  hint?: string
}

type TextFieldProps = CommonProps &
  InputHTMLAttributes<HTMLInputElement> & { ref?: Ref<HTMLInputElement> }

export function TextField({ label, error, hint, ...input }: TextFieldProps) {
  const id = useId()
  return (
    <FieldShell id={id} label={label} error={error} hint={hint}>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        {...input}
      />
    </FieldShell>
  )
}

type TextAreaProps = CommonProps &
  TextareaHTMLAttributes<HTMLTextAreaElement> & { ref?: Ref<HTMLTextAreaElement> }

export function TextArea({ label, error, hint, ...textarea }: TextAreaProps) {
  const id = useId()
  return (
    <FieldShell id={id} label={label} error={error} hint={hint}>
      <textarea
        id={id}
        rows={4}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
        {...textarea}
      />
    </FieldShell>
  )
}
