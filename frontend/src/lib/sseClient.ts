/**
 * Cliente SSE con fetch + ReadableStream + TextDecoderStream.
 *
 * EventSource nativo no soporta POST con body JSON; por eso usamos fetch.
 * Ver doc-002 sección 6 para el flujo completo.
 */

import type { EventoError, EventoFinal, EventoFuentes, EventoToken, FuenteBm25, QaPeticion } from './schemas'
import { EventoSseSchema } from './schemas'

export type SseHandlers = {
  onToken: (motor: string, texto: string) => void
  onFuentes: (fuentes: FuenteBm25[]) => void
  onFinal: (motor: string, meta: Omit<EventoFinal, 'tipo'>) => void
  onError: (motor: string, mensaje: string) => void
}

/**
 * Inicia un stream SSE hacia el endpoint dado.
 * Retorna una función `abort()` para cancelar el stream.
 */
export function streamQa(
  endpoint: '/api/qa/stream' | '/api/qa/dual/stream',
  peticion: QaPeticion,
  handlers: SseHandlers,
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
        body: JSON.stringify(peticion),
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
            const resultado = EventoSseSchema.safeParse(json)
            if (!resultado.success) continue

            const evento = resultado.data
            switch (evento.tipo) {
              case 'token':
                handlers.onToken((evento as EventoToken).motor, (evento as EventoToken).texto)
                break
              case 'fuentes':
                handlers.onFuentes((evento as EventoFuentes).fuentes)
                break
              case 'final': {
                const e = evento as EventoFinal
                handlers.onFinal(e.motor, { motor: e.motor, texto: e.texto, latencia_ms: e.latencia_ms, modelo: e.modelo })
                break
              }
              case 'error': {
                const e = evento as EventoError
                handlers.onError(e.motor, e.mensaje)
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
