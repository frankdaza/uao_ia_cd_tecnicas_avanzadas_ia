import { cn } from '@/lib/cn'

interface VinculoTelegramBadgeProps {
  vinculado: boolean
  className?: string
}

/** Indicador de emparejamiento Telegram en listado de casos. */
export function VinculoTelegramBadge({ vinculado, className }: VinculoTelegramBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        vinculado
          ? 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-400'
          : 'bg-amber-500/15 text-amber-800 dark:text-amber-300',
        className,
      )}
    >
      {vinculado ? 'Vinculado' : 'Pendiente'}
    </span>
  )
}
