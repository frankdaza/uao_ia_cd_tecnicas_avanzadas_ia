import {
  Activity,
  Bot,
  Database,
  Stethoscope,
  Timer,
  Webhook,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import type { ResumenDashboardAdmin } from '@/lib/schemas'
import { cn } from '@/lib/cn'

interface SystemHealthPanelProps {
  data: ResumenDashboardAdmin | undefined
  isLoading: boolean
  onNavigate: (path: string) => void
}

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <Badge
      variant={ok ? 'default' : 'destructive'}
      className={cn(
        ok && 'bg-[var(--color-accent)]/20 text-[var(--color-accent-dark)] border-transparent',
      )}
    >
      {label}
    </Badge>
  )
}

/** Panel de salud del sistema (solo administradores). */
export function SystemHealthPanel({ data, isLoading, onNavigate }: SystemHealthPanelProps) {
  if (isLoading && !data) {
    return (
      <section className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-28" />
          ))}
        </div>
      </section>
    )
  }

  if (!data) return null

  const { medicos, procedimientos, config_operativa: cfg, telegram_webhook: tg } = data

  const items = [
    {
      title: 'Médicos',
      icon: Stethoscope,
      value: `${medicos.activos} activos`,
      detail: `${medicos.total} en catálogo`,
      path: '/admin/medicos',
    },
    {
      title: 'Protocolos indexados',
      icon: Database,
      value: `${procedimientos.ok} listos`,
      detail: `${procedimientos.pendiente} pend. · ${procedimientos.error} error`,
      path: '/admin/procedimientos',
    },
    {
      title: 'Job recordatorios',
      icon: Timer,
      value: cfg.recordatorios_job_habilitado ? 'Activo' : 'Pausado',
      detail: `Cada ${cfg.recordatorios_job_interval_seg} s`,
      path: '/admin/recordatorios',
      ok: cfg.recordatorios_job_habilitado,
    },
    {
      title: 'HITL escalamiento',
      icon: Bot,
      value: cfg.agente_hitl_habilitado ? 'Habilitado' : 'Desactivado',
      detail: 'Escalamiento clínico del agente',
      path: '/admin/agente-hitl',
      ok: cfg.agente_hitl_habilitado,
    },
    {
      title: 'Webhook Telegram',
      icon: Webhook,
      value: tg.configurado ? 'Configurado' : 'Sin configurar',
      detail:
        tg.pending_update_count != null
          ? `${tg.pending_update_count} updates en cola`
          : 'Estado no disponible',
      path: '/admin/telegram',
      ok: tg.configurado,
    },
    {
      title: 'Índice procedimientos',
      icon: Activity,
      value: `${procedimientos.total} total`,
      detail: 'Estado de indexación Qdrant',
      path: '/admin/procedimientos',
    },
  ]

  return (
    <section className="space-y-4 border-t border-[var(--border)] pt-8">
      <div>
        <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">
          Sistema y administración
        </h2>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Estado operativo de integraciones y catálogos
        </p>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => {
          const Icon = item.icon
          return (
            <Card
              key={item.title}
              className="cursor-pointer transition-shadow hover:shadow-md hover:border-[var(--color-accent)]/30"
              onClick={() => onNavigate(item.path)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  onNavigate(item.path)
                }
              }}
            >
              <CardHeader className="flex flex-row items-start justify-between pb-2">
                <CardTitle className="text-sm font-medium">{item.title}</CardTitle>
                <Icon className="h-4 w-4 text-[var(--color-accent)]" aria-hidden />
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="font-semibold text-[var(--color-text)]">{item.value}</p>
                <p className="text-xs text-[var(--color-text-muted)]">{item.detail}</p>
                {'ok' in item && item.ok != null ? (
                  <StatusPill ok={item.ok} label={item.ok ? 'OK' : 'Revisar'} />
                ) : null}
                {item.title === 'Webhook Telegram' && tg.last_error_message ? (
                  <p className="text-xs text-[var(--destructive)] line-clamp-2">
                    {tg.last_error_message}
                  </p>
                ) : null}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </section>
  )
}
