import { request } from './client'
import type { Cv, CvExtraction, Profile } from './types'

export function uploadCv(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request<Cv>('/cvs', { method: 'POST', formData })
}

/** Reads the text of the PDF (the backend answers 422 when nothing can be read). */
export const extractCv = (cvId: string) =>
  request<CvExtraction>(`/cvs/${cvId}/extract`, { method: 'POST' })

/** Asks the AI for a structured profile; creates a new profile version. */
export const buildCvProfile = (cvId: string) =>
  request<Profile>(`/cvs/${cvId}/profile`, { method: 'POST' })
