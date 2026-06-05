import type { LucideIcon } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/cn'

interface KpiCardProps {
  title: string
  value: number | string
  subtitle?: string
  icon: LucideIcon
  accentClassName?: string
  onClick?: () => void
}

/** Tarjeta KPI con icono y valor destacado. */
export function KpiCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accentClassName,
  onClick,
}: KpiCardProps) {
  const interactive = Boolean(onClick)

  return (
    <Card
      className={cn(
        'relative overflow-hidden transition-shadow',
        interactive && 'cursor-pointer hover:shadow-md hover:border-[var(--color-accent)]/40',
        accentClassName,
      )}
      onClick={onClick}
      onKeyDown={
        interactive
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onClick?.()
              }
            }
          : undefined
      }
      role={interactive ? 'button' : undefined}
      tabIndex={interactive ? 0 : undefined}
    >
      <div className="pointer-events-none absolute -right-4 -top-4 h-24 w-24 rounded-full bg-[var(--color-accent)]/8" />
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-[var(--color-text-muted)]">{title}</CardTitle>
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--color-accent)]/15 text-[var(--color-accent)]">
          <Icon className="h-4 w-4" aria-hidden />
        </span>
      </CardHeader>
      <CardContent>
        <p className="font-display text-3xl font-bold tabular-nums tracking-tight text-[var(--color-text)]">
          {value}
        </p>
        {subtitle ? (
          <p className="mt-1 text-xs text-[var(--color-text-subtle)]">{subtitle}</p>
        ) : null}
      </CardContent>
    </Card>
  )
}
