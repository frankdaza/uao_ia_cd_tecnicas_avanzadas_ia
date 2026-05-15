import { describe, it, expect } from 'vitest'
import {
  SaludSchema,
  AgentePeticionSchema,
  EventoAgenteSseSchema,
  SesionRespuestaSchema,
  HistorialSesionRespuestaSchema,
} from '@/lib/schemas'

describe('Schemas Zod', () => {
  it('valida Salud correctamente', () => {
    const data = {
      estado: 'ok',
      version: '0.1.0',
      agente_mock_llm: false,
    }
    expect(() => SaludSchema.parse(data)).not.toThrow()
  })

  it('acepta Salud sin agente_mock_llm', () => {
    expect(() => SaludSchema.parse({ estado: 'ok', version: '0.1.0' })).not.toThrow()
  })

  it('valida evento SSE agente tipo token', () => {
    const evento = { tipo: 'token', motor: 'agente', texto: 'La Fundación' }
    const resultado = EventoAgenteSseSchema.safeParse(evento)
    expect(resultado.success).toBe(true)
  })

  it('rechaza evento SSE agente con tipo desconocido', () => {
    const evento = { tipo: 'desconocido', motor: 'agente' }
    const resultado = EventoAgenteSseSchema.safeParse(evento)
    expect(resultado.success).toBe(false)
  })

  it('valida AgentePeticion con primer_turno por defecto', () => {
    const data = {
      session_id: 'user:550e8400-e29b-41d4-a716-446655440000',
      pregunta: '¿Cuál es la misión?',
    }
    const parsed = AgentePeticionSchema.parse(data)
    expect(parsed.primer_turno).toBe(false)
  })

  it('rechaza AgentePeticion con pregunta vacía', () => {
    expect(() =>
      AgentePeticionSchema.parse({
        session_id: 'user:550e8400-e29b-41d4-a716-446655440000',
        pregunta: '',
      }),
    ).toThrow()
  })

  it('valida SesionRespuesta alineada al backend', () => {
    const data = {
      usuario_id: '550e8400-e29b-41d4-a716-446655440000',
      session_id: 'user:550e8400-e29b-41d4-a716-446655440000',
      nombre: 'María Pérez',
      ya_existia: false,
      ultimo_mensaje_at: null,
    }
    const parsed = SesionRespuestaSchema.parse(data)
    expect(parsed.session_id).toContain('user:')
  })

  it('valida HistorialSesionRespuesta', () => {
    const data = {
      mensajes: [{ rol: 'human' as const, contenido: 'Hola', creado_en: null }],
    }
    expect(() => HistorialSesionRespuestaSchema.parse(data)).not.toThrow()
  })
})
