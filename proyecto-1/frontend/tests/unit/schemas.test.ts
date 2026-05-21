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

  it('acepta historial con metadata_turno null en human (JSON FastAPI)', () => {
    const data = {
      mensajes: [
        { rol: 'human' as const, contenido: 'Hola', creado_en: null, metadata_turno: null },
        { rol: 'ai' as const, contenido: 'Respuesta', creado_en: null, metadata_turno: null },
        { rol: 'human' as const, contenido: 'Otra', creado_en: null, metadata_turno: null },
      ],
    }
    const parsed = HistorialSesionRespuestaSchema.parse(data)
    expect(parsed.mensajes[0].metadata_turno).toBeNull()
    expect(parsed.mensajes[1].metadata_turno).toBeNull()
    expect(parsed.mensajes[2].metadata_turno).toBeNull()
  })

  it('acepta mensaje de historial con contenido null (legacy)', () => {
    const data = {
      mensajes: [{ rol: 'human' as const, contenido: null, creado_en: null }],
    }
    const parsed = HistorialSesionRespuestaSchema.parse(data)
    expect(parsed.mensajes[0].contenido).toBe('')
  })

  it('valida HistorialSesionRespuesta con metadata_turno en mensaje ai', () => {
    const data = {
      mensajes: [
        { rol: 'human' as const, contenido: 'Pregunta', creado_en: null },
        {
          rol: 'ai' as const,
          contenido: 'Respuesta',
          creado_en: null,
          metadata_turno: {
            motor: 'agente',
            herramienta_efectiva: 'faq_estructurada',
            pensamientos: [
              { tipo: 'decision_router', herramienta: 'faq_estructurada', razon_breve: 'Razon.' },
            ],
            fuentes: [{ archivo: 'a.md', score: 0.9 }],
          },
        },
      ],
    }
    const parsed = HistorialSesionRespuestaSchema.parse(data)
    expect(parsed.mensajes[1].metadata_turno?.herramienta_efectiva).toBe('faq_estructurada')
    expect(parsed.mensajes[1].metadata_turno?.fuentes?.[0]?.archivo).toBe('a.md')
  })
})
