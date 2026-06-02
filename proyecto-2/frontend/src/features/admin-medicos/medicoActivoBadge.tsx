import { cn } from '@/lib/cn'

const ACTIVO_CONFIG = {
  true: {
    label: 'Activo',
    className: 'bg-emerald-500/15 text-emerald-900 dark:text-emerald-200 border-emerald-500/30',
  },
  false: {
    label: 'Inactivo',
    className: 'bg-slate-500/15 text-slate-900 dark:text-slate-200 border-slate-500/30',
  },
} as const

export function MedicoActivoBadge({
  activo,
  className,
}: {
  activo: boolean
  className?: string
}) {
  const cfg = activo ? ACTIVO_CONFIG.true : ACTIVO_CONFIG.false
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
