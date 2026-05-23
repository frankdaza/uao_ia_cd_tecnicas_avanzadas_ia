import { cn } from '@/lib/cn'
import type { SeveridadTriage } from '@/lib/schemas'
import { SEVERIDAD_LABEL, severidadBadgeClass } from './severidadStyles'

interface SeveridadBadgeProps {
  severidad: SeveridadTriage
  className?: string
}

/** Etiqueta de severidad de triage con color semántico. */
export function SeveridadBadge({ severidad, className }: SeveridadBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex rounded-md px-2 py-0.5 text-xs font-semibold uppercase tracking-wide',
        severidadBadgeClass(severidad),
        className,
      )}
    >
      {SEVERIDAD_LABEL[severidad]}
    </span>
  )
}
