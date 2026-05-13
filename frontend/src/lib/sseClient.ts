/**
 * Cliente SSE con fetch + ReadableStream + TextDecoderStream.
 *
 * EventSource nativo no soporta POST con body JSON; por eso usamos fetch.
 * Ver doc-002 sección 6 para el flujo completo.
 */

import type {
  AgentePeticion,
  EventoErrorAgente,
  EventoFinalAgente,
  EventoFuentesAgente,
  RagChunk,
} from './schemas'
import { AgentePeticionSchema, EventoAgenteSseSchema } from './schemas'

export type AgenteSseHandlers = {
  onPensamiento: (herramientaCandidata: string, razon: string) => void
  onHerramienta: (nombre: string, latenciaMs: number) => void
  onToken: (motor: string, texto: string) => void
  onFuentes: (chunks: RagChunk[]) => void
  onFinal: (meta: Omit<EventoFinalAgente, 'tipo'>) => void
  onError: (motor: string, mensaje: string, codigo?: string) => void
}

/**
 * Inicia un stream SSE hacia `/api/agente/stream`.
 * Retorna una función `abort()` para cancelar el stream.
 */
export function streamAgente(
  endpoint: '/api/agente/stream',
  peticion: AgentePeticion,
  handlers: AgenteSseHandlers,
  signal?: AbortSignal,
): { abort: () => void } {
  const controller = new AbortController()
  const combinedSignal = signal
    ? AbortSignal.any([signal, controller.signal])
    : controller.signal

  void (async () => {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(AgentePeticionSchema.parse(peticion)),
        signal: combinedSignal,
      })

      if (!response.ok || !response.body) {
        handlers.onError('sistema', `Error HTTP ${response.status}`)
        return
      }

      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += value

        const lineas = buffer.split('\n')
        buffer = lineas.pop() ?? ''

        for (const linea of lineas) {
          if (!linea.startsWith('data: ')) continue
          const raw = linea.slice(6).trim()
          if (!raw) continue

          try {
            const json: unknown = JSON.parse(raw)
            const resultado = EventoAgenteSseSchema.safeParse(json)
            if (!resultado.success) continue

            const evento = resultado.data
            switch (evento.tipo) {
              case 'pensamiento':
                handlers.onPensamiento(evento.herramienta_candidata, evento.razon)
                break
              case 'herramienta':
                handlers.onHerramienta(evento.nombre, evento.latencia_ms)
                break
              case 'token':
                handlers.onToken(evento.motor, evento.texto)
                break
              case 'fuentes':
                handlers.onFuentes((evento as EventoFuentesAgente).chunks)
                break
              case 'final': {
                const e = evento as EventoFinalAgente
                handlers.onFinal({
                  motor: e.motor,
                  texto: e.texto,
                  latencia_ms: e.latencia_ms,
                  modelo: e.modelo,
                  metricas: e.metricas ?? null,
                })
                break
              }
              case 'error': {
                const e = evento as EventoErrorAgente
                handlers.onError(e.motor, e.mensaje, e.codigo)
                break
              }
            }
          } catch {
            // Línea no JSON (p.ej. keepalive o comentario SSE), ignorar
          }
        }
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      handlers.onError('sistema', err instanceof Error ? err.message : 'Error desconocido')
    }
  })()

  return { abort: () => controller.abort() }
}
