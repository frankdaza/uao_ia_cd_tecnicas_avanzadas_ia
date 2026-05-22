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

/** Opción mínima para select de nuevo caso (GET /api/staff/tipos-procedimiento). */
export const TipoProcedimientoOpcionSchema = z.object({
  id: z.uuid(),
  codigo: z.string(),
  nombre: z.string(),
})

export type TipoProcedimientoOpcion = z.infer<typeof TipoProcedimientoOpcionSchema>

export const ListadoTiposProcedimientoOpcionSchema = z.object({
  items: z.array(TipoProcedimientoOpcionSchema),
})

export type ListadoTiposProcedimientoOpcion = z.infer<typeof ListadoTiposProcedimientoOpcionSchema>

/** Cuerpo de POST /api/staff/casos (UC-MVP-02). */
export const CrearCasoBodySchema = z.object({
  paciente_doc_id: z.string().min(1).max(128),
  paciente_nombre: z.string().min(1).max(512),
  tipo_procedimiento_id: z.uuid(),
  cirujano_id: z.string().min(1).max(128),
  cirujano_nombre: z.string().min(1).max(512),
  fecha_cirugia: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  notas_especificas: z.string().max(8000).optional(),
})

export type CrearCasoBody = z.infer<typeof CrearCasoBodySchema>

/** Vista de caso en listado staff. */
export const CasoSchema = z.object({
  id: z.uuid(),
  paciente_doc_id: z.string(),
  paciente_nombre: z.string(),
  tipo_procedimiento_id: z.uuid(),
  cirujano_id: z.string(),
  cirujano_nombre: z.string(),
  fecha_cirugia: z.string(),
  notas_especificas: z.string().nullable(),
  estado: z.string(),
  created_at: z.string(),
  vinculado_telegram: z.boolean(),
  codigo_emparejamiento_activo: z.string().nullable(),
})

export type Caso = z.infer<typeof CasoSchema>

export const ListadoCasosSchema = z.object({
  items: z.array(CasoSchema),
  limit: z.number().int(),
  offset: z.number().int(),
})

export type ListadoCasos = z.infer<typeof ListadoCasosSchema>

/** Respuesta de POST .../codigo-emparejamiento. */
export const CodigoEmparejamientoSchema = z.object({
  caso_id: z.uuid(),
  codigo: z.string(),
  expira_at: z.string(),
})

export type CodigoEmparejamiento = z.infer<typeof CodigoEmparejamientoSchema>
