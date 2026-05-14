import { describe, expect, it } from 'vitest'
import { AdminConfigEstadoSchema, AdminMetricasSchema, AdminUsuariosListadoSchema } from './adminSchemas'

describe('AdminConfigEstadoSchema', () => {
  it('parsea respuesta minima del backend', () => {
    const raw = {
      version: 0,
      modelo_llm_router: 'gpt-4o-mini',
      modelo_llm_compositor: 'gpt-4o-mini',
      temperatura_router: 0,
      temperatura_compositor: 0.2,
      rag_top_k: 5,
      rag_score_minimo: 0.25,
      meta_prompt: { version: 1 },
      prompt_institucional: 'x'.repeat(80),
    }
    const r = AdminConfigEstadoSchema.parse(raw)
    expect(r.version).toBe(0)
    expect(r.model_kwargs_router).toEqual({})
  })
})

describe('AdminMetricasSchema', () => {
  it('parsea metricas', () => {
    const r = AdminMetricasSchema.parse({
      usuarios_total: 3,
      usuarios_activos_ultimos_7_dias: 1,
      sesiones_estimadas: 0,
    })
    expect(r.usuarios_total).toBe(3)
  })
})

describe('AdminUsuariosListadoSchema', () => {
  it('parsea listado paginado', () => {
    const r = AdminUsuariosListadoSchema.parse({
      items: [
        {
          id: '550e8400-e29b-41d4-a716-446655440000',
          nombre: 'Ana',
          documento_identidad_enmascarado: '***901',
          created_at: '2026-01-01T12:00:00Z',
          updated_at: '2026-01-02T12:00:00Z',
          last_login_at: null,
        },
      ],
      total: 1,
      limit: 15,
      offset: 0,
    })
    expect(r.items).toHaveLength(1)
    expect(r.total).toBe(1)
  })
})
