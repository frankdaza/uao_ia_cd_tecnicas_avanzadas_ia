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
   Eventos SSE
   ---------------------------------------------------------------- */

export const EventoTokenSchema = z.object({
  tipo: z.literal('token'),
  motor: z.string(),
  texto: z.string(),
})
export type EventoToken = z.infer<typeof EventoTokenSchema>

export const EventoFuentesSchema = z.object({
  tipo: z.literal('fuentes'),
  fuentes: z.array(FuenteBm25Schema),
})
export type EventoFuentes = z.infer<typeof EventoFuentesSchema>

export const EventoFinalSchema = z.object({
  tipo: z.literal('final'),
  motor: z.string(),
  texto: z.string(),
  latencia_ms: z.number(),
  modelo: z.string(),
})
export type EventoFinal = z.infer<typeof EventoFinalSchema>

export const EventoErrorSchema = z.object({
  tipo: z.literal('error'),
  motor: z.string(),
  mensaje: z.string(),
})
export type EventoError = z.infer<typeof EventoErrorSchema>

export const EventoSseSchema = z.discriminatedUnion('tipo', [
  EventoTokenSchema,
  EventoFuentesSchema,
  EventoFinalSchema,
  EventoErrorSchema,
])
export type EventoSse = z.infer<typeof EventoSseSchema>

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
