import { useCallback, useEffect, useRef, useState } from 'react'
import { ZodError } from 'zod'
import { toast } from 'sonner'
import { useAuth } from '@/features/auth/AuthContext'
import { ApiError, deleteUltimoTurno, getHistorialSesion } from '@/lib/api'
import { respuestaFinalEsSinInformacion } from '@/lib/agenteRespuesta'
import { streamAgente } from '@/lib/sseClient'
import type { HistorialMensaje, ListadoItem, MetadataTurnoHistorial, RagChunk, ResultadoListadoSse } from '@/lib/schemas'
import { ListadoItemSchema } from '@/lib/schemas'
import type { ChatTurn, RouterThought } from './MessageList'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import type { Message } from './MessageBubble'

function routerThoughtsDesdeHistorial(meta: MetadataTurnoHistorial | null | undefined): RouterThought[] {
  const raw = meta?.pensamientos
  if (!raw?.length) return []
  return raw.map((p) => ({
    herramientaCandidata: String(p.herramienta ?? ''),
    razon: String(p.razon_breve ?? ''),
  }))
}

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
      let toolUsed: string | null = null
      let routerThoughts: RouterThought[] = []
      let ragSources: RagChunk[] = []
      while (i < mensajes.length) {
        const next = mensajes[i]
        if (next.rol === 'human') break
        if (next.rol === 'ai') {
          assistantContent = next.contenido
          const meta = next.metadata_turno
          toolUsed = meta?.herramienta_efectiva ?? null
          routerThoughts = routerThoughtsDesdeHistorial(meta)
          ragSources = meta?.fuentes?.length ? [...meta.fuentes] : []
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
        ragSources,
        routerThoughts,
        toolUsed,
        listadoItems: [],
        listadoConteo: undefined,
        listadoMuestraTruncada: undefined,
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

function itemsDesdeResultadoListado(res: ResultadoListadoSse | null | undefined): ListadoItem[] {
  if (!res?.items?.length) return []
  return res.items
    .map((x) => ListadoItemSchema.safeParse(x))
    .flatMap((r) => (r.success ? [r.data] : []))
}

/** Contenedor principal del chat M2: historial, streaming SSE del agente y metadatos de tools. */
export function Chat() {
  const { sessionId } = useAuth()
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [isBusy, setIsBusy] = useState(false)
  const [historialLoading, setHistorialLoading] = useState(true)
  const [historialError, setHistorialError] = useState<string | null>(null)
  const abortRef = useRef<(() => void) | null>(null)
  const turnsRef = useRef<ChatTurn[]>([])
  /** Tras la primera carga: si no había mensajes, el primer envío usa `primer_turno: true`. */
  const usarPrimerTurnoRef = useRef(false)

  useEffect(() => {
    turnsRef.current = turns
  }, [turns])

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
      } catch (error) {
        if (cancelado) return
        usarPrimerTurnoRef.current = false
        if (import.meta.env.DEV) {
          console.error('[Chat] Fallo al cargar historial (GET /api/sesiones/actual/historial)', error)
        }
        let mensajeBanner =
          'No se pudo cargar el historial. Puede enviar mensajes, pero no verá conversaciones anteriores.'
        let mensajeToast = 'No se pudo cargar el historial de la sesión.'
        if (error instanceof ApiError) {
          mensajeToast = error.detail?.trim() || mensajeToast
          if (error.status === 401 || error.status === 403) {
            mensajeBanner =
              'Sesión inválida o expirada. Inicie sesión de nuevo para ver el historial anterior.'
          } else if (error.status >= 500) {
            mensajeBanner =
              'Error del servidor al leer el historial. Revise que PostgreSQL (memoria LangChain) esté disponible y los logs del backend.'
          } else {
            mensajeBanner = `No se pudo cargar el historial (código ${String(error.status)}). ${error.detail ?? ''}`.trim()
          }
        } else if (error instanceof ZodError) {
          mensajeToast =
            'La respuesta del historial no coincide con el formato esperado (detalle en consola del navegador).'
          mensajeBanner =
            'El servidor devolvió datos de historial en un formato incompatible. Abra la consola (F12) y busque el prefijo [API].'
        }
        setHistorialError(mensajeBanner)
        toast.error(mensajeToast)
      } finally {
        if (!cancelado) setHistorialLoading(false)
      }
    })()

    return () => {
      cancelado = true
    }
  }, [sessionId])

  useEffect(() => {
    return () => {
      abortRef.current?.()
      abortRef.current = null
    }
  }, [])

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
        listadoItems: [],
        listadoConteo: undefined,
        listadoMuestraTruncada: undefined,
      }

      setTurns((prev) => [...prev, nuevoTurno])
      setIsBusy(true)

      const primerTurnoActivo = usarPrimerTurnoRef.current

      const { abort } = streamAgente(
        '/api/agente/stream',
        {
          session_id: sessionId,
          pregunta: preguntaLimpia,
          primer_turno: primerTurnoActivo,
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
          onHerramienta: (nombre, _latenciaMs, resultadoListado) => {
            setTurns((prev) =>
              prev.map((t) => {
                if (t.id !== idTurno) return t
                const listadoItems =
                  nombre === 'listar_estructurado'
                    ? itemsDesdeResultadoListado(resultadoListado ?? null)
                    : t.listadoItems
                const listadoConteo =
                  nombre === 'listar_estructurado'
                    ? resultadoListado?.conteo
                    : t.listadoConteo
                const listadoMuestraTruncada =
                  nombre === 'listar_estructurado'
                    ? resultadoListado?.muestra_truncada
                    : t.listadoMuestraTruncada
                return {
                  ...t,
                  toolUsed: nombre,
                  listadoItems,
                  listadoConteo,
                  listadoMuestraTruncada,
                }
              }),
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
            if (primerTurnoActivo) {
              usarPrimerTurnoRef.current = false
            }
            const sinInfo = respuestaFinalEsSinInformacion(meta.texto)
            setTurns((prev) =>
              prev.map((t) => {
                if (t.id !== idTurno || !t.assistantMessage) return t
                const limpiarListado = sinInfo && t.toolUsed === 'listar_estructurado'
                const contenidoFinal =
                  t.assistantMessage.content.trim().length > 0
                    ? t.assistantMessage.content
                    : meta.texto
                return {
                  ...t,
                  ...(limpiarListado
                    ? {
                        listadoItems: [],
                        listadoConteo: undefined,
                        listadoMuestraTruncada: undefined,
                      }
                    : {}),
                  assistantMessage: {
                    ...t.assistantMessage,
                    content: contenidoFinal,
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

  const handleRegenerateLast = useCallback(async () => {
    if (isBusy || historialLoading || !sessionId) return
    const prev = turnsRef.current
    if (prev.length === 0) return
    const q = prev[prev.length - 1].userMessage.content.trim()
    if (!q) return
    try {
      await deleteUltimoTurno(sessionId)
    } catch {
      toast.error('No se pudo eliminar el último turno en el servidor. Intente de nuevo.')
      return
    }
    setTurns((p) => (p.length === 0 ? p : p.slice(0, -1)))
    queueMicrotask(() => lanzarConsulta(q))
  }, [isBusy, historialLoading, sessionId, lanzarConsulta])

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
