import { FileUp } from 'lucide-react'
import { useRef, useState, type DragEvent } from 'react'
import { MAX_CV_MB } from '../lib/cvFile'

interface CvDropzoneProps {
  onFiles: (files: File[]) => void
  disabled?: boolean
}

/** Drop a PDF here, or pick one with the button (keyboard and screen reader friendly). */
export function CvDropzone({ onFiles, disabled = false }: CvDropzoneProps) {
  const input = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragging(false)
    if (!disabled) onFiles(Array.from(event.dataTransfer.files))
  }

  const classes = ['dropzone', dragging ? 'is-dragging' : '', disabled ? 'is-disabled' : '']
    .filter(Boolean)
    .join(' ')

  return (
    <div
      className={classes}
      role="group"
      aria-label="Zone de dépôt du CV"
      onDragOver={(event) => {
        event.preventDefault()
        if (!disabled) setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
    >
      <FileUp size={36} aria-hidden="true" />
      <p className="dropzone-title">Glissez votre CV ici</p>
      <p className="muted">PDF, {MAX_CV_MB} Mo maximum</p>
      <button
        type="button"
        className="secondary"
        disabled={disabled}
        onClick={() => input.current?.click()}
      >
        Choisir un fichier
      </button>
      <input
        ref={input}
        className="visually-hidden"
        type="file"
        accept="application/pdf,.pdf"
        aria-label="Fichier PDF du CV"
        disabled={disabled}
        tabIndex={-1}
        onChange={(event) => {
          onFiles(Array.from(event.target.files ?? []))
          event.target.value = '' // the same file can be chosen again after an error
        }}
      />
    </div>
  )
}
