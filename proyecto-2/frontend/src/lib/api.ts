import type { ZodType } from 'zod'
import { formatApiDetail } from './formatApiError'
import { getAccessToken } from './authStorage'
import type {
  Caso,
  CodigoEmparejamiento,
  CrearCasoBody,
  ListadoCasos,
  ListadoProcedimientos,
  ListadoTiposProcedimientoOpcion,
  Procedimiento,
  ProcedimientoMetadata,
  Salud,
  StaffLoginBody,
  StaffLoginResponse,
} from './schemas'
import {
  CasoSchema,
  CodigoEmparejamientoSchema,
  ListadoCasosSchema,
  ListadoProcedimientosSchema,
  ListadoTiposProcedimientoOpcionSchema,
  ProcedimientoSchema,
  SaludSchema,
  StaffLoginResponseSchema,
} from './schemas'

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
      const body = (await response.json()) as { detail?: unknown }
      detail = formatApiDetail(body?.detail)
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
  if (
    init?.body != null &&
    !(init.body instanceof FormData) &&
    !headers.has('Content-Type')
  ) {
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

/** Listado paginado del catálogo (UC-MVP-01). */
export async function listAdminProcedimientos(params?: {
  limit?: number
  offset?: number
}): Promise<ListadoProcedimientos> {
  const qs = new URLSearchParams()
  if (params?.limit != null) qs.set('limit', String(params.limit))
  if (params?.offset != null) qs.set('offset', String(params.offset))
  const query = qs.toString()
  const res = await apiFetch(`/admin/procedimientos${query ? `?${query}` : ''}`)
  return parseJson(res, ListadoProcedimientosSchema)
}

export async function getAdminProcedimiento(id: string): Promise<Procedimiento> {
  const res = await apiFetch(`/admin/procedimientos/${id}`)
  return parseJson(res, ProcedimientoSchema)
}

export async function createAdminProcedimiento(
  metadata: ProcedimientoMetadata,
  archivo: File,
): Promise<Procedimiento> {
  const form = new FormData()
  form.append('metadata', JSON.stringify(metadata))
  form.append('archivo', archivo, archivo.name)
  const res = await apiFetch('/admin/procedimientos', { method: 'POST', body: form })
  return parseJson(res, ProcedimientoSchema)
}

export async function patchAdminProcedimiento(
  id: string,
  opts: { metadata?: Partial<ProcedimientoMetadata>; archivo?: File },
): Promise<Procedimiento> {
  const form = new FormData()
  if (opts.metadata && Object.keys(opts.metadata).length > 0) {
    form.append('metadata', JSON.stringify(opts.metadata))
  }
  if (opts.archivo) {
    form.append('archivo', opts.archivo, opts.archivo.name)
  }
  const res = await apiFetch(`/admin/procedimientos/${id}`, { method: 'PATCH', body: form })
  return parseJson(res, ProcedimientoSchema)
}

export async function reindexAdminProcedimiento(id: string): Promise<Procedimiento> {
  const res = await apiFetch(`/admin/procedimientos/${id}/reindexar`, { method: 'POST' })
  return parseJson(res, ProcedimientoSchema)
}

/** Tipos indexados para select de nuevo caso (UC-MVP-02). */
export async function listStaffTiposProcedimiento(): Promise<ListadoTiposProcedimientoOpcion> {
  const res = await apiFetch('/staff/tipos-procedimiento?indexacion_estado=ok&limit=100')
  return parseJson(res, ListadoTiposProcedimientoOpcionSchema)
}

/** Alta de caso postoperatorio. */
export async function createStaffCaso(body: CrearCasoBody): Promise<Caso> {
  const res = await apiFetch('/staff/casos', {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return parseJson(res, CasoSchema)
}

/** Listado de casos staff. */
export async function listStaffCasos(params?: {
  estado?: 'activo' | 'cerrado'
  limit?: number
  offset?: number
}): Promise<ListadoCasos> {
  const qs = new URLSearchParams()
  if (params?.estado) qs.set('estado', params.estado)
  if (params?.limit != null) qs.set('limit', String(params.limit))
  if (params?.offset != null) qs.set('offset', String(params.offset))
  const query = qs.toString()
  const res = await apiFetch(`/staff/casos${query ? `?${query}` : ''}`)
  return parseJson(res, ListadoCasosSchema)
}

/** Genera o regenera código de emparejamiento Telegram. */
export async function generateCodigoEmparejamiento(casoId: string): Promise<CodigoEmparejamiento> {
  const res = await apiFetch(`/staff/casos/${casoId}/codigo-emparejamiento`, { method: 'POST' })
  return parseJson(res, CodigoEmparejamientoSchema)
}
