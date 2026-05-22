import { z } from 'zod'

/** Respuesta de GET /api/salud (TAAM, proyecto-2). */
export const SaludSchema = z.object({
  estado: z.string(),
  version: z.string(),
  proyecto: z.string(),
})
export type Salud = z.infer<typeof SaludSchema>
