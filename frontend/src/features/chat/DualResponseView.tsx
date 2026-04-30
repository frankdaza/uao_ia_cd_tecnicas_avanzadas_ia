import { AlertTriangle } from 'lucide-react'
import type { Message } from './MessageBubble'
import { MessageBubble } from './MessageBubble'

interface DualResponseViewProps {
  mensajeOllama: Message | null
  mensajeOpenai: Message | null
}

/** Vista de dos columnas para respuestas paralelas Ollama y OpenAI. */
export function DualResponseView({ mensajeOllama, mensajeOpenai }: DualResponseViewProps) {
  return (
    <div className="flex flex-col gap-3 max-w-full">
      {/* Aviso de coste dual */}
      <div className="flex items-center gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-400 max-w-3xl mx-auto w-full">
        <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
        <span>
          <strong>Modo dual activo:</strong> se realizan dos llamadas LLM por consulta. Mayor
          latencia y consumo de créditos OpenAI si está habilitado el motor comercial.
        </span>
      </div>

      {/* Columnas Ollama | OpenAI */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-full px-4">
        {mensajeOllama && (
          <div className="flex flex-col gap-1">
            <p className="text-xs font-semibold text-[var(--color-text-muted)]">Ollama (local)</p>
            <MessageBubble message={mensajeOllama} />
          </div>
        )}
        {mensajeOpenai && (
          <div className="flex flex-col gap-1">
            <p className="text-xs font-semibold text-[var(--color-text-muted)]">OpenAI (API)</p>
            <MessageBubble message={mensajeOpenai} />
          </div>
        )}
      </div>
    </div>
  )
}
