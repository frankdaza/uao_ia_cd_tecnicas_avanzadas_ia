import { useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ApiError, listarMedicos } from '@/lib/api'
import { formatFechaAlta } from '@/lib/formatFecha'
import { MedicoActivoBadge } from './medicoActivoBadge'

interface MedicosListPageProps {
  onNavigate: (path: string) => void
}

/** Listado del catálogo de médicos (admin). */
export function MedicosListPage({ onNavigate }: MedicosListPageProps) {
  const q = useQuery({
    queryKey: ['admin', 'medicos'],
    queryFn: () => listarMedicos({ limit: 100 }),
  })

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">
            Catálogo de médicos
          </h2>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Cirujanos y médicos tratantes asociados a casos postoperatorio.
          </p>
        </div>
        <Button type="button" onClick={() => onNavigate('/admin/medicos/nuevo')}>
          <Plus className="h-4 w-4" aria-hidden />
          Nuevo médico
        </Button>
      </div>

      {q.isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Cargando médicos…</p>
      ) : null}

      {q.isError ? (
        <p className="text-sm text-[var(--destructive)]">
          {q.error instanceof ApiError
            ? (q.error.detail ?? q.error.message)
            : 'No se pudo cargar el catálogo de médicos.'}
        </p>
      ) : null}

      {q.data && q.data.items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-[var(--border)] p-8 text-center text-sm text-[var(--color-text-muted)]">
          No hay médicos registrados. Cree el primero con el botón superior.
        </p>
      ) : null}

      {q.data && q.data.items.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-[var(--color-surface)] text-xs uppercase tracking-wide text-[var(--color-text-subtle)]">
              <tr>
                <th className="px-4 py-3 font-medium">Código</th>
                <th className="px-4 py-3 font-medium">Nombre</th>
                <th className="px-4 py-3 font-medium">Especialidad</th>
                <th className="px-4 py-3 font-medium">Estado</th>
                <th className="px-4 py-3 font-medium">Alta</th>
                <th className="px-4 py-3 font-medium sr-only">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {q.data.items.map((row) => (
                <tr key={row.id} className="hover:bg-[var(--accent)]/40">
                  <td className="px-4 py-3 font-mono text-xs">{row.codigo_registro}</td>
                  <td className="px-4 py-3">{row.nombre_completo}</td>
                  <td className="px-4 py-3 text-[var(--color-text-muted)]">
                    {row.especialidad ?? '—'}
                  </td>
                  <td className="px-4 py-3">
                    <MedicoActivoBadge activo={row.activo} />
                  </td>
                  <td className="px-4 py-3 text-[var(--color-text-muted)] whitespace-nowrap">
                    {formatFechaAlta(row.created_at)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => onNavigate(`/admin/medicos/${row.id}`)}
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
