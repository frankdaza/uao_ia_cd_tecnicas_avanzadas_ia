/**
 * Cliente HTTP tipado para los endpoints sincrónicos del API FastAPI.
 * Para streaming SSE usar sseClient.ts.
 */

import type {
  HistorialSesionRespuesta,
  Salud,
  SesionCierreRespuesta,
  SesionPeticion,
  SesionRespuesta,
  BorradoUltimoTurnoRespuesta,
} from './schemas'
import {
  HistorialSesionRespuestaSchema,
  SaludSchema,
  SesionCierreRespuestaSchema,
  SesionRespuestaSchema,
  BorradoUltimoTurnoRespuestaSchema,
} from './schemas'

const BASE = '/api'

/** Cabecera opcional alineada con `src/api/dependencias.py` (`X-Session-Id`). */
export const SESSION_HEADER_NAME = 'X-Session-Id'

const DEFAULT_CREDENTIALS: RequestCredentials = 'include'

type AuthInvalidCallback = () => void
let authInvalidHandler: AuthInvalidCallback | null = null

/** Registra limpieza de sesión local cuando una petición REST devuelve 401/403 (p. ej. cookie expirada). */
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

async function parseJson<T>(response: Response, schema: { parse: (v: unknown) => T }): Promise<T> {
  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      authInvalidHandler?.()
    }
    let detail: string | undefined
    try {
      const body = (await response.json()) as { detail?: string }
      detail = body?.detail
    } catch {
      // ignore
    }
    throw new ApiError(
      detail ?? `Error del servidor: ${response.status}`,
      response.status,
      detail,
    )
  }
  const json = await response.json()
  return schema.parse(json)
}

/** Verifica que el servidor esté en funcionamiento. */
export async function getSalud(): Promise<Salud> {
  const res = await fetch(`${BASE}/salud`)
  return parseJson(res, SaludSchema)
}

/**
 * Inicia sesión M2: envía documento y nombre; el servidor fija cookie HTTP-only `fvl_session_id`.
 */
export async function postIniciarSesion(peticion: SesionPeticion): Promise<SesionRespuesta> {
  const res = await fetch(`${BASE}/sesiones`, {
    method: 'POST',
    credentials: DEFAULT_CREDENTIALS,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(peticion),
  })
  return parseJson(res, SesionRespuestaSchema)
}

/**
 * Historial de la sesión actual (cookie o cabecera `X-Session-Id`).
 */
export async function getHistorialSesion(sessionId?: string): Promise<HistorialSesionRespuesta> {
  const res = await fetch(`${BASE}/sesiones/actual/historial`, {
    method: 'GET',
    credentials: DEFAULT_CREDENTIALS,
    headers: sessionId ? { [SESSION_HEADER_NAME]: sessionId } : {},
  })
  return parseJson(res, HistorialSesionRespuestaSchema)
}

/** Elimina el último turno persistido (human + ai) antes de regenerar en el cliente. */
export async function deleteUltimoTurno(sessionId?: string): Promise<BorradoUltimoTurnoRespuesta> {
  const res = await fetch(`${BASE}/sesiones/actual/ultimo-turno`, {
    method: 'DELETE',
    credentials: DEFAULT_CREDENTIALS,
    headers: sessionId ? { [SESSION_HEADER_NAME]: sessionId } : {},
  })
  return parseJson(res, BorradoUltimoTurnoRespuestaSchema)
}

/** Cierra sesión en el servidor (borra cookie en la respuesta). */
export async function postCerrarSesion(sessionId?: string): Promise<SesionCierreRespuesta> {
  const res = await fetch(`${BASE}/sesiones/cerrar`, {
    method: 'POST',
    credentials: DEFAULT_CREDENTIALS,
    headers: sessionId ? { [SESSION_HEADER_NAME]: sessionId } : {},
  })
  return parseJson(res, SesionCierreRespuestaSchema)
}
