import { useQuery } from '@tanstack/react-query'
import { Loader2, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ApiError, listAdminProcedimientos } from '@/lib/api'
import type { Procedimiento } from '@/lib/schemas'
import { formatFechaAlta } from '@/lib/formatFecha'
import { IndexacionEstadoBadge } from './indexacionEstado'

interface ProcedimientosListPageProps {
  onNavigate: (path: string) => void
}

function hayPendientes(items: Procedimiento[]): boolean {
  return items.some((p) => p.indexacion_estado === 'pendiente')
}

/** Listado del catálogo de procedimientos (UC-MVP-01). */
export function ProcedimientosListPage({ onNavigate }: ProcedimientosListPageProps) {
  const q = useQuery({
    queryKey: ['admin', 'procedimientos'],
    queryFn: () => listAdminProcedimientos({ limit: 100 }),
    refetchInterval: (query) => (hayPendientes(query.state.data?.items ?? []) ? 3000 : false),
  })

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">
            Catálogo de procedimientos
          </h2>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Protocolos PDF e indexación en Qdrant para el agente TAAM.
          </p>
        </div>
        <Button type="button" onClick={() => onNavigate('/admin/procedimientos/nuevo')}>
          <Plus className="h-4 w-4" aria-hidden />
          Nuevo procedimiento
        </Button>
      </div>

      {q.isFetching && q.data ? (
        <p className="flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
          <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
          Actualizando estados de indexación…
        </p>
      ) : null}

      {q.isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Cargando catálogo…</p>
      ) : null}

      {q.isError ? (
        <p className="text-sm text-[var(--destructive)]">
          {q.error instanceof ApiError
            ? (q.error.detail ?? q.error.message)
            : 'No se pudo cargar el catálogo.'}
        </p>
      ) : null}

      {q.data && q.data.items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-[var(--border)] p-8 text-center text-sm text-[var(--color-text-muted)]">
          No hay procedimientos registrados. Cree el primero con el botón superior.
        </p>
      ) : null}

      {q.data && q.data.items.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-[var(--color-surface)] text-xs uppercase tracking-wide text-[var(--color-text-subtle)]">
              <tr>
                <th className="px-4 py-3 font-medium">Código</th>
                <th className="px-4 py-3 font-medium">Nombre</th>
                <th className="px-4 py-3 font-medium">Versión vector</th>
                <th className="px-4 py-3 font-medium">Indexación</th>
                <th className="px-4 py-3 font-medium">Alta</th>
                <th className="px-4 py-3 font-medium sr-only">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {q.data.items.map((row) => (
                <tr key={row.id} className="hover:bg-[var(--accent)]/40">
                  <td className="px-4 py-3 font-mono text-xs">{row.codigo}</td>
                  <td className="px-4 py-3">{row.nombre}</td>
                  <td className="px-4 py-3 text-[var(--color-text-muted)]">
                    {row.qdrant_collection_version ?? '—'}
                  </td>
                  <td className="px-4 py-3">
                    <IndexacionEstadoBadge estado={row.indexacion_estado} />
                  </td>
                  <td className="px-4 py-3 text-[var(--color-text-muted)] whitespace-nowrap">
                    {formatFechaAlta(row.created_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => onNavigate(`/admin/procedimientos/${row.id}`)}
                    >
                      Ver detalle
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  )
}
