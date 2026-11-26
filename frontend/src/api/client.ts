export const API_BASE = '/api/v1'
/** Required by the backend on every state-changing request authenticated by the cookie. */
export const CSRF_HEADER = 'X-CSRF-Protection'

export interface FieldError {
  field: string
  message: string
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly fieldErrors: FieldError[]

  constructor(status: number, code: string, detail: string, fieldErrors: FieldError[] = []) {
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.fieldErrors = fieldErrors
  }
}

export function isApiError(error: unknown, status?: number): error is ApiError {
  return error instanceof ApiError && (status === undefined || error.status === status)
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  json?: unknown
  form?: Record<string, string>
  formData?: FormData
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function toApiError(status: number, data: unknown): ApiError {
  if (!isRecord(data)) return new ApiError(status, 'error', 'Une erreur est survenue.')
  const detail = typeof data.detail === 'string' ? data.detail : 'Une erreur est survenue.'
  const code = typeof data.code === 'string' ? data.code : 'error'
  const fieldErrors: FieldError[] = []
  if (Array.isArray(data.errors)) {
    for (const item of data.errors) {
      if (isRecord(item) && typeof item.field === 'string' && typeof item.message === 'string') {
        fieldErrors.push({ field: item.field, message: item.message })
      }
    }
  }
  return new ApiError(status, code, detail, fieldErrors)
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json', [CSRF_HEADER]: '1' }
  let body: BodyInit | undefined
  if (options.json !== undefined) {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify(options.json)
  } else if (options.form) {
    body = new URLSearchParams(options.form) // the browser sets the form content type
  } else if (options.formData) {
    body = options.formData // multipart: the browser adds the boundary, never set Content-Type here
  }

  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body,
      credentials: 'same-origin',
    })
  } catch {
    throw new ApiError(
      0,
      'network_error',
      'Impossible de joindre le serveur. Vérifiez votre connexion.',
    )
  }

  if (response.status === 204) return undefined as T
  const data: unknown = await response.json().catch(() => null)
  if (!response.ok) throw toApiError(response.status, data)
  return data as T
}
