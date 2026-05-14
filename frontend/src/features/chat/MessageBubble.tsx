import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { toast } from 'sonner'
import { Copy, RotateCcw, ChevronDown, ChevronRight } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/cn'
import type { ListadoItem } from '@/lib/schemas'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  motor?: 'ollama' | 'openai' | string
  content: string
  isStreaming?: boolean
  latencia_ms?: number
  modelo?: string
}

interface MessageBubbleProps {
  message: Message
  showAssistantFooter?: boolean
  onRegenerate?: () => void | Promise<void>
  /** Nombre de tool ejecutada (`faq_estructurada`, `rag_denso`, …). */
  toolUsed?: string | null
  /** Filas devueltas por la tool `listar_estructurado` (evento SSE). */
  listadoItems?: ListadoItem[]
  listadoConteo?: number
  listadoMuestraTruncada?: boolean
  /** Eventos de decisión del router (solo resúmenes seguros del backend). */
  routerThoughts?: { herramientaCandidata: string; razon: string }[]
}

function etiquetaToolEjecutada(nombre: string): string {
  if (nombre === 'faq_estructurada') return 'Tool: FAQ'
  if (nombre === 'rag_denso') return 'Tool: RAG denso'
  if (nombre === 'listar_estructurado') return 'Tool: Listado estructurado'
  return `Tool: ${nombre}`
}

async function copiar(texto: string) {
  try {
    await navigator.clipboard.writeText(texto)
    toast.success('Texto copiado al portapapeles')
  } catch {
    toast.error('No se pudo copiar el texto')
  }
}

/** Burbuja de mensaje del chat con render Markdown. */
export function MessageBubble({
  message,
  showAssistantFooter = false,
  onRegenerate,
  toolUsed = null,
  listadoItems = [],
  listadoConteo,
  listadoMuestraTruncada,
  routerThoughts,
}: MessageBubbleProps) {
  const esUsuario = message.role === 'user'
  const [razonamientoAbierto, setRazonamientoAbierto] = useState(false)
  const pensamientos = routerThoughts ?? []

  return (
    <div
      className={cn(
        'flex gap-3 max-w-3xl mx-auto w-full',
        esUsuario && 'flex-row-reverse',
      )}
    >
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold',
          esUsuario
            ? 'bg-[var(--color-secondary)] text-[var(--color-primary)]'
            : 'bg-[var(--color-accent)] text-white',
        )}
        aria-hidden="true"
      >
        {esUsuario ? 'Tú' : 'IA'}
      </div>

      <div className={cn('flex-1 flex flex-col gap-1 min-w-0', esUsuario && 'items-end')}>
        {!esUsuario && message.motor && (
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary" className="text-xs">
              {message.motor === 'ollama'
                ? 'Ollama (local)'
                : message.motor === 'openai'
                  ? 'OpenAI (API)'
                  : message.motor === 'agente'
                    ? 'Agente'
                    : message.motor}
            </Badge>
            {toolUsed && (
              <Badge variant="outline" className="text-xs border-[var(--color-accent)]/40">
                {etiquetaToolEjecutada(toolUsed)}
              </Badge>
            )}
            {message.latencia_ms != null &&
              !message.isStreaming &&
              message.latencia_ms > 0 && (
                <span className="text-xs text-[var(--color-text-subtle)] tabular-nums">
                  {(message.latencia_ms / 1000).toFixed(1)}s
                </span>
              )}
          </div>
        )}

        {!esUsuario && pensamientos.length > 0 && (
          <div className="w-full max-w-full">
            <button
              type="button"
              className="flex items-center gap-1 text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-accent)] rounded-md py-0.5"
              aria-expanded={razonamientoAbierto}
              onClick={() => setRazonamientoAbierto((a) => !a)}
            >
              {razonamientoAbierto ? (
                <ChevronDown className="h-3.5 w-3.5 shrink-0" aria-hidden />
              ) : (
                <ChevronRight className="h-3.5 w-3.5 shrink-0" aria-hidden />
              )}
              Razonamiento del router
            </button>
            {razonamientoAbierto && (
              <ul className="mt-1.5 space-y-1.5 rounded-lg border border-[var(--border)] bg-[var(--color-surface-2)]/60 px-3 py-2 text-xs text-[var(--color-text-muted)]">
                {pensamientos.map((p, idx) => (
                  <li key={`${p.herramientaCandidata}-${idx}`} className="leading-snug">
                    <span className="font-medium text-[var(--color-text)]">{p.herramientaCandidata}</span>
                    {p.razon ? <span>: {p.razon}</span> : null}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        <div
          className={cn(
            'rounded-2xl px-4 py-3 text-sm leading-relaxed max-w-full',
            esUsuario
              ? 'bg-[var(--color-message-user-bg)] text-[var(--color-message-user-fg)] rounded-tr-sm shadow-sm'
              : 'bg-[var(--color-surface)] border border-[var(--border)] rounded-tl-sm',
          )}
        >
          {!esUsuario &&
            toolUsed === 'listar_estructurado' &&
            listadoItems &&
            listadoItems.length > 0 && (
              <div className="mb-3 overflow-x-auto rounded-lg border border-[var(--border)] bg-[var(--color-surface-2)]/40">
                <p className="px-3 py-2 text-xs text-[var(--color-text-muted)] border-b border-[var(--border)]">
                  {listadoConteo != null ? (
                    <>
                      Total estimado: <span className="font-semibold text-[var(--color-text)]">{listadoConteo}</span>
                      {listadoMuestraTruncada ? ' (muestra truncada)' : null}
                    </>
                  ) : (
                    'Resultado del listado'
                  )}
                </p>
                <table className="w-full text-xs text-left">
                  <thead>
                    <tr className="border-b border-[var(--border)] text-[var(--color-text-muted)]">
                      <th className="px-3 py-2 font-medium">Nombre</th>
                      <th className="px-3 py-2 font-medium">Especialidad</th>
                      <th className="px-3 py-2 font-medium">Sedes</th>
                      <th className="px-3 py-2 font-medium">Enlace</th>
                    </tr>
                  </thead>
                  <tbody>
                    {listadoItems.map((row, idx) => (
                      <tr key={`${row.nombre}-${idx}`} className="border-b border-[var(--border)] last:border-0">
                        <td className="px-3 py-2 align-top text-[var(--color-text)]">{row.nombre}</td>
                        <td className="px-3 py-2 align-top text-[var(--color-text-muted)]">
                          {(row.especialidad ?? []).join(', ') || '—'}
                        </td>
                        <td className="px-3 py-2 align-top text-[var(--color-text-muted)]">
                          {(row.sedes ?? []).join(', ') || '—'}
                        </td>
                        <td className="px-3 py-2 align-top">
                          {row.source_url ? (
                            <a
                              href={row.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-[var(--color-accent)] underline-offset-2 hover:underline break-all"
                            >
                              Ver
                            </a>
                          ) : (
                            '—'
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          {message.isStreaming && !message.content ? (
            <div className="flex flex-col gap-1.5">
              <Skeleton className="h-3 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
              <Skeleton className="h-3 w-5/6" />
            </div>
          ) : esUsuario ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ className, children }) {
                    const match = /language-(\w+)/.exec(className ?? '')
                    const isBlock = Boolean(match)
                    const codeText = String(children).replace(/\n$/, '')
                    if (!isBlock) {
                      return (
                        <code className="bg-[var(--color-surface-2)] px-1 py-0.5 rounded text-xs font-mono">
                          {children}
                        </code>
                      )
                    }
                    return (
                      <MarkdownCodeBlock language={match?.[1] ?? ''} code={codeText} />
                    )
                  },
                  a({ href, children, ...props }) {
                    return (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[var(--color-accent)] underline-offset-2 hover:underline"
                        {...props}
                      >
                        {children}
                      </a>
                    )
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
              {message.isStreaming && (
                <span
                  className="inline-block w-1.5 h-4 bg-[var(--color-accent)] animate-pulse ml-0.5 token-fade-in"
                  aria-hidden
                />
              )}
            </div>
          )}
        </div>

        {!esUsuario && showAssistantFooter && message.content && !message.isStreaming && (
          <div className="flex gap-2 justify-start flex-wrap">
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => void copiar(message.content)}
              aria-label="Copiar respuesta del asistente"
            >
              <Copy className="h-3 w-3 mr-1.5 shrink-0" aria-hidden />
              Copiar
            </Button>
            {onRegenerate && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => void Promise.resolve(onRegenerate())}
                aria-label="Generar respuesta nuevamente"
              >
                <RotateCcw className="h-3 w-3 mr-1.5 shrink-0" aria-hidden />
                Regenerar
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
