import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { ConteoPorSeveridad } from '@/lib/schemas'
import { SeveridadBadge } from '@/features/seguimiento/SeveridadBadge'
import type { SeveridadTriage } from '@/lib/schemas'
import { cn } from '@/lib/cn'

interface SeverityBreakdownProps {
  pendientes: ConteoPorSeveridad
  onNavigateSeguimiento?: (severidad?: SeveridadTriage) => void
}

const SEVERIDADES: SeveridadTriage[] = ['urgente', 'seguimiento', 'info']

/** Desglose visual de alertas pendientes por severidad. */
export function SeverityBreakdown({ pendientes, onNavigateSeguimiento }: SeverityBreakdownProps) {
  const max = Math.max(pendientes.urgente, pendientes.seguimiento, pendientes.info, 1)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Alertas pendientes</CardTitle>
        <CardDescription>
          {pendientes.total} en bandeja — priorice urgente y seguimiento
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {SEVERIDADES.map((sev) => {
          const count =
            sev === 'urgente'
              ? pendientes.urgente
              : sev === 'seguimiento'
                ? pendientes.seguimiento
                : pendientes.info
          const pct = Math.round((count / max) * 100)
          return (
            <button
              key={sev}
              type="button"
              className={cn(
                'w-full text-left rounded-lg p-3 transition-colors',
                'hover:bg-[var(--accent)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]',
              )}
              onClick={() => onNavigateSeguimiento?.(sev)}
            >
              <div className="mb-2 flex items-center justify-between gap-2">
                <SeveridadBadge severidad={sev} />
                <span className="font-mono text-lg font-semibold tabular-nums">{count}</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-[var(--muted)]">
                <div
                  className={cn(
                    'h-full rounded-full transition-all duration-500',
                    sev === 'urgente' && 'bg-[var(--destructive)]',
                    sev === 'seguimiento' && 'bg-amber-500',
                    sev === 'info' && 'bg-[var(--color-accent)]',
                  )}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </button>
          )
        })}
      </CardContent>
    </Card>
  )
}
