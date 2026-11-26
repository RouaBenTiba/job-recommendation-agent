import { describe, expect, it } from 'vitest'
import { mockApi } from '../test/mockApi'
import { ApiError, CSRF_HEADER, request } from './client'

describe('request', () => {
  it('always sends the CSRF header and stays same-origin', async () => {
    const api = mockApi({ 'GET /auth/me': { json: { ok: true } } })
    await request('/auth/me')
    expect(api.calls[0].headers.get(CSRF_HEADER)).toBe('1')
    expect(api.calls[0].credentials).toBe('same-origin')
  })

  it('sends JSON bodies and form bodies', async () => {
    const api = mockApi({ 'PATCH /profile': { json: {} }, 'POST /auth/login': { json: {} } })
    await request('/profile', { method: 'PATCH', json: { summary: 'x' } })
    await request('/auth/login', {
      method: 'POST',
      form: { username: 'a@b.co', password: 'secret' },
    })
    expect(api.calls[0].headers.get('Content-Type')).toBe('application/json')
    expect(api.calls[0].json).toEqual({ summary: 'x' })
    expect(api.calls[1].form?.get('username')).toBe('a@b.co')
    expect(api.calls[1].form?.get('password')).toBe('secret')
  })

  it('sends files as multipart without forcing a content type', async () => {
    const api = mockApi({ 'POST /cvs': { json: {} } })
    const formData = new FormData()
    formData.append('file', new File(['%PDF-1.4'], 'cv.pdf', { type: 'application/pdf' }))
    await request('/cvs', { method: 'POST', formData })
    expect((api.calls[0].formData?.get('file') as File).name).toBe('cv.pdf')
    expect(api.calls[0].headers.get('Content-Type')).toBeNull() // the browser adds the boundary
  })

  it('returns undefined for 204 answers', async () => {
    mockApi({ 'POST /auth/logout': { status: 204 } })
    await expect(request('/auth/logout', { method: 'POST' })).resolves.toBeUndefined()
  })

  it('turns the backend error format into an ApiError with field errors', async () => {
    mockApi({
      'PATCH /profile': {
        status: 422,
        json: {
          code: 'validation_error',
          detail: 'Les données envoyées sont invalides.',
          errors: [{ field: 'skills.1', message: 'too long' }, { nonsense: true }],
        },
      },
    })
    const error = await request('/profile', { method: 'PATCH', json: {} }).catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      status: 422,
      code: 'validation_error',
      message: 'Les données envoyées sont invalides.',
      fieldErrors: [{ field: 'skills.1', message: 'too long' }],
    })
  })

  it('copes with a non-JSON error body', async () => {
    mockApi({ 'GET /profile': () => ({ status: 500, json: null }) })
    await expect(request('/profile')).rejects.toMatchObject({ status: 500, code: 'error' })
  })

  it('reports an unreachable server as a network error', async () => {
    mockApi({}) // every request throws: the server cannot be reached
    await expect(request('/auth/me')).rejects.toMatchObject({ status: 0, code: 'network_error' })
  })
})
