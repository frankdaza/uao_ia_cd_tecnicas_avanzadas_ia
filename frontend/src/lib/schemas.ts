import { z } from 'zod'

/* ----------------------------------------------------------------
   Modelos disponibles
   ---------------------------------------------------------------- */

export const ModelosRespuestaSchema = z.object({
  modelos_ollama: z.array(z.string()),
  modelos_openai: z.array(z.string()),
  openai_disponible: z.boolean(),
})
export type ModelosRespuesta = z.infer<typeof ModelosRespuestaSchema>

/* ----------------------------------------------------------------
   Fuentes BM25
   ---------------------------------------------------------------- */

export const FuenteBm25Schema = z.object({
  archivo: z.string(),
  titulo: z.string(),
  source_url: z.string(),
  score: z.number(),
})
export type FuenteBm25 = z.infer<typeof FuenteBm25Schema>

/* ----------------------------------------------------------------
   Request Q&A
   ---------------------------------------------------------------- */

export const QaPeticionSchema = z.object({
  pregunta: z.string().min(1),
  prompt_sistema: z.string().nullable().optional(),
  modelo_openai: z.string().default('gpt-4o-mini'),
  max_tokens_openai: z.number().int().positive().nullable().optional(),
  temperatura: z.number().min(0).max(2).default(0.2),
  top_p: z.number().min(0).max(1).default(1),
})
export type QaPeticion = z.infer<typeof QaPeticionSchema>

/* ----------------------------------------------------------------
   Response Q&A sincrónico
   ---------------------------------------------------------------- */

export const MetadatosMotorSchema = z.object({
  modelo: z.string(),
  latencia_ms: z.number(),
})
export type MetadatosMotor = z.infer<typeof MetadatosMotorSchema>

export const QaRespuestaSchema = z.object({
  texto_ollama: z.string().nullable(),
  texto_openai: z.string().nullable(),
  fuentes: z.array(FuenteBm25Schema),
  metadatos_ollama: MetadatosMotorSchema.nullable(),
  metadatos_openai: MetadatosMotorSchema.nullable(),
})
export type QaRespuesta = z.infer<typeof QaRespuestaSchema>

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
    chunk_index: z.coerce.number().optional(),
  })
  .passthrough()
export type RagChunk = z.infer<typeof RagChunkSchema>

export const EventoPensamientoSchema = z.object({
  tipo: z.literal('pensamiento'),
  herramienta_candidata: z.string(),
  razon: z.string().default(''),
})
export type EventoPensamiento = z.infer<typeof EventoPensamientoSchema>

export const EventoHerramientaSchema = z.object({
  tipo: z.literal('herramienta'),
  nombre: z.string(),
  latencia_ms: z.number().int().nonnegative(),
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
  latencia_ms: z.number().int().nonnegative(),
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
})
export type Salud = z.infer<typeof SaludSchema>

/* ----------------------------------------------------------------
   Prompt por defecto
   ---------------------------------------------------------------- */

export const PromptDefectoSchema = z.object({
  prompt_sistema: z.string(),
})
export type PromptDefecto = z.infer<typeof PromptDefectoSchema>

/* ----------------------------------------------------------------
   Recarga de corpus
   ---------------------------------------------------------------- */

export const RecargaRespuestaSchema = z.object({
  mensaje: z.string(),
})
export type RecargaRespuesta = z.infer<typeof RecargaRespuestaSchema>

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

export const HistorialMensajeSchema = z.object({
  rol: z.enum(['human', 'ai', 'system', 'tool']),
  contenido: z.string(),
  creado_en: z.union([z.string(), z.null()]).optional(),
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
