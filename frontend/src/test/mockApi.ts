import { vi } from 'vitest'

export interface MockRequest {
  method: string
  path: string
  headers: Headers
  json: unknown
  form: URLSearchParams | null
  formData: FormData | null
  credentials: RequestCredentials | undefined
}

export interface MockReply {
  status?: number
  json?: unknown
}

type Reply = MockReply | ((request: MockRequest) => MockReply | Promise<MockReply>)

/**
 * Replaces `fetch`: no test ever reaches a real server. Keys look like "GET /auth/me"
 * (the /api/v1 prefix is removed). A request that is not declared makes the test fail.
 */
export function mockApi(routes: Record<string, Reply>) {
  const calls: MockRequest[] = []

  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const path = String(input).replace('/api/v1', '')
    const method = init?.method ?? 'GET'
    const body = init?.body
    const request: MockRequest = {
      method,
      path,
      headers: new Headers(init?.headers),
      json: typeof body === 'string' ? JSON.parse(body) : null,
      form: body instanceof URLSearchParams ? body : null,
      formData: body instanceof FormData ? body : null,
      credentials: init?.credentials,
    }
    calls.push(request)

    const route = routes[`${method} ${path}`]
    if (!route) throw new Error(`Unmocked request: ${method} ${path}`)
    const reply = typeof route === 'function' ? await route(request) : route
    const status = reply.status ?? 200
    if (status === 204) return new Response(null, { status })
    return new Response(JSON.stringify(reply.json ?? null), {
      status,
      headers: { 'Content-Type': 'application/json' },
    })
  })
  vi.stubGlobal('fetch', fetchMock)

  return {
    calls,
    to: (method: string, path: string) =>
      calls.filter((call) => call.method === method && call.path === path),
  }
}

export const USER = {
  id: 'user-1',
  email: 'roua@example.com',
  full_name: 'Roua',
  created_at: '2026-11-01T10:00:00Z',
}

export const PROFILE = {
  id: 'profile-2',
  version: 2,
  is_current: true,
  cv_id: null,
  source: 'llm',
  extraction_model: 'gemini-3.5-flash (profile_extraction_v1)',
  summary: 'Étudiante ingénieure en informatique.',
  objectives: null,
  education: [
    {
      school: 'ENIT',
      degree: 'Cycle ingénieur',
      field_of_study: null,
      start_year: 2023,
      end_year: 2026,
    },
  ],
  experiences: [
    {
      company: 'Société Exemple',
      title: 'Stagiaire',
      start: '2025-06',
      end: null,
      description: null,
      technologies: ['FastAPI'],
    },
  ],
  skills: ['Travail en équipe'],
  technologies: ['Python', 'Docker'],
  interests: [],
  created_at: '2026-11-02T09:00:00Z',
  updated_at: '2026-11-02T09:00:00Z',
}

export const VERSIONS = [
  {
    id: 'profile-1',
    version: 1,
    is_current: false,
    source: 'llm',
    extraction_model: null,
    created_at: '2026-11-01T10:00:00Z',
  },
  {
    id: 'profile-2',
    version: 2,
    is_current: true,
    source: 'manual',
    extraction_model: null,
    created_at: '2026-11-02T09:00:00Z',
  },
]

export const NO_PREFERENCES = {
  id: null,
  contract_types: [],
  locations: [],
  domains: [],
  remote_ok: false,
  willing_to_relocate: false,
  updated_at: null,
}
