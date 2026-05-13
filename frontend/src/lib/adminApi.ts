/**
 * Cliente HTTP del panel administrativo M2 (cabecera ``X-Admin-Key``).
 */

import { ApiError } from './api'
import { emitirAdminNoAutorizado } from './adminUnauthorized'
import {
  AdminConfigEstadoSchema,
  type AdminConfigEstado,
  AdminMetricasSchema,
  type AdminMetricas,
  AdminUsuariosListadoSchema,
  type AdminUsuariosListado,
} from './adminSchemas'

const BASE = '/api'
export const ADMIN_KEY_HEADER = 'X-Admin-Key'

function headersAdmin(adminKey: string, extra?: Record<string, string>) {
  return {
    [ADMIN_KEY_HEADER]: adminKey,
    ...extra,
  }
}

type OpcionesParseAdmin = {
  /** Si es true, no se emite evento global ante 401 (p. ej. verificación en pantalla de acceso). */
  silenciarEvento401?: boolean
}

async function parseJson<T>(
  response: Response,
  schema: { parse: (v: unknown) => T },
  opciones?: OpcionesParseAdmin,
): Promise<T> {
  if (!response.ok) {
    let detail: string | undefined
    try {
      const body = (await response.json()) as { detail?: string | string[] }
      if (typeof body?.detail === 'string') detail = body.detail
      else if (Array.isArray(body?.detail)) detail = body.detail.map((x) => String(x)).join('; ')
    } catch {
      // ignore
    }
    if (response.status === 401 && !opciones?.silenciarEvento401) {
      emitirAdminNoAutorizado()
    }
    throw new ApiError(detail ?? `Error del servidor: ${response.status}`, response.status, detail)
  }
  const json = await response.json()
  return schema.parse(json)
}

export async function getAdminConfig(adminKey: string): Promise<AdminConfigEstado> {
  const res = await fetch(`${BASE}/admin/config`, { headers: headersAdmin(adminKey) })
  return parseJson(res, AdminConfigEstadoSchema)
}

/**
 * Comprueba la clave contra ``GET /api/admin/config`` sin disparar el flujo de sesión caducada (401).
 */
export async function verificarClaveAdministracion(adminKey: string): Promise<AdminConfigEstado> {
  const res = await fetch(`${BASE}/admin/config`, { headers: headersAdmin(adminKey) })
  return parseJson(res, AdminConfigEstadoSchema, { silenciarEvento401: true })
}

export async function patchAdminConfig(
  adminKey: string,
  body: Record<string, unknown>,
): Promise<AdminConfigEstado> {
  const res = await fetch(`${BASE}/admin/config`, {
    method: 'PATCH',
    headers: headersAdmin(adminKey, { 'Content-Type': 'application/json' }),
    body: JSON.stringify(body),
  })
  return parseJson(res, AdminConfigEstadoSchema)
}

export async function getAdminMetricas(adminKey: string): Promise<AdminMetricas> {
  const res = await fetch(`${BASE}/admin/metricas/resumen`, { headers: headersAdmin(adminKey) })
  return parseJson(res, AdminMetricasSchema)
}

export async function getAdminUsuarios(
  adminKey: string,
  params: { limit: number; offset: number },
): Promise<AdminUsuariosListado> {
  const q = new URLSearchParams({
    limit: String(params.limit),
    offset: String(params.offset),
  })
  const res = await fetch(`${BASE}/admin/usuarios?${q.toString()}`, { headers: headersAdmin(adminKey) })
  return parseJson(res, AdminUsuariosListadoSchema)
}
