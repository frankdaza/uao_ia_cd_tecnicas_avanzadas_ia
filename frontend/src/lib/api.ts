/**
 * Cliente HTTP tipado para los endpoints sincrónicos del API FastAPI.
 * Para streaming SSE usar sseClient.ts.
 */

import type {
  ModelosRespuesta,
  PromptDefecto,
  QaPeticion,
  QaRespuesta,
  RecargaRespuesta,
  Salud,
} from './schemas'
import {
  ModelosRespuestaSchema,
  PromptDefectoSchema,
  QaRespuestaSchema,
  RecargaRespuestaSchema,
  SaludSchema,
} from './schemas'

const BASE = '/api'

class ApiError extends Error {
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

/** Lista los modelos disponibles por motor. */
export async function getModelos(): Promise<ModelosRespuesta> {
  const res = await fetch(`${BASE}/modelos`)
  return parseJson(res, ModelosRespuestaSchema)
}

/** Obtiene el prompt de sistema predeterminado. */
export async function getPromptDefecto(): Promise<PromptDefecto> {
  const res = await fetch(`${BASE}/prompt-defecto`)
  return parseJson(res, PromptDefectoSchema)
}

/** Recarga el índice BM25. */
export async function postRecargarCorpus(): Promise<RecargaRespuesta> {
  const res = await fetch(`${BASE}/recargar-corpus`, { method: 'POST' })
  return parseJson(res, RecargaRespuestaSchema)
}

/** Consulta sincrónica al pipeline Q&A. */
export async function postQa(peticion: QaPeticion): Promise<QaRespuesta> {
  const res = await fetch(`${BASE}/qa`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(peticion),
  })
  return parseJson(res, QaRespuestaSchema)
}

export { ApiError }
