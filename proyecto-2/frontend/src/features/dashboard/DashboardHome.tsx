import { useEffect, useState } from 'react'
import {
  AlertTriangle,
  Bell,
  ClipboardList,
  MessageCircle,
  RefreshCw,
  Stethoscope,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuth } from '@/features/auth/AuthContext'
import { AlertsTrendChart } from './AlertsTrendChart'
import { formatUpdatedAgo } from './formatUpdatedAt'
import { KpiCard } from './KpiCard'
import { RecentAlertsList } from './RecentAlertsList'
import { SeverityBreakdown } from './SeverityBreakdown'
import { SystemHealthPanel } from './SystemHealthPanel'
import { useAdminDashboard } from './useAdminDashboard'
import { useStaffDashboard } from './useStaffDashboard'

interface DashboardHomeProps {
  onNavigate: (path: string) => void
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-10 w-72" />
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32" />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <Skeleton className="h-64 lg:col-span-2" />
        <Skeleton className="h-64" />
      </div>
    </div>
  )
}

/** Dashboard de inicio con KPIs en tiempo real (staff + sección admin). */
export function DashboardHome({ onNavigate }: DashboardHomeProps) {
  const { user } = useAuth()
  const esAdmin = user?.rol === 'admin'

  const staffQuery = useStaffDashboard()
  const adminQuery = useAdminDashboard(esAdmin)

  const [, tick] = useState(0)
  useEffect(() => {
    const id = window.setInterval(() => tick((n) => n + 1), 10_000)
    return () => window.clearInterval(id)
  }, [])

  const updatedLabel = staffQuery.dataUpdatedAt
    ? formatUpdatedAgo(staffQuery.dataUpdatedAt)
    : null

  if (staffQuery.isLoading && !staffQuery.data) {
    return <DashboardSkeleton />
  }

  if (staffQuery.isError) {
    return (
      <section className="max-w-lg space-y-4 rounded-lg border border-[var(--destructive)]/40 bg-[var(--destructive)]/5 p-6">
        <h2 className="font-display text-lg font-semibold text-[var(--color-text)]">
          No se pudo cargar el panel
        </h2>
        <p className="text-sm text-[var(--color-text-muted)]">
          {staffQuery.error instanceof Error ? staffQuery.error.message : 'Error desconocido'}
        </p>
        <Button type="button" variant="outline" onClick={() => staffQuery.refetch()}>
          Reintentar
        </Button>
      </section>
    )
  }

  const data = staffQuery.data
  if (!data) return null

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest text-[var(--color-accent)]">
            Panel TAAM
          </p>
          <h1 className="font-display text-2xl font-bold tracking-tight text-[var(--color-text)] sm:text-3xl">
            Hola, {user?.nombre?.split(' ')[0] ?? 'equipo'}
          </h1>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Resumen operativo en tiempo real del seguimiento posoperatorio
          </p>
        </div>
        <div className="flex items-center gap-2">
          {updatedLabel ? (
            <span className="text-xs text-[var(--color-text-subtle)]">
              Actualizado {updatedLabel}
            </span>
          ) : null}
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={staffQuery.isFetching}
            onClick={() => {
              void staffQuery.refetch()
              if (esAdmin) void adminQuery.refetch()
            }}
          >
            <RefreshCw
              className={staffQuery.isFetching ? 'h-4 w-4 animate-spin' : 'h-4 w-4'}
              aria-hidden
            />
            Actualizar
          </Button>
        </div>
      </header>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          title="Alertas pendientes"
          value={data.alertas.pendientes.total}
          subtitle={`${data.alertas.revisadas_ultimas_24h} revisadas en 24 h`}
          icon={AlertTriangle}
          accentClassName="border-[var(--destructive)]/20"
          onClick={() => onNavigate('/seguimiento')}
        />
        <KpiCard
          title="Casos activos"
          value={data.casos.activos}
          subtitle={`${data.casos.cerrados} cerrados · ${data.casos.total} total`}
          icon={ClipboardList}
          onClick={() => onNavigate('/casos')}
        />
        <KpiCard
          title="Telegram vinculado"
          value={data.casos.con_telegram_vinculado}
          subtitle="Pacientes con chat activo"
          icon={MessageCircle}
          onClick={() => onNavigate('/seguimiento/casos')}
        />
        <KpiCard
          title="Recordatorios vencidos"
          value={data.recordatorios.pendientes_vencidos}
          subtitle={`${data.recordatorios.enviados_ultimas_24h} enviados en 24 h`}
          icon={Bell}
          onClick={() => onNavigate('/casos')}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <AlertsTrendChart serie={data.serie_alertas_7d} />
        <SeverityBreakdown
          pendientes={data.alertas.pendientes}
          onNavigateSeguimiento={() => onNavigate('/seguimiento')}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <RecentAlertsList alertas={data.alertas_recientes} onNavigate={onNavigate} />
        <KpiCard
          title="Urgentes sin revisar"
          value={data.alertas.pendientes.urgente}
          subtitle="Requieren atención prioritaria"
          icon={Stethoscope}
          accentClassName="border-[var(--destructive)]/30 bg-[var(--destructive)]/5"
          onClick={() => onNavigate('/seguimiento')}
        />
      </div>

      {esAdmin ? (
        <SystemHealthPanel
          data={adminQuery.data}
          isLoading={adminQuery.isLoading}
          onNavigate={onNavigate}
        />
      ) : null}
    </div>
  )
}
