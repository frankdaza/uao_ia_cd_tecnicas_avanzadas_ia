import type { MensajeConversacion } from '@/lib/schemas'
import { cn } from '@/lib/cn'
import { MensajeMarkdown } from './MensajeMarkdown'

interface ConversacionHiloProps {
  mensajes: MensajeConversacion[]
}

/** Hilo paciente–bot en burbujas (solo lectura). */
export function ConversacionHilo({ mensajes }: ConversacionHiloProps) {
  const ordenados = [...mensajes].sort((a, b) => a.indice - b.indice)

  if (ordenados.length === 0) {
    return (
      <p className="rounded-lg border border-dashed border-[var(--border)] p-6 text-center text-sm text-[var(--color-text-muted)]">
        Aún no hay mensajes en el hilo de este caso.
      </p>
    )
  }

  return (
    <div className="flex max-h-[min(480px,60vh)] flex-col gap-3 overflow-y-auto rounded-lg border border-[var(--border)] p-4">
      {ordenados.map((msg) => {
        const esPaciente = msg.rol === 'human'
        return (
          <div
            key={msg.indice}
            className={cn('flex', esPaciente ? 'justify-end' : 'justify-start')}
          >
            <div
              className={cn(
                'max-w-[85%] rounded-lg px-3 py-2 text-sm',
                esPaciente && 'whitespace-pre-wrap',
                esPaciente
                  ? 'bg-[var(--color-primary)]/15 text-[var(--color-text)]'
                  : 'bg-[var(--color-surface)] text-[var(--color-text)]',
              )}
            >
              <p className="mb-1 text-[10px] font-medium uppercase tracking-wide text-[var(--color-text-subtle)]">
                {esPaciente ? 'Paciente' : 'Bot TAAM'}
              </p>
              {esPaciente ? msg.contenido : <MensajeMarkdown>{msg.contenido}</MensajeMarkdown>}
            </div>
          </div>
        )
      })}
    </div>
  )
}
