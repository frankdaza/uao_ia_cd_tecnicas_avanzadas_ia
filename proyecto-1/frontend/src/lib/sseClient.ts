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
  ResultadoListadoSse,
} from './schemas'
import { AgentePeticionSchema, EventoAgenteSseSchema } from './schemas'

export type AgenteSseHandlers = {
  onPensamiento: (herramientaCandidata: string, razon: string) => void
  onHerramienta: (
    nombre: string,
    latenciaMs: number,
    resultadoListado?: ResultadoListadoSse | null,
  ) => void
  onToken: (motor: string, texto: string) => void
  onFuentes: (chunks: RagChunk[]) => void
  onFinal: (meta: Omit<EventoFinalAgente, 'tipo'>) => void
  onError: (motor: string, mensaje: string, codigo?: string) => void
}

/** Combina dos AbortSignal en uno solo (fallback si no existe AbortSignal.any). */
function combinarAbortSignals(a: AbortSignal, b: AbortSignal): AbortSignal {
  const anyFn = (
    AbortSignal as unknown as { any?: (signals: AbortSignal[]) => AbortSignal }
  ).any
  if (typeof anyFn === 'function') {
    return anyFn([a, b])
  }
  const merged = new AbortController()
  const abortMerged = () => {
    if (!merged.signal.aborted) merged.abort()
  }
  if (a.aborted || b.aborted) {
    abortMerged()
    return merged.signal
  }
  a.addEventListener('abort', abortMerged, { once: true })
  b.addEventListener('abort', abortMerged, { once: true })
  return merged.signal
}

/** Normaliza CRLF y CR sueltos a salto de línea Unix (parser SSE). */
export function normalizarSaltosLineaSse(texto: string): string {
  return texto.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
}

/**
 * Acumula líneas de un bloque SSE (hasta línea en blanco) y emite el payload `data` unido.
 * Acepta `data:` con o sin espacio tras los dos puntos; ignora comentarios `:keepalive`.
 */
export function crearAcumuladorBloqueSse(onPayloadData: (rawJson: string) => void): {
  pushLinea: (linea: string) => void
  finalizar: () => void
} {
  let bloque: string[] = []

  const vaciarBloque = () => {
    const partesData: string[] = []
    for (const linea of bloque) {
      if (linea.startsWith(':')) continue
      const coincideData = /^data: ?(.*)$/.exec(linea)
      if (coincideData) {
        partesData.push(coincideData[1].trimStart())
        continue
      }
    }
    bloque = []
    if (partesData.length === 0) return
    const unido = partesData.join('\n')
    if (!unido.trim()) return
    onPayloadData(unido)
  }

  return {
    pushLinea(linea: string) {
      if (linea === '') {
        vaciarBloque()
        return
      }
      bloque.push(linea)
    },
    finalizar() {
      vaciarBloque()
    },
  }
}

/** Despacha un evento JSON; retorna true si fue cierre de stream (`final` o `error`). */
function despacharEventoAgente(json: unknown, handlers: AgenteSseHandlers): boolean {
  const resultado = EventoAgenteSseSchema.safeParse(json)
  if (!resultado.success) {
    if (import.meta.env.DEV) {
      console.warn('[sseClient] Evento SSE inválido', resultado.error.flatten(), json)
    }
    handlers.onError('sistema', 'Evento SSE con formato inesperado', 'sse_parse')
    return true
  }
  const evento = resultado.data
  switch (evento.tipo) {
    case 'pensamiento':
      handlers.onPensamiento(evento.herramienta_candidata, evento.razon)
      break
    case 'herramienta':
      handlers.onHerramienta(
        evento.nombre,
        evento.latencia_ms,
        evento.resultado_listado ?? null,
      )
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
      return true
    }
    case 'error': {
      const e = evento as EventoErrorAgente
      handlers.onError(e.motor, e.mensaje, e.codigo)
      return true
    }
  }
  return false
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
    ? combinarAbortSignals(signal, controller.signal)
    : controller.signal

  void (async () => {
    let streamTerminal = false
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(AgentePeticionSchema.parse(peticion)),
        signal: combinedSignal,
        credentials: 'include',
      })

      if (!response.ok || !response.body) {
        streamTerminal = true
        handlers.onError('sistema', `Error HTTP ${response.status}`)
        return
      }

      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
      let buffer = ''
      const acum = crearAcumuladorBloqueSse((raw) => {
        try {
          const json: unknown = JSON.parse(raw)
          if (despacharEventoAgente(json, handlers)) {
            streamTerminal = true
          }
        } catch {
          // Payload no JSON (p. ej. keepalive), ignorar
        }
      })

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += normalizarSaltosLineaSse(value)

        const lineas = buffer.split('\n')
        buffer = lineas.pop() ?? ''

        for (const linea of lineas) {
          acum.pushLinea(linea)
        }
      }

      if (buffer.length > 0) {
        acum.pushLinea(buffer)
      }
      acum.finalizar()

      if (!streamTerminal) {
        handlers.onError(
          'sistema',
          'La conexión terminó sin confirmación del servidor (sin evento final).',
          'stream_cerrado',
        )
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return
      if (!streamTerminal) {
        handlers.onError('sistema', err instanceof Error ? err.message : 'Error desconocido')
      }
    }
  })()

  return { abort: () => controller.abort() }
}
