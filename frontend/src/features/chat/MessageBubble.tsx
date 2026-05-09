import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { toast } from 'sonner'
import { Copy, RotateCcw } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/cn'
import { MarkdownCodeBlock } from '@/features/chat/MarkdownCodeBlock'

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
  onRegenerate?: () => void
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
}: MessageBubbleProps) {
  const esUsuario = message.role === 'user'

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
          <div className="flex items-center gap-2">
            <Badge variant="secondary" className="text-xs">
              {message.motor === 'ollama'
                ? 'Ollama (local)'
                : message.motor === 'openai'
                  ? 'OpenAI (API)'
                  : message.motor}
            </Badge>
            {message.latencia_ms != null &&
              !message.isStreaming &&
              message.latencia_ms > 0 && (
                <span className="text-xs text-[var(--color-text-subtle)] tabular-nums">
                  {(message.latencia_ms / 1000).toFixed(1)}s
                </span>
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
                onClick={() => onRegenerate()}
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
