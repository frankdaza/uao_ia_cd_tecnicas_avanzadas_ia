import { cn } from '@/lib/cn'
import type { Procedimiento } from '@/lib/schemas'

const ESTADO_CONFIG: Record<
  Procedimiento['indexacion_estado'],
  { label: string; className: string }
> = {
  pendiente: {
    label: 'Indexación pendiente',
    className:
      'bg-amber-500/15 text-amber-900 dark:text-amber-200 border-amber-500/30',
  },
  ok: {
    label: 'Listo para RAG',
    className: 'bg-emerald-500/15 text-emerald-900 dark:text-emerald-200 border-emerald-500/30',
  },
  error: {
    label: 'Error de indexación',
    className: 'bg-red-500/15 text-red-900 dark:text-red-200 border-red-500/30',
  },
}

export function IndexacionEstadoBadge({
  estado,
  className,
}: {
  estado: Procedimiento['indexacion_estado']
  className?: string
}) {
  const cfg = ESTADO_CONFIG[estado]
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium',
        cfg.className,
        className,
      )}
    >
      {cfg.label}
    </span>
  )
}

const FORMATO_CONFIG: Record<
  Procedimiento['formato_protocolo'],
  { label: string; className: string }
> = {
  pdf: {
    label: 'PDF',
    className: 'bg-slate-500/15 text-slate-900 dark:text-slate-200 border-slate-500/30',
  },
  markdown: {
    label: 'Markdown',
    className: 'bg-violet-500/15 text-violet-900 dark:text-violet-200 border-violet-500/30',
  },
}

export function FormatoProtocoloBadge({
  formato,
  className,
}: {
  formato: Procedimiento['formato_protocolo']
  className?: string
}) {
  const cfg = FORMATO_CONFIG[formato]
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium',
        cfg.className,
        className,
      )}
    >
      {cfg.label}
    </span>
  )
}
