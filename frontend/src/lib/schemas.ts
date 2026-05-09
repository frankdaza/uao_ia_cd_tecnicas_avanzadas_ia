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
  usar_ollama: z.boolean().default(true),
  usar_openai: z.boolean().default(false),
  modelo_ollama: z.string().default('llama3.1:8b'),
  modelo_openai: z.string().default('gpt-4o-mini'),
  num_ctx: z.number().int().min(1024).max(131072).default(8192),
  max_tokens_openai: z.number().int().positive().nullable().optional(),
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
