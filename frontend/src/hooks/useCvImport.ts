import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useState } from 'react'
import { isApiError } from '../api/client'
import { buildCvProfile, extractCv, uploadCv } from '../api/cvs'
import type { Profile } from '../api/types'
import { PROFILE_KEY, VERSIONS_KEY } from './useProfile'

export type ImportStage = 'upload' | 'extract' | 'profile'

export interface ExtractionSummary {
  pages_read: number
  page_count: number
  truncated: boolean
  characters: number
}

export type ImportState =
  | { phase: 'idle' }
  | { phase: 'running'; file: File; stage: ImportStage }
  | {
      phase: 'failed'
      file: File
      stage: ImportStage
      message: string
      retryable: boolean
      cvId: string | null
      extraction: ExtractionSummary | null
    }
  | { phase: 'done'; file: File; profile: Profile; extraction: ExtractionSummary }

interface Resume {
  cvId: string | null
  extraction: ExtractionSummary | null
}

/**
 * Upload, read the PDF, then ask the AI for the profile. When a step fails, a retry restarts
 * from that step only: an uploaded CV is never uploaded twice.
 */
export function useCvImport() {
  const client = useQueryClient()
  const [state, setState] = useState<ImportState>({ phase: 'idle' })

  const run = useCallback(
    async (file: File, from: ImportStage, resume: Resume) => {
      let stage = from
      let cvId = resume.cvId
      let extraction = resume.extraction
      try {
        if (stage === 'upload') {
          setState({ phase: 'running', file, stage })
          cvId = (await uploadCv(file)).id
          stage = 'extract'
        }
        if (stage === 'extract' && cvId) {
          setState({ phase: 'running', file, stage })
          const result = await extractCv(cvId)
          // The text itself is never kept in the browser: only what is shown to the candidate.
          extraction = {
            pages_read: result.pages_read,
            page_count: result.page_count,
            truncated: result.truncated,
            characters: result.characters,
          }
          stage = 'profile'
        }
        if (!cvId || !extraction) throw new Error('missing step')
        setState({ phase: 'running', file, stage: 'profile' })
        const profile = await buildCvProfile(cvId)
        client.setQueryData(PROFILE_KEY, profile)
        void client.invalidateQueries({ queryKey: VERSIONS_KEY })
        setState({ phase: 'done', file, profile, extraction })
      } catch (error) {
        const api = isApiError(error) ? error : null
        // Network errors and server errors may disappear on a second try; a refused file will not.
        const transient = !api || api.status === 0 || api.status >= 500
        setState({
          phase: 'failed',
          file,
          stage,
          message: api ? api.message : 'Une erreur inattendue est survenue.',
          retryable: transient,
          cvId,
          extraction,
        })
      }
    },
    [client],
  )

  const start = useCallback(
    (file: File) => {
      if (state.phase === 'running') return
      void run(file, 'upload', { cvId: null, extraction: null })
    },
    [run, state.phase],
  )

  const retry = useCallback(() => {
    if (state.phase !== 'failed' || !state.retryable) return
    void run(state.file, state.stage, { cvId: state.cvId, extraction: state.extraction })
  }, [run, state])

  const reset = useCallback(() => setState({ phase: 'idle' }), [])

  return { state, start, retry, reset }
}
