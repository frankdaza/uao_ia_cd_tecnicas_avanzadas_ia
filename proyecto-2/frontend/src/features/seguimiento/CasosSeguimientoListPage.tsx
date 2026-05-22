import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { ApiError, listStaffAlertas, listStaffCasos } from '@/lib/api'
import { formatFechaSolo } from '@/lib/formatFecha'
import { casoSeguimientoPath, SEGUIMIENTO_PATH } from './seguimientoPaths'

interface CasosSeguimientoListPageProps {
  onNavigate: (path: string) => void
}

/** Casos activos con conteo de alertas pendientes por caso. */
export function CasosSeguimientoListPage({ onNavigate }: CasosSeguimientoListPageProps) {
  const casosQ = useQuery({
    queryKey: ['staff', 'casos', 'activo'],
    queryFn: () => listStaffCasos({ estado: 'activo', limit: 100 }),
  })

  const alertasQ = useQuery({
    queryKey: ['staff', 'alertas', 'pendientes-conteo'],
    queryFn: () => listStaffAlertas({ revisado: false, limit: 100 }),
  })

  const pendientesPorCaso = useMemo(() => {
    const map = new Map<string, number>()
    for (const a of alertasQ.data?.items ?? []) {
      map.set(a.caso_id, (map.get(a.caso_id) ?? 0) + 1)
    }
    return map
  }, [alertasQ.data])

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">
            Casos en seguimiento
          </h2>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Casos activos con indicador de alertas de triage pendientes.
          </p>
        </div>
        <Button type="button" variant="outline" size="sm" onClick={() => onNavigate(SEGUIMIENTO_PATH)}>
          Bandeja de alertas
        </Button>
      </div>

      {casosQ.isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Cargando casos…</p>
      ) : null}

      {(casosQ.isError || alertasQ.isError) && (
        <p className="text-sm text-[var(--destructive)]">
          {casosQ.error instanceof ApiError
            ? (casosQ.error.detail ?? casosQ.error.message)
            : alertasQ.error instanceof ApiError
              ? (alertasQ.error.detail ?? alertasQ.error.message)
              : 'No se pudo cargar el listado.'}
        </p>
      )}

      {casosQ.data && casosQ.data.items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-[var(--border)] p-8 text-center text-sm text-[var(--color-text-muted)]">
          No hay casos activos.
        </p>
      ) : null}

      {casosQ.data && casosQ.data.items.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-[var(--color-surface)] text-xs uppercase tracking-wide text-[var(--color-text-subtle)]">
              <tr>
                <th className="px-4 py-3 font-medium">Paciente</th>
                <th className="px-4 py-3 font-medium">Cirujano</th>
                <th className="px-4 py-3 font-medium">Cirugía</th>
                <th className="px-4 py-3 font-medium">Telegram</th>
                <th className="px-4 py-3 font-medium">Alertas</th>
                <th className="px-4 py-3 font-medium sr-only">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {casosQ.data.items.map((caso) => {
                const n = pendientesPorCaso.get(caso.id) ?? 0
                return (
                  <tr key={caso.id} className="hover:bg-[var(--color-surface)]/60">
                    <td className="px-4 py-3">
                      <div className="font-medium text-[var(--color-text)]">{caso.paciente_nombre}</div>
                      <div className="text-xs text-[var(--color-text-muted)]">{caso.paciente_doc_id}</div>
                    </td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">{caso.cirujano_nombre}</td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">
                      {formatFechaSolo(caso.fecha_cirugia)}
                    </td>
                    <td className="px-4 py-3 text-[var(--color-text-muted)]">
                      {caso.vinculado_telegram ? 'Vinculado' : 'Pendiente'}
                    </td>
                    <td className="px-4 py-3">
                      {n > 0 ? (
                        <span className="inline-flex min-w-[1.5rem] items-center justify-center rounded-full bg-[var(--destructive)] px-2 py-0.5 text-xs font-semibold text-white">
                          {n}
                        </span>
                      ) : (
                        <span className="text-xs text-[var(--color-text-subtle)]">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => onNavigate(casoSeguimientoPath(caso.id))}
                      >
                        Abrir
                      </Button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  )
}
