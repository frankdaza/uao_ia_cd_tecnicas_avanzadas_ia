import { z } from 'zod'

/** Respuesta GET/PATCH ``/api/admin/config`` (valores efectivos). */
export const AdminConfigEstadoSchema = z.object({
  version: z.number().int().nonnegative(),
  updated_at: z.string().nullable().optional(),
  modelo_llm_router: z.string(),
  modelo_llm_compositor: z.string(),
  temperatura_router: z.number(),
  temperatura_compositor: z.number(),
  top_p_router: z.number().nullable().optional(),
  top_p_compositor: z.number().nullable().optional(),
  model_kwargs_router: z.record(z.string(), z.unknown()).optional().default({}),
  model_kwargs_compositor: z.record(z.string(), z.unknown()).optional().default({}),
  meta_prompt: z.record(z.string(), z.unknown()),
  prompt_institucional: z.string(),
  rag_top_k: z.number().int().min(1).max(50),
  rag_score_minimo: z.number().min(0).max(1),
  rag_top_k_inicial: z.number().int().min(1).max(200),
  rag_mmr_habilitado: z.boolean(),
  rag_mmr_lambda: z.number().min(0).max(1),
  rag_reranker_habilitado: z.boolean(),
  rag_reranker_modelo: z.string().max(256),
  rag_reranker_top_n_entrada: z.number().int().min(1).max(50),
  historial_turnos_max: z.number().int().min(1).max(200),
  nota_precedencia: z.string().optional(),
})
export type AdminConfigEstado = z.infer<typeof AdminConfigEstadoSchema>

export const AdminMetricasSchema = z.object({
  usuarios_total: z.number().int().nonnegative(),
  usuarios_activos_ultimos_7_dias: z.number().int().nonnegative(),
  sesiones_estimadas: z.number().int().nonnegative(),
})
export type AdminMetricas = z.infer<typeof AdminMetricasSchema>

export const AdminUsuarioItemSchema = z.object({
  id: z.string().uuid(),
  nombre: z.string(),
  documento_identidad_enmascarado: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
  last_login_at: z.string().nullable().optional(),
})
export type AdminUsuarioItem = z.infer<typeof AdminUsuarioItemSchema>

export const AdminUsuariosListadoSchema = z.object({
  items: z.array(AdminUsuarioItemSchema),
  total: z.number().int().nonnegative(),
  limit: z.number().int().positive(),
  offset: z.number().int().nonnegative(),
})
export type AdminUsuariosListado = z.infer<typeof AdminUsuariosListadoSchema>
