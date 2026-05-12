import { describe, it, expect } from 'vitest'
import { ModelosRespuestaSchema, EventoSseSchema, QaPeticionSchema } from '@/lib/schemas'

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

  it('valida evento SSE tipo token', () => {
    const evento = { tipo: 'token', motor: 'ollama', texto: 'La Fundación' }
    const resultado = EventoSseSchema.safeParse(evento)
    expect(resultado.success).toBe(true)
  })

  it('rechaza evento SSE con tipo desconocido', () => {
    const evento = { tipo: 'desconocido', motor: 'ollama' }
    const resultado = EventoSseSchema.safeParse(evento)
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
})
