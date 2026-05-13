import { useCallback, useEffect, useRef, useState } from 'react'
import { toast } from 'sonner'
import { useAuth } from '@/features/auth/AuthContext'
import { getHistorialSesion } from '@/lib/api'
import { streamAgente } from '@/lib/sseClient'
import type { HistorialMensaje, RagChunk } from '@/lib/schemas'
import type { ChatTurn } from './MessageList'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import type { Message } from './MessageBubble'

function mapHistorialToTurns(mensajes: HistorialMensaje[]): ChatTurn[] {
  const out: ChatTurn[] = []
  let i = 0
  while (i < mensajes.length) {
    const row = mensajes[i]
    if (row.rol === 'system' || row.rol === 'tool') {
      i += 1
      continue
    }
    if (row.rol === 'human') {
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: row.contenido,
      }
      i += 1
      let assistantContent = ''
      let foundAi = false
      while (i < mensajes.length) {
        const next = mensajes[i]
        if (next.rol === 'human') break
        if (next.rol === 'ai') {
          assistantContent = next.contenido
          foundAi = true
          i += 1
          break
        }
        i += 1
      }
      const assistantMessage: Message | undefined = foundAi
        ? {
            id: crypto.randomUUID(),
            role: 'assistant',
            motor: 'agente',
            content: assistantContent,
            isStreaming: false,
          }
        : undefined
      out.push({
        id: `turn-${out.length}-${crypto.randomUUID()}`,
        userMessage: userMessage,
        assistantMessage,
        ragSources: [],
        routerThoughts: [],
        toolUsed: null,
      })
      continue
    }
    i += 1
  }
  return out
}

function mergeRagSources(prev: RagChunk[], next: RagChunk[]): RagChunk[] {
  if (next.length === 0) return prev
  return [...prev, ...next]
}

/** Contenedor principal del chat M2: historial, streaming SSE del agente y metadatos de tools. */
export function Chat() {
  const { sessionId } = useAuth()
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [isBusy, setIsBusy] = useState(false)
  const [historialLoading, setHistorialLoading] = useState(true)
  const [historialError, setHistorialError] = useState<string | null>(null)
  const abortRef = useRef<(() => void) | null>(null)
  /** Tras la primera carga: si no había mensajes, el primer envío usa `primer_turno: true`. */
  const usarPrimerTurnoRef = useRef(false)

  useEffect(() => {
    if (!sessionId) {
      queueMicrotask(() => {
        setTurns([])
        setHistorialLoading(false)
        setHistorialError(null)
      })
      return
    }

    let cancelado = false

    void (async () => {
      setHistorialLoading(true)
      setHistorialError(null)
      try {
        const { mensajes } = await getHistorialSesion(sessionId)
        if (cancelado) return
        usarPrimerTurnoRef.current = mensajes.length === 0
        setTurns(mapHistorialToTurns(mensajes))
      } catch {
        if (cancelado) return
        usarPrimerTurnoRef.current = false
        setHistorialError('No se pudo cargar el historial. Puede enviar mensajes, pero no verá conversaciones anteriores.')
        toast.error('No se pudo cargar el historial de la sesión.')
      } finally {
        if (!cancelado) setHistorialLoading(false)
      }
    })()

    return () => {
      cancelado = true
    }
  }, [sessionId])

  const lanzarConsulta = useCallback(
    (pregunta: string) => {
      if (!sessionId) {
        toast.error('No hay sesión activa. Inicie sesión nuevamente.')
        return
      }

      const preguntaLimpia = pregunta.trim()
      if (!preguntaLimpia) return

      const idTurno = `turn-${crypto.randomUUID()}`
      const idResp = `${idTurno}-assistant`

      const userMessage: Message = {
        id: `${idTurno}-user`,
        role: 'user',
        content: preguntaLimpia,
      }

      const assistantInicial: Message = {
        id: idResp,
        role: 'assistant',
        motor: 'agente',
        content: '',
        isStreaming: true,
      }

      const nuevoTurno: ChatTurn = {
        id: idTurno,
        userMessage,
        assistantMessage: assistantInicial,
        ragSources: [],
        routerThoughts: [],
        toolUsed: null,
      }

      setTurns((prev) => [...prev, nuevoTurno])
      setIsBusy(true)

      const primerTurno = usarPrimerTurnoRef.current
      usarPrimerTurnoRef.current = false

      const { abort } = streamAgente(
        '/api/agente/stream',
        {
          session_id: sessionId,
          pregunta: preguntaLimpia,
          primer_turno: primerTurno,
        },
        {
          onPensamiento: (herramientaCandidata, razon) => {
            setTurns((prev) =>
              prev.map((t) =>
                t.id === idTurno
                  ? {
                      ...t,
                      routerThoughts: [
                        ...t.routerThoughts,
                        { herramientaCandidata, razon },
                      ],
                    }
                  : t,
              ),
            )
          },
          onHerramienta: (nombre) => {
            setTurns((prev) =>
              prev.map((t) => (t.id === idTurno ? { ...t, toolUsed: nombre } : t)),
            )
          },
          onToken: (_motor, texto) => {
            setTurns((prev) =>
              prev.map((t) => {
                if (t.id !== idTurno || !t.assistantMessage) return t
                return {
                  ...t,
                  assistantMessage: {
                    ...t.assistantMessage,
                    content: t.assistantMessage.content + texto,
                  },
                }
              }),
            )
          },
          onFuentes: (chunks) => {
            setTurns((prev) =>
              prev.map((t) =>
                t.id === idTurno ? { ...t, ragSources: mergeRagSources(t.ragSources, chunks) } : t,
              ),
            )
          },
          onFinal: (meta) => {
            setTurns((prev) =>
              prev.map((t) => {
                if (t.id !== idTurno || !t.assistantMessage) return t
                return {
                  ...t,
                  assistantMessage: {
                    ...t.assistantMessage,
                    isStreaming: false,
                    latencia_ms: meta.latencia_ms,
                    modelo: meta.modelo,
                  },
                }
              }),
            )
            setIsBusy(false)
          },
          onError: (motor, mensaje, codigo) => {
            const detalle = codigo ? `${mensaje} (${codigo})` : mensaje
            toast.error(`Error (${motor}): ${detalle}`)
            setIsBusy(false)
            setTurns((prev) =>
              prev.map((t) => {
                if (t.id !== idTurno || !t.assistantMessage) return t
                return {
                  ...t,
                  assistantMessage: {
                    ...t.assistantMessage,
                    isStreaming: false,
                    content:
                      t.assistantMessage.content ||
                      'No se pudo completar la respuesta. Intente de nuevo o reformule la pregunta.',
                  },
                }
              }),
            )
          },
        },
      )

      abortRef.current = abort
    },
    [sessionId],
  )

  const handleIntentoEnviar = useCallback(
    (pregunta: string) => {
      if (isBusy || historialLoading) return
      lanzarConsulta(pregunta)
    },
    [isBusy, historialLoading, lanzarConsulta],
  )

  const handleStop = useCallback(() => {
    abortRef.current?.()
    abortRef.current = null
    setIsBusy(false)
    setTurns((prev) =>
      prev.map((t) => ({
        ...t,
        assistantMessage: t.assistantMessage
          ? { ...t.assistantMessage, isStreaming: false }
          : undefined,
      })),
    )
  }, [])

  const handleRegenerateLast = useCallback(() => {
    if (isBusy || historialLoading) return
    setTurns((prev) => {
      if (prev.length === 0) return prev
      const q = prev[prev.length - 1].userMessage.content
      const next = prev.slice(0, -1)
      queueMicrotask(() => lanzarConsulta(q))
      return next
    })
  }, [isBusy, historialLoading, lanzarConsulta])

  if (!sessionId) {
    return (
      <div className="flex flex-col h-full items-center justify-center px-4 text-center text-sm text-[var(--color-text-muted)]">
        Inicie sesión para usar el asistente.
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {historialError && (
        <div
          role="status"
          className="shrink-0 mx-4 mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-950 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-100"
        >
          {historialError}
        </div>
      )}
      <MessageList
        turns={turns}
        historialLoading={historialLoading}
        onSelectSuggested={handleIntentoEnviar}
        onRegenerateLast={handleRegenerateLast}
      />
      <ChatInput
        onSubmit={handleIntentoEnviar}
        isBusy={isBusy}
        historialLoading={historialLoading}
        onStop={handleStop}
      />
    </div>
  )
}
