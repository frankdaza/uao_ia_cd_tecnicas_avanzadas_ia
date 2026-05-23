import { useQuery } from '@tanstack/react-query'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { getAdminConfig, getAdminMetricas } from '@/lib/adminApi'

type Props = {
  adminKey: string
}

export function AdminDashboardPage({ adminKey }: Props) {
  const metricas = useQuery({
    queryKey: ['admin', 'metricas', adminKey],
    queryFn: () => getAdminMetricas(adminKey),
  })
  const config = useQuery({
    queryKey: ['admin', 'config', adminKey],
    queryFn: () => getAdminConfig(adminKey),
  })

  const vacioNegocio =
    !metricas.isLoading &&
    !metricas.isError &&
    metricas.data != null &&
    metricas.data.usuarios_total === 0 &&
    metricas.data.usuarios_activos_ultimos_7_dias === 0

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <TarjetaKpi
          titulo="Usuarios registrados"
          valor={metricas.data?.usuarios_total}
          cargando={metricas.isLoading}
          error={metricas.isError}
        />
        <TarjetaKpi
          titulo="Activos (últimos 7 días)"
          valor={metricas.data?.usuarios_activos_ultimos_7_dias}
          cargando={metricas.isLoading}
          error={metricas.isError}
        />
        <TarjetaKpi
          titulo="Sesiones (estimado)"
          valor={metricas.data?.sesiones_estimadas}
          subtitulo="Reservado en backend; puede figurar en 0"
          cargando={metricas.isLoading}
          error={metricas.isError}
        />
        <TarjetaKpi
          titulo="Versión de configuración"
          valor={config.data?.version}
          subtitulo="Control optimista en base de datos"
          cargando={config.isLoading}
          error={config.isError}
        />
      </div>
      {vacioNegocio ? (
        <div
          className="rounded-xl border border-dashed border-border bg-muted/30 p-6 text-center text-sm text-muted-foreground"
          role="status"
        >
          Aún no hay usuarios registrados en el sistema. Cuando existan cuentas, los totales se actualizarán aquí.
        </div>
      ) : null}
      <div className="rounded-xl border border-border bg-card p-4 text-sm text-muted-foreground">
        <p>
          Los cambios en modelo y prompts se aplican en la <strong className="text-foreground">siguiente</strong>{' '}
          petición del agente (no se interrumpe un stream SSE ya abierto).
        </p>
      </div>
    </div>
  )
}

function TarjetaKpi({
  titulo,
  valor,
  subtitulo,
  cargando,
  error,
}: {
  titulo: string
  valor: number | undefined
  subtitulo?: string
  cargando: boolean
  error: boolean
}) {
  return (
    <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <p className="text-sm font-medium text-muted-foreground">{titulo}</p>
      {cargando ? (
        <Skeleton className="mt-3 h-9 w-24" />
      ) : error ? (
        <p className="mt-3 text-sm text-destructive">No se pudieron cargar los datos.</p>
      ) : (
        <p className="mt-3 font-display text-3xl font-semibold tabular-nums text-foreground">{valor ?? '—'}</p>
      )}
      {subtitulo ? <p className="mt-2 text-xs text-muted-foreground">{subtitulo}</p> : null}
      {error ? (
        <Badge variant="destructive" className="mt-2">
          Error
        </Badge>
      ) : null}
    </div>
  )
}
