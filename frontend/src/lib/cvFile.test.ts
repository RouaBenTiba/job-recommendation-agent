import { describe, expect, it } from 'vitest'
import { formatFileSize, MAX_CV_BYTES, validateCvFiles } from './cvFile'

const pdf = (name = 'cv.pdf', size = 1000, type = 'application/pdf') =>
  new File([new Uint8Array(size)], name, { type })

describe('validateCvFiles', () => {
  it('accepts a PDF', () => {
    expect(validateCvFiles([pdf()])).toBeNull()
  })

  it('accepts a PDF whose type is not reported by the system', () => {
    expect(validateCvFiles([pdf('CV.PDF', 1000, '')])).toBeNull()
  })

  it('refuses other formats', () => {
    expect(validateCvFiles([pdf('cv.docx', 1000, 'application/msword')])).toBe(
      'Seuls les fichiers PDF sont acceptés.',
    )
  })

  it('refuses an empty file and one that is too large', () => {
    expect(validateCvFiles([pdf('cv.pdf', 0)])).toBe('Le fichier est vide.')
    expect(validateCvFiles([pdf('cv.pdf', MAX_CV_BYTES + 1)])).toBe(
      'Le fichier dépasse la taille maximale de 5 Mo.',
    )
    expect(validateCvFiles([pdf('cv.pdf', MAX_CV_BYTES)])).toBeNull()
  })

  it('refuses several files at once, and no file', () => {
    expect(validateCvFiles([pdf(), pdf('b.pdf')])).toBe('Importez un seul fichier à la fois.')
    expect(validateCvFiles([])).toBe('Aucun fichier sélectionné.')
  })
})

describe('formatFileSize', () => {
  it('uses Ko below one megabyte and Mo above', () => {
    expect(formatFileSize(1)).toBe('1 Ko')
    expect(formatFileSize(340 * 1024)).toBe('340 Ko')
    expect(formatFileSize(1.5 * 1024 * 1024)).toBe('1,5 Mo')
  })
})
