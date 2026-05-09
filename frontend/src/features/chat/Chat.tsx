import { useCallback, useRef, useState } from 'react'
import { toast } from 'sonner'
import { useSettings } from '@/features/settings/SettingsContext'
import { streamQa } from '@/lib/sseClient'
import type { FuenteBm25 } from '@/lib/schemas'
import type { ChatTurn } from './MessageList'
import { MessageList } from './MessageList'
import { ChatInput } from './ChatInput'
import type { Message } from './MessageBubble'

let turnoCounter = 0

/** Contenedor principal del chat: gestiona el estado y el streaming SSE. */
export function Chat() {
  const [turns, setTurns] = useState<ChatTurn[]>([])
  const [isBusy, setIsBusy] = useState(false)
  const { settings, toQaPeticion } = useSettings()
  const abortRef = useRef<(() => void) | null>(null)

  const lanzarConsulta = useCallback(
    (pregunta: string) => {
      const preguntaLimpia = pregunta.trim()
      if (!preguntaLimpia) return

      const idTurno = `turno-${++turnoCounter}`
      const idRespOllama = `${idTurno}-ollama`
      const idRespOpenai = `${idTurno}-openai`
      const modoDual = settings.usarOllama && settings.usarOpenai

      const mensajePregunta: Message = {
        id: `${idTurno}-pregunta`,
        role: 'user',
        content: preguntaLimpia,
      }

      const respOllamaInicial: Message = {
        id: idRespOllama,
        role: 'assistant',
        motor: 'ollama',
        content: '',
        isStreaming: true,
      }

      const respOpenaiInicial: Message = {
        id: idRespOpenai,
        role: 'assistant',
        motor: 'openai',
        content: '',
        isStreaming: true,
      }

      const nuevoTurno: ChatTurn = {
        id: idTurno,
        pregunta: mensajePregunta,
        respuestaOllama: settings.usarOllama ? respOllamaInicial : undefined,
        respuestaOpenai: settings.usarOpenai ? respOpenaiInicial : undefined,
        fuentes: [],
        modoDual,
      }

      setTurns((prev) => [...prev, nuevoTurno])
      setIsBusy(true)

      const peticion = toQaPeticion(preguntaLimpia)
      const endpoint = modoDual ? '/api/qa/dual/stream' : '/api/qa/stream'

      const { abort } = streamQa(endpoint, peticion, {
        onToken: (motor, texto) => {
          setTurns((prev) =>
            prev.map((t) => {
              if (t.id !== idTurno) return t
              if (motor === 'openai') {
                return {
                  ...t,
                  respuestaOpenai: t.respuestaOpenai
                    ? { ...t.respuestaOpenai, content: t.respuestaOpenai.content + texto }
                    : undefined,
                }
              }
              return {
                ...t,
                respuestaOllama: t.respuestaOllama
                  ? { ...t.respuestaOllama, content: t.respuestaOllama.content + texto }
                  : undefined,
              }
            }),
          )
        },
        onFuentes: (fuentes: FuenteBm25[]) => {
          setTurns((prev) =>
            prev.map((t) => (t.id === idTurno ? { ...t, fuentes } : t)),
          )
        },
        onFinal: (motor, meta) => {
          setTurns((prev) =>
            prev.map((t) => {
              if (t.id !== idTurno) return t
              if (motor === 'openai') {
                return {
                  ...t,
                  respuestaOpenai: t.respuestaOpenai
                    ? {
                        ...t.respuestaOpenai,
                        isStreaming: false,
                        latencia_ms: meta.latencia_ms,
                        modelo: meta.modelo,
                      }
                    : undefined,
                }
              }
              return {
                ...t,
                respuestaOllama: t.respuestaOllama
                  ? {
                      ...t.respuestaOllama,
                      isStreaming: false,
                      latencia_ms: meta.latencia_ms,
                      modelo: meta.modelo,
                    }
                  : undefined,
              }
            }),
          )
          if (!modoDual || motor === 'openai') setIsBusy(false)
        },
        onError: (motor, mensaje) => {
          toast.error(`Error (${motor}): ${mensaje}`)
          setIsBusy(false)
          setTurns((prev) =>
            prev.map((t) => {
              if (t.id !== idTurno) return t
              return {
                ...t,
                respuestaOllama: t.respuestaOllama
                  ? { ...t.respuestaOllama, isStreaming: false }
                  : undefined,
                respuestaOpenai: t.respuestaOpenai
                  ? { ...t.respuestaOpenai, isStreaming: false }
                  : undefined,
              }
            }),
          )
        },
      })

      abortRef.current = abort
    },
    [settings, toQaPeticion],
  )

  const handleIntentoEnviar = useCallback(
    (pregunta: string) => {
      if (isBusy) return
      lanzarConsulta(pregunta)
    },
    [isBusy, lanzarConsulta],
  )

  const handleStop = useCallback(() => {
    abortRef.current?.()
    abortRef.current = null
    setIsBusy(false)
    setTurns((prev) =>
      prev.map((t) => ({
        ...t,
        respuestaOllama: t.respuestaOllama
          ? { ...t.respuestaOllama, isStreaming: false }
          : undefined,
        respuestaOpenai: t.respuestaOpenai
          ? { ...t.respuestaOpenai, isStreaming: false }
          : undefined,
      })),
    )
  }, [])

  const handleRegenerateLast = useCallback(() => {
    if (isBusy) return
    setTurns((prev) => {
      if (prev.length === 0) return prev
      const q = prev[prev.length - 1].pregunta.content
      const next = prev.slice(0, -1)
      queueMicrotask(() => lanzarConsulta(q))
      return next
    })
  }, [isBusy, lanzarConsulta])

  return (
    <div className="flex flex-col h-full">
      <MessageList
        turns={turns}
        onSelectSuggested={handleIntentoEnviar}
        onRegenerateLast={handleRegenerateLast}
      />
      <ChatInput
        onSubmit={handleIntentoEnviar}
        isBusy={isBusy}
        onStop={handleStop}
      />
    </div>
  )
}
