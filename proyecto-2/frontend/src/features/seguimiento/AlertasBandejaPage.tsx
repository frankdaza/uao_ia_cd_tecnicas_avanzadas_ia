import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { ApiError, listStaffAlertas, markAlertaRevisada } from '@/lib/api'
import type { AlertaTriage, SeveridadTriage } from '@/lib/schemas'
import { AlertaCard } from './AlertaCard'
import { SEGUIMIENTO_CASOS_PATH } from './seguimientoPaths'

const POLL_MS = 30_000

interface AlertasBandejaPageProps {
  onNavigate: (path: string) => void
}

/** Bandeja de alertas de triage pendientes (UC-MVP-05). */
export function AlertasBandejaPage({ onNavigate }: AlertasBandejaPageProps) {
  const qc = useQueryClient()
  const [mostrarRevisadas, setMostrarRevisadas] = useState(false)
  const [filtroSeveridad, setFiltroSeveridad] = useState<SeveridadTriage | ''>('')
  const prevPendientesRef = useRef<number | null>(null)

  const alertasQ = useQuery({
    queryKey: ['staff', 'alertas', mostrarRevisadas, filtroSeveridad],
    queryFn: () =>
      listStaffAlertas({
        revisado: mostrarRevisadas,
        severidad: filtroSeveridad || undefined,
        limit: 100,
      }),
    refetchInterval: POLL_MS,
  })

  useEffect(() => {
    if (mostrarRevisadas || !alertasQ.data) return
    const n = alertasQ.data.items.length
    if (prevPendientesRef.current != null && n > prevPendientesRef.current) {
      const diff = n - prevPendientesRef.current
      toast.info(
        diff === 1 ? 'Hay 1 alerta nueva pendiente.' : `Hay ${diff} alertas nuevas pendientes.`,
      )
    }
    prevPendientesRef.current = n
  }, [alertasQ.data, mostrarRevisadas])

  const marcarMut = useMutation({
    mutationFn: (alerta: AlertaTriage) => markAlertaRevisada(alerta.id),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['staff', 'alertas'] })
      await qc.invalidateQueries({ queryKey: ['staff', 'resumen'] })
      toast.success('Alerta marcada como revisada.')
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof ApiError
          ? (err.detail ?? err.message)
          : 'No se pudo marcar la alerta.'
      toast.error(msg)
    },
  })

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">
            Bandeja de alertas
          </h2>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Revise el triage automático y valide con el hilo del paciente. Actualización cada 30 s.
          </p>
        </div>
        <Button type="button" variant="outline" size="sm" onClick={() => onNavigate(SEGUIMIENTO_CASOS_PATH)}>
          Ver casos
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-3 rounded-lg border border-[var(--border)] p-3">
        <label className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
          <input
            type="checkbox"
            checked={mostrarRevisadas}
            onChange={(e) => setMostrarRevisadas(e.target.checked)}
            className="rounded border-[var(--border)]"
          />
          Mostrar revisadas
        </label>
        <label className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
          Severidad
          <select
            value={filtroSeveridad}
            onChange={(e) => setFiltroSeveridad(e.target.value as SeveridadTriage | '')}
            className="rounded-md border border-[var(--border)] bg-transparent px-2 py-1 text-sm"
          >
            <option value="">Todas</option>
            <option value="urgente">Urgente</option>
            <option value="seguimiento">Seguimiento</option>
            <option value="info">Información</option>
          </select>
        </label>
      </div>

      {alertasQ.isLoading ? (
        <p className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          Cargando alertas…
        </p>
      ) : null}

      {alertasQ.isError ? (
        <p className="text-sm text-[var(--destructive)]">
          {alertasQ.error instanceof ApiError
            ? (alertasQ.error.detail ?? alertasQ.error.message)
            : 'No se pudo cargar la bandeja.'}
        </p>
      ) : null}

      {alertasQ.data && alertasQ.data.items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-[var(--border)] p-8 text-center text-sm text-[var(--color-text-muted)]">
          {mostrarRevisadas
            ? 'No hay alertas con los filtros seleccionados.'
            : 'No hay alertas pendientes de revisión. Buen trabajo.'}
        </p>
      ) : null}

      {alertasQ.data && alertasQ.data.items.length > 0 ? (
        <ul className="space-y-4">
          {alertasQ.data.items.map((alerta) => (
            <li key={alerta.id}>
              <AlertaCard
                alerta={alerta}
                onNavigate={onNavigate}
                onMarcarRevisado={(a) => marcarMut.mutate(a)}
                marcando={marcarMut.isPending && marcarMut.variables?.id === alerta.id}
                showMarcar={!mostrarRevisadas}
              />
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
