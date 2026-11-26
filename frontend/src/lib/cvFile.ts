/** Same limit as the backend (MAX_CV_SIZE_MB). */
export const MAX_CV_MB = 5
export const MAX_CV_BYTES = MAX_CV_MB * 1024 * 1024

/** Checked in the browser to answer instantly; the backend checks again (content included). */
export function validateCvFiles(files: File[]): string | null {
  if (files.length === 0) return 'Aucun fichier sélectionné.'
  if (files.length > 1) return 'Importez un seul fichier à la fois.'
  const file = files[0]
  const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
  if (!isPdf) return 'Seuls les fichiers PDF sont acceptés.'
  if (file.size === 0) return 'Le fichier est vide.'
  if (file.size > MAX_CV_BYTES) return `Le fichier dépasse la taille maximale de ${MAX_CV_MB} Mo.`
  return null
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(1).replace('.', ',')} Mo`
}
