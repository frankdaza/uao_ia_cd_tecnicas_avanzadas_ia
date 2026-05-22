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

/** Recurso de catálogo UC-MVP-01 (GET/POST/PATCH admin procedimientos). */
export const ProcedimientoSchema = z.object({
  id: z.uuid(),
  codigo: z.string(),
  nombre: z.string(),
  indexacion_estado: z.enum(['pendiente', 'ok', 'error']),
  qdrant_collection_version: z.number().int().nullable(),
  created_at: z.string(),
})

export type Procedimiento = z.infer<typeof ProcedimientoSchema>

export const ListadoProcedimientosSchema = z.object({
  items: z.array(ProcedimientoSchema),
  limit: z.number().int(),
  offset: z.number().int(),
})

export type ListadoProcedimientos = z.infer<typeof ListadoProcedimientosSchema>

/** Metadata del campo form ``metadata`` en multipart. */
export const ProcedimientoMetadataSchema = z.object({
  codigo: z
    .string()
    .min(1)
    .max(64)
    .regex(/^[A-Za-z0-9_-]+$/, 'Código: solo letras, números, guion y guion bajo.'),
  nombre: z.string().min(1).max(512),
})

export type ProcedimientoMetadata = z.infer<typeof ProcedimientoMetadataSchema>
