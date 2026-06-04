import { Copy, X } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { formatFechaAlta } from '@/lib/formatFecha'
import type { CodigoEmparejamiento } from '@/lib/schemas'
import { buildTelegramStartLink } from '@/lib/telegramDeepLink'

interface CodigoEmparejamientoModalProps {
  data: CodigoEmparejamiento
  pacienteNombre?: string
  onClose: () => void
}

async function copiarTexto(texto: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(texto)
    return true
  } catch {
    return false
  }
}

/** Modal con código de emparejamiento, TTL e instrucciones Telegram. */
export function CodigoEmparejamientoModal({
  data,
  pacienteNombre,
  onClose,
}: CodigoEmparejamientoModalProps) {
  const deepLink = buildTelegramStartLink(data.codigo)
  const expiraTexto = formatFechaAlta(data.expira_at)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="codigo-emparejamiento-titulo"
    >
      <div className="relative w-full max-w-md rounded-xl border border-[var(--border)] bg-[var(--color-surface)] p-6 shadow-lg">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="absolute right-2 top-2"
          onClick={onClose}
          aria-label="Cerrar"
        >
          <X className="h-4 w-4" aria-hidden />
        </Button>

        <h3
          id="codigo-emparejamiento-titulo"
          className="font-display text-lg font-semibold text-[var(--color-text)] pr-8"
        >
          Código de emparejamiento
        </h3>
        {pacienteNombre ? (
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">Paciente: {pacienteNombre}</p>
        ) : null}

        <p
          className="mt-6 text-center font-mono text-3xl font-bold tracking-widest text-[var(--color-text)]"
          data-testid="codigo-emparejamiento-valor"
        >
          {data.codigo}
        </p>

        <p className="mt-3 text-center text-xs text-[var(--color-text-muted)]">
          Válido hasta: {expiraTexto}
        </p>

        <p className="mt-6 text-sm text-[var(--color-text-muted)] leading-relaxed">
          En Telegram, el paciente debe enviar al bot:{' '}
          <code className="rounded bg-[var(--color-surface-2)] px-1 py-0.5 text-xs">
            /start {data.codigo}
          </code>
        </p>

        {deepLink ? (
          <p className="mt-3 text-sm">
            <a
              href={deepLink}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[var(--color-accent)] underline break-all hover:text-[var(--color-accent-light)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ring)]"
            >
              {deepLink}
            </a>
          </p>
        ) : (
          <p className="mt-3 text-xs text-[var(--color-text-subtle)]">
            Configure <code className="text-[10px]">VITE_TELEGRAM_BOT_USERNAME</code> para mostrar
            el enlace directo a Telegram.
          </p>
        )}

        <div className="mt-6 flex flex-col gap-2 sm:flex-row">
          <Button
            type="button"
            className="flex-1"
            onClick={async () => {
              const ok = await copiarTexto(data.codigo)
              if (ok) {
                toast.success('Código copiado al portapapeles.')
              } else {
                toast.error('No se pudo copiar. Seleccione el código manualmente.')
              }
            }}
          >
            <Copy className="h-4 w-4" aria-hidden />
            Copiar código
          </Button>
          <Button type="button" variant="outline" className="flex-1" onClick={onClose}>
            Cerrar
          </Button>
        </div>
      </div>
    </div>
  )
}
