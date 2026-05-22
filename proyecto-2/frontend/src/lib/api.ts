import type { ZodType } from 'zod'
import type { Salud } from './schemas'
import { SaludSchema } from './schemas'

const BASE = '/api'

async function parseJson<T>(res: Response, schema: ZodType<T>): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `HTTP ${res.status}`)
  }
  const data: unknown = await res.json()
  return schema.parse(data)
}

/** Health-check del backend TAAM (proxy Vite → :8001 en dev). */
export async function getSalud(): Promise<Salud> {
  const res = await fetch(`${BASE}/salud`)
  return parseJson(res, SaludSchema)
}
