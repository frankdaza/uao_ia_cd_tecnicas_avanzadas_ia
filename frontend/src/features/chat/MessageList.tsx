import { useCallback, useLayoutEffect, useRef, useState } from 'react'
import type { RagChunk } from '@/lib/schemas'
import { ArrowDownToLine, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { SUGGESTED_PROMPTS } from '@/features/chat/constants'
import type { Message } from './MessageBubble'
import { MessageBubble } from './MessageBubble'
import { SourcesPanel } from './SourcesPanel'

export interface RouterThought {
  herramientaCandidata: string
  razon: string
}

export interface ChatTurn {
  id: string
  userMessage: Message
  assistantMessage?: Message
  ragSources: RagChunk[]
  routerThoughts: RouterThought[]
  toolUsed: string | null
}

interface MessageListProps {
  turns: ChatTurn[]
  historialLoading?: boolean
  onSelectSuggested?: (pregunta: string) => void
  onRegenerateLast?: () => void
}

const UMBRAL_PXL = 100

/** Lista scrollable con auto-scroll condicional y sugerencias iniciales. */
export function MessageList({
  turns,
  historialLoading = false,
  onSelectSuggested,
  onRegenerateLast,
}: MessageListProps) {
  const areaRef = useRef<HTMLDivElement>(null)
  const sentinelRef = useRef<HTMLDivElement>(null)
  const prevLen = useRef(0)
  const [mostrarSaltarAbajo, setMostrarSaltarAbajo] = useState(false)

  const cercanoAlPie = useCallback(() => {
    const el = areaRef.current
    if (!el) return true
    const distancia = el.scrollHeight - el.scrollTop - el.clientHeight
    return distancia < UMBRAL_PXL
  }, [])

  const scrollSuavePie = () => sentinelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })

  useLayoutEffect(() => {
    if (turns.length > prevLen.current || cercanoAlPie()) {
      sentinelRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
    prevLen.current = turns.length
  }, [turns, cercanoAlPie])

  const onScroll = () => setMostrarSaltarAbajo(!cercanoAlPie())

  if (historialLoading && turns.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto flex flex-col bg-[var(--color-background)] items-center justify-center px-4 py-12">
        <p className="text-sm text-[var(--color-text-muted)]" role="status">
          Cargando historial de la sesión…
        </p>
      </div>
    )
  }

  if (turns.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto flex flex-col bg-[var(--color-background)]">
        <div className="flex-1 flex items-center justify-center text-center px-4 py-8">
          <div className="flex flex-col items-center gap-6 max-w-lg w-full">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-[var(--color-primary)] via-[var(--color-accent)] to-[var(--color-lime)] flex items-center justify-center shadow-lg shadow-[color-mix(in_srgb,var(--color-accent)_35%,transparent)] rotate-[-3deg]">
              <Sparkles className="h-10 w-10 text-white" aria-hidden />
            </div>
            <div>
              <h2 className="font-display text-xl font-semibold tracking-tight text-[var(--color-primary)] dark:text-[var(--color-text)]">
                ¿En qué puedo ayudarte hoy?
              </h2>
              <p className="text-sm text-[var(--color-text-muted)] mt-2 leading-relaxed">
                Haz una pregunta sobre la Fundación Valle del Lili. Las respuestas se fundamentan en el
                corpus indexado desde el sitio web oficial — no sustituyen asesoría médica ni trámites
                oficiales.
              </p>
            </div>
            {onSelectSuggested && (
              <div className="grid gap-3 w-full sm:grid-cols-2">
                {SUGGESTED_PROMPTS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => onSelectSuggested(p)}
                    className="text-left rounded-xl border border-[var(--border)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-2)] hover:border-[var(--color-accent)] px-4 py-3 text-sm shadow-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] focus-visible:ring-offset-2"
                  >
                    {p}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 min-h-0 relative flex flex-col">
      <div
        ref={areaRef}
        onScroll={onScroll}
        className="flex-1 overflow-y-auto py-6 flex flex-col gap-6 chat-gradient"
      >
        {turns.map((turn, index) => {
          const ultimoTurno = index === turns.length - 1
          const assistant = turn.assistantMessage
          return (
            <div key={turn.id} className="flex flex-col gap-4 relative">
              <div className="px-4">
                <MessageBubble message={turn.userMessage} />
              </div>
              <div className="px-4">
                {assistant != null ? (
                  <MessageBubble
                    message={assistant}
                    toolUsed={turn.toolUsed}
                    routerThoughts={turn.routerThoughts}
                    showAssistantFooter={Boolean(ultimoTurno && assistant.role === 'assistant')}
                    onRegenerate={ultimoTurno ? onRegenerateLast : undefined}
                  />
                ) : null}
              </div>
              {turn.ragSources.length > 0 && <SourcesPanel chunks={turn.ragSources} />}
            </div>
          )
        })}
        <div ref={sentinelRef} />
      </div>
      {mostrarSaltarAbajo && (
        <div className="absolute bottom-3 right-4 z-10">
          <Button
            type="button"
            size="sm"
            variant="secondary"
            className="shadow-md gap-1.5 rounded-full px-4"
            onClick={scrollSuavePie}
            aria-label="Ir al último mensaje"
          >
            <ArrowDownToLine className="h-4 w-4" aria-hidden />
            Último mensaje
          </Button>
        </div>
      )}
    </div>
  )
}
