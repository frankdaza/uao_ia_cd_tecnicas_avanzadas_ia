import { z } from 'zod'

/** Respuesta de GET /api/salud (TAAM, proyecto-2). */
export const SaludSchema = z.object({
  estado: z.string(),
  version: z.string(),
  proyecto: z.string(),
})
export type Salud = z.infer<typeof SaludSchema>

/** Cuerpo de POST /api/auth/staff/login */
export const StaffLoginBodySchema = z.object({
  email: z.string().email(),
  password: z.string().min(8).max(256),
})

export type StaffLoginBody = z.infer<typeof StaffLoginBodySchema>

/** Respuesta JWT staff (TASK-105). */
export const StaffLoginResponseSchema = z.object({
  access_token: z.string().min(1),
  token_type: z.string(),
  expira_en_seg: z.number().int().positive(),
  rol: z.string(),
  nombre: z.string(),
})

export type StaffLoginResponse = z.infer<typeof StaffLoginResponseSchema>
