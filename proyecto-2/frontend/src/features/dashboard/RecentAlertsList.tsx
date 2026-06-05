import { ChevronRight } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import type { AlertaTriage } from '@/lib/schemas'
import { SeveridadBadge } from '@/features/seguimiento/SeveridadBadge'
import { severidadCardClass } from '@/features/seguimiento/severidadStyles'
import { casoSeguimientoPath } from '@/features/seguimiento/seguimientoPaths'
import { cn } from '@/lib/cn'

interface RecentAlertsListProps {
  alertas: AlertaTriage[]
  onNavigate: (path: string) => void
}

function formatRelativo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime()
  const min = Math.floor(diff / 60_000)
  if (min < 1) return 'ahora'
  if (min < 60) return `hace ${min} min`
  const h = Math.floor(min / 60)
  if (h < 24) return `hace ${h} h`
  return new Date(iso).toLocaleDateString('es-CO', { day: 'numeric', month: 'short' })
}

/** Lista compacta de alertas pendientes recientes. */
export function RecentAlertsList({ alertas, onNavigate }: RecentAlertsListProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-2">
        <div>
          <CardTitle>Atención inmediata</CardTitle>
          <CardDescription>Últimas alertas pendientes de revisión</CardDescription>
        </div>
        <Button type="button" variant="ghost" size="sm" onClick={() => onNavigate('/seguimiento')}>
          Ver bandeja
        </Button>
      </CardHeader>
      <CardContent className="space-y-2">
        {alertas.length === 0 ? (
          <p className="rounded-lg border border-dashed border-[var(--border)] p-6 text-center text-sm text-[var(--color-text-muted)]">
            No hay alertas pendientes. Buen trabajo.
          </p>
        ) : (
          alertas.map((alerta) => (
            <button
              key={alerta.id}
              type="button"
              className={cn(
                'flex w-full items-start gap-3 rounded-lg border p-3 text-left transition-colors',
                'hover:shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]',
                severidadCardClass(alerta.severidad),
              )}
              onClick={() => onNavigate(casoSeguimientoPath(alerta.caso_id, alerta.id))}
            >
              <div className="min-w-0 flex-1 space-y-1">
                <div className="flex flex-wrap items-center gap-2">
                  <SeveridadBadge severidad={alerta.severidad} />
                  <span className="text-xs text-[var(--color-text-subtle)]">
                    {formatRelativo(alerta.created_at)}
                  </span>
                </div>
                <p className="truncate text-sm font-medium text-[var(--color-text)]">
                  {alerta.paciente_nombre}
                </p>
                <p className="line-clamp-2 text-xs text-[var(--color-text-muted)]">{alerta.resumen}</p>
              </div>
              <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-[var(--color-text-subtle)]" />
            </button>
          ))
        )}
      </CardContent>
    </Card>
  )
}
