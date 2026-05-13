import { describe, it, expect } from 'vitest'
import {
  ModelosRespuestaSchema,
  EventoAgenteSseSchema,
  QaPeticionSchema,
  SesionRespuestaSchema,
  HistorialSesionRespuestaSchema,
} from '@/lib/schemas'

describe('Schemas Zod', () => {
  it('valida ModelosRespuesta correctamente', () => {
    const data = {
      modelos_ollama: ['llama3.1:8b'],
      modelos_openai: ['gpt-4o-mini'],
      openai_disponible: true,
    }
    expect(() => ModelosRespuestaSchema.parse(data)).not.toThrow()
  })

  it('rechaza ModelosRespuesta con campo faltante', () => {
    expect(() => ModelosRespuestaSchema.parse({ modelos_ollama: [] })).toThrow()
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

  it('valida QaPeticion con valores por defecto', () => {
    const data = { pregunta: '¿Cuál es la misión?' }
    const parsed = QaPeticionSchema.parse(data)
    expect(parsed.modelo_openai).toBe('gpt-4o-mini')
    expect(parsed.temperatura).toBe(0.2)
    expect(parsed.top_p).toBe(1)
  })

  it('rechaza QaPeticion con pregunta vacía', () => {
    expect(() => QaPeticionSchema.parse({ pregunta: '' })).toThrow()
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
