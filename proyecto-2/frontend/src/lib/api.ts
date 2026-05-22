import type { ZodType } from 'zod'
import { getAccessToken } from './authStorage'
import type { Salud, StaffLoginBody, StaffLoginResponse } from './schemas'
import { SaludSchema, StaffLoginResponseSchema } from './schemas'

const BASE = '/api'

type AuthInvalidCallback = () => void
let authInvalidHandler: AuthInvalidCallback | null = null

/** Limpia sesión local cuando una petición REST devuelve 401/403 (JWT expirado o inválido). */
export function setAuthInvalidHandler(handler: AuthInvalidCallback | null): void {
  authInvalidHandler = handler
}

export class ApiError extends Error {
  readonly status: number
  readonly detail: string | undefined

  constructor(message: string, status: number, detail?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function parseJson<T>(response: Response, schema: ZodType<T>): Promise<T> {
  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      authInvalidHandler?.()
    }
    let detail: string | undefined
    try {
      const body = (await response.json()) as { detail?: string }
      detail = typeof body?.detail === 'string' ? body.detail : undefined
    } catch {
      //
    }
    throw new ApiError(
      detail ?? `Error del servidor: ${response.status}`,
      response.status,
      detail,
    )
  }
  const json: unknown = await response.json()
  return schema.parse(json)
}

/**
 * Fetch autenticado: adjunta ``Authorization: Bearer`` si hay token en sessionStorage.
 */
export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers)
  const token = getAccessToken()
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  if (init?.body != null && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  return fetch(`${BASE}${path}`, { ...init, headers })
}

/** Health-check del backend TAAM (proxy Vite → :8001 en dev). */
export async function getSalud(): Promise<Salud> {
  const res = await fetch(`${BASE}/salud`)
  return parseJson(res, SaludSchema)
}

/** Inicio de sesión staff; no requiere Bearer previo. */
export async function postStaffLogin(body: StaffLoginBody): Promise<StaffLoginResponse> {
  const res = await fetch(`${BASE}/auth/staff/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return parseJson(res, StaffLoginResponseSchema)
}
