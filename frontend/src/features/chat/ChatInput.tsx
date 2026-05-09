import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { Send, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

const SESSION_DRAFT = 'fvl-draft-input'

interface ChatInputProps {
  onSubmit: (pregunta: string) => void
  isBusy: boolean
  onStop?: () => void
}

/** Área de entrada del chat: borrador persistente en sessionStorage y autoaltura. */
export function ChatInput({ onSubmit, isBusy, onStop }: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const [draft, setDraft] = useState(() => {
    try {
      return sessionStorage.getItem(SESSION_DRAFT) ?? ''
    } catch {
      return ''
    }
  })

  useEffect(() => {
    try {
      sessionStorage.setItem(SESSION_DRAFT, draft)
    } catch {
      //
    }
  }, [draft])

  const resize = () => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, 220)}px`
  }

  useEffect(() => {
    resize()
  }, [draft])

  const enviar = () => {
    const valor = draft.trim()
    if (!valor) return
    if (isBusy) return
    onSubmit(valor)
    setDraft('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      enviar()
    }
  }

  return (
    <div className="border-t border-[var(--border)] bg-[var(--background)] p-4">
      <div className="flex gap-2 items-end max-w-3xl mx-auto">
        <Textarea
          id="chat-principal-q"
          ref={textareaRef}
          placeholder="¿Cuál es tu pregunta sobre la Fundación Valle del Lili?"
          rows={2}
          disabled={isBusy && !onStop}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
          aria-label="Escribe tu pregunta"
          className="flex-1 resize-none min-h-[52px]"
        />
        {isBusy && onStop ? (
          <Button
            type="button"
            onClick={() => onStop()}
            aria-label="Detener generación"
            variant="secondary"
            className="shrink-0 gap-2"
          >
            <Square className="h-4 w-4 fill-current" aria-hidden />
            <span className="hidden sm:inline text-xs">Detener</span>
          </Button>
        ) : (
          <Button type="button" onClick={enviar} disabled={isBusy || !draft.trim()} aria-label="Enviar pregunta" className="shrink-0">
            <Send className="h-4 w-4" aria-hidden />
            <span className="sr-only">Enviar</span>
          </Button>
        )}
      </div>
      <p className="text-center text-xs text-[var(--color-text-subtle)] mt-2">
        Ctrl+Enter para enviar · Ctrl+B panel · Ctrl+K foco en el campo
      </p>
    </div>
  )
}
