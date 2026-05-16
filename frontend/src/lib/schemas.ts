import { z } from 'zod'

/* ----------------------------------------------------------------
   Módulo 2 — agente: petición y eventos SSE (/api/agente/stream)
   ---------------------------------------------------------------- */

export const AgentePeticionSchema = z.object({
  session_id: z.string().min(1).max(256),
  pregunta: z.string().min(1),
  primer_turno: z.boolean().default(false),
})
export type AgentePeticion = z.infer<typeof AgentePeticionSchema>

/** Chunk RAG denso (Qdrant); el backend puede incluir campos extra. */
export const RagChunkSchema = z
  .object({
    archivo: z.string().optional(),
    titulo: z.string().optional(),
    source_url: z.string().optional(),
    score: z.coerce.number().optional(),
    score_denso: z.coerce.number().optional(),
    score_final: z.coerce.number().optional(),
    chunk_index: z.coerce.number().optional(),
  })
  .passthrough()
export type RagChunk = z.infer<typeof RagChunkSchema>

export const ListadoItemSchema = z.object({
  nombre: z.string(),
  source_url: z.string().optional(),
  especialidad: z.array(z.string()).optional(),
  sedes: z.array(z.string()).optional(),
  archivo: z.string().optional(),
})
export type ListadoItem = z.infer<typeof ListadoItemSchema>

export const ResultadoListadoSseSchema = z.object({
  conteo: z.coerce.number().optional(),
  muestra_truncada: z.boolean().optional(),
  items: z.array(z.unknown()).optional(),
  filtros_aplicados: z.record(z.string(), z.unknown()).optional(),
})
export type ResultadoListadoSse = z.infer<typeof ResultadoListadoSseSchema>

export const EventoPensamientoSchema = z.object({
  tipo: z.literal('pensamiento'),
  herramienta_candidata: z.string(),
  razon: z.string().default(''),
  argumentos_resumidos: z.record(z.string(), z.unknown()).optional(),
})
export type EventoPensamiento = z.infer<typeof EventoPensamientoSchema>

export const EventoHerramientaSchema = z.object({
  tipo: z.literal('herramienta'),
  nombre: z.string(),
  latencia_ms: z.coerce.number().int().nonnegative(),
  faq_match_encontrado: z.boolean().optional(),
  faq_umbral_match: z.number().optional(),
  faq_consulta_ejecutada: z.string().optional(),
  resultado_listado: ResultadoListadoSseSchema.optional(),
})
export type EventoHerramienta = z.infer<typeof EventoHerramientaSchema>

export const EventoTokenAgenteSchema = z.object({
  tipo: z.literal('token'),
  motor: z.string(),
  texto: z.string(),
})
export type EventoTokenAgente = z.infer<typeof EventoTokenAgenteSchema>

export const EventoFuentesAgenteSchema = z.object({
  tipo: z.literal('fuentes'),
  chunks: z
    .array(z.unknown())
    .default([])
    .transform((arr) =>
      arr.map((item) => RagChunkSchema.safeParse(item)).flatMap((r) => (r.success ? [r.data] : [])),
    ),
})
export type EventoFuentesAgente = z.infer<typeof EventoFuentesAgenteSchema>

export const EventoFinalAgenteSchema = z.object({
  tipo: z.literal('final'),
  motor: z.string(),
  texto: z.string(),
  latencia_ms: z.coerce.number().int().nonnegative(),
  modelo: z.string(),
  metricas: z.record(z.string(), z.unknown()).nullable().optional(),
})
export type EventoFinalAgente = z.infer<typeof EventoFinalAgenteSchema>

export const EventoErrorAgenteSchema = z.object({
  tipo: z.literal('error'),
  codigo: z.string().default('error'),
  mensaje: z.string(),
  motor: z.string(),
})
export type EventoErrorAgente = z.infer<typeof EventoErrorAgenteSchema>

export const EventoAgenteSseSchema = z.discriminatedUnion('tipo', [
  EventoPensamientoSchema,
  EventoHerramientaSchema,
  EventoTokenAgenteSchema,
  EventoFuentesAgenteSchema,
  EventoFinalAgenteSchema,
  EventoErrorAgenteSchema,
])
export type EventoAgenteSse = z.infer<typeof EventoAgenteSseSchema>

/* ----------------------------------------------------------------
   Health check
   ---------------------------------------------------------------- */

export const SaludSchema = z.object({
  estado: z.string(),
  version: z.string(),
  agente_mock_llm: z.boolean().nullish(),
})
export type Salud = z.infer<typeof SaludSchema>

/* ----------------------------------------------------------------
   Módulo 2: sesión (POST /api/sesiones, historial, cierre)
   ---------------------------------------------------------------- */

export const SesionPeticionSchema = z.object({
  documento_identidad: z.string().min(1).max(128),
  nombre: z.string().min(1).max(512),
})
export type SesionPeticion = z.infer<typeof SesionPeticionSchema>

export const SesionRespuestaSchema = z.object({
  usuario_id: z.string().uuid(),
  session_id: z.string().min(1).max(256),
  nombre: z.string(),
  ya_existia: z.boolean(),
  ultimo_mensaje_at: z.union([z.string(), z.null()]).optional(),
})
export type SesionRespuesta = z.infer<typeof SesionRespuestaSchema>

/** Metadatos del turno del agente M2 en GET /api/sesiones/actual/historial (TASK-94). */
export const MetadataTurnoHistorialSchema = z.object({
  motor: z.string().optional(),
  herramienta_efectiva: z.string().nullable().optional(),
  pensamientos: z.array(z.record(z.string(), z.unknown())).optional(),
  fuentes: z
    .array(z.unknown())
    .nullish()
    .transform((arr) =>
      (arr ?? []).map((item) => RagChunkSchema.safeParse(item)).flatMap((r) => (r.success ? [r.data] : [])),
    ),
  recortado: z.boolean().nullable().optional(),
})
export type MetadataTurnoHistorial = z.infer<typeof MetadataTurnoHistorialSchema>

export const HistorialMensajeSchema = z.object({
  rol: z.enum(['human', 'ai', 'system', 'tool']),
  /** LangChain puede serializar contenido ausente; el cliente normaliza a cadena vacía. */
  contenido: z.preprocess((v) => (v === null || v === undefined ? '' : v), z.string()),
  creado_en: z.union([z.string(), z.null()]).optional(),
  /** FastAPI suele serializar None como JSON null; Zod .optional() no acepta null si la clave existe. */
  metadata_turno: MetadataTurnoHistorialSchema.nullish(),
})
export type HistorialMensaje = z.infer<typeof HistorialMensajeSchema>

export const HistorialSesionRespuestaSchema = z.object({
  mensajes: z.array(HistorialMensajeSchema),
})
export type HistorialSesionRespuesta = z.infer<typeof HistorialSesionRespuestaSchema>

export const SesionCierreRespuestaSchema = z.object({
  ok: z.boolean(),
  mensaje: z.string(),
})
export type SesionCierreRespuesta = z.infer<typeof SesionCierreRespuestaSchema>

export const BorradoUltimoTurnoRespuestaSchema = z.object({
  ok: z.boolean(),
  filas_borradas: z.number().int().min(0).max(2),
})
export type BorradoUltimoTurnoRespuesta = z.infer<typeof BorradoUltimoTurnoRespuestaSchema>
