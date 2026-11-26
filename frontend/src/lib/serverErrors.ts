import type { FieldValues, Path, UseFormSetError } from 'react-hook-form'
import type { FieldError } from '../api/client'

/**
 * Show the field errors returned by the backend (`errors: [{field, message}]`) under the right
 * fields. A path ending with a list index ("skills.2") is attached to the list itself, because
 * tag lists display one error for the whole list.
 */
export function applyServerErrors<T extends FieldValues>(
  setError: UseFormSetError<T>,
  errors: FieldError[],
): boolean {
  let applied = false
  for (const error of errors) {
    const target = error.field.replace(/(\.\d+)+$/, '')
    if (!target) continue
    setError(target as Path<T>, { type: 'server', message: error.message })
    applied = true
  }
  return applied
}
