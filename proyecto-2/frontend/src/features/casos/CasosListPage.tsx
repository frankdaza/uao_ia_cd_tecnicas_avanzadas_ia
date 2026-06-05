import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Loader2, Plus, RefreshCw, Unlink } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/features/auth/AuthContext'
import {
  ApiError,
  desvincularTelegramCaso,
  generateCodigoEmparejamiento,
  listStaffCasos,
  listStaffTiposProcedimiento,
} from '@/lib/api'
import { formatFechaSolo } from '@/lib/formatFecha'
import type { Caso, CodigoEmparejamiento, TipoProcedimientoOpcion } from '@/lib/schemas'
import { CodigoEmparejamientoModal } from './CodigoEmparejamientoModal'
import { VinculoTelegramBadge } from './VinculoTelegramBadge'

interface CasosListPageProps {
  onNavigate: (path: string) => void
}

function nombreProcedimiento(
  caso: Caso,
  mapa: Map<string, { codigo: string; nombre: string }>,
): string {
  const t = mapa.get(caso.tipo_procedimiento_id)
  return t ? `${t.codigo} — ${t.nombre}` : caso.tipo_procedimiento_id.slice(0, 8)
}

/** Listado de casos activos y regeneración de código (UC-MVP-02). */
export function CasosListPage({ onNavigate }: CasosListPageProps) {
  const { user } = useAuth()
  const esAdmin = user?.rol === 'admin'
  const qc = useQueryClient()
  const [modalCodigo, setModalCodigo] = useState<{
    data: CodigoEmparejamiento
    pacienteNombre: string
  } | null>(null)

  const tiposQ = useQuery({
    queryKey: ['staff', 'tipos-procedimiento'],
    queryFn: listStaffTiposProcedimiento,
  })

  const casosQ = useQuery({
    queryKey: ['staff', 'casos', 'activo'],
    queryFn: () => listStaffCasos({ estado: 'activo', limit: 100 }),
  })

  const mapaTipos = new Map<string, { codigo: string; nombre: string }>(
    (tiposQ.data?.items ?? []).map((t: TipoProcedimientoOpcion) => [
      t.id,
      { codigo: t.codigo, nombre: t.nombre },
    ]),
  )

  const regenerarMut = useMutation({
    mutationFn: async (caso: Caso) => generateCodigoEmparejamiento(caso.id),
    onSuccess: async (data, caso) => {
      await qc.invalidateQueries({ queryKey: ['staff', 'casos'] })
      setModalCodigo({ data, pacienteNombre: caso.paciente_nombre })
      toast.success('Código regenerado. El código anterior ya no es válido.')
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof ApiError
          ? (err.detail ?? err.message)
          : 'No se pudo generar el código.'
      toast.error(msg)
    },
  })

  const desvincularMut = useMutation({
    mutationFn: async (caso: Caso) => desvincularTelegramCaso(caso.id),
    onSuccess: async (data) => {
      await qc.invalidateQueries({ queryKey: ['staff', 'casos'] })
      toast.success('Dispositivo Telegram desvinculado del caso.')
      if (!data.notificado_telegram) {
        toast.warning(
          'El caso quedó desvinculado, pero no se pudo enviar la notificación por Telegram.',
        )
      }
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof ApiError
          ? (err.detail ?? err.message)
          : 'No se pudo desvincular el dispositivo.'
      toast.error(msg)
    },
  })

  const confirmarDesvincular = (caso: Caso) => {
    const ok = window.confirm(
      `¿Desvincular el dispositivo Telegram de ${caso.paciente_nombre}? ` +
        'El paciente recibirá un aviso por Telegram. El historial en Seguimiento se conserva. ' +
        'Deberá generar un código nuevo para volver a vincular.',
    )
    if (ok) {
      desvincularMut.mutate(caso)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">
            Casos postoperatorio
          </h2>
          <p className="mt-1 text-sm text-[var(--color-text-muted)]">
            Casos activos y vínculo con Telegram del paciente.
          </p>
        </div>
        <Button type="button" onClick={() => onNavigate('/casos/nuevo')}>
          <Plus className="h-4 w-4" aria-hidden />
          Nuevo caso
        </Button>
      </div>

      {casosQ.isLoading ? (
        <p className="text-sm text-[var(--color-text-muted)]">Cargando casos…</p>
      ) : null}

      {casosQ.isError ? (
        <p className="text-sm text-[var(--destructive)]">
          {casosQ.error instanceof ApiError
            ? (casosQ.error.detail ?? casosQ.error.message)
            : 'No se pudo cargar el listado.'}
        </p>
      ) : null}

      {casosQ.data && casosQ.data.items.length === 0 ? (
        <p className="rounded-lg border border-dashed border-[var(--border)] p-8 text-center text-sm text-[var(--color-text-muted)]">
          No hay casos activos. Registre el primero con «Nuevo caso».
        </p>
      ) : null}

      {casosQ.data && casosQ.data.items.length > 0 ? (
        <div className="overflow-x-auto rounded-lg border border-[var(--border)]">
          <table className="w-full min-w-[960px] text-left text-sm">
            <thead className="bg-[var(--color-surface)] text-xs uppercase tracking-wide text-[var(--color-text-subtle)]">
              <tr>
                <th className="px-4 py-3 font-medium">Paciente</th>
                <th className="px-4 py-3 font-medium">Procedimiento</th>
                <th className="px-4 py-3 font-medium">Cirujano</th>
                <th className="px-4 py-3 font-medium">Cirugía</th>
                <th className="px-4 py-3 font-medium">Telegram</th>
                <th className="px-4 py-3 font-medium">Código</th>
                {esAdmin ? (
                  <th className="px-4 py-3 font-medium">Desvincular</th>
                ) : null}
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {casosQ.data.items.map((caso) => (
                <tr key={caso.id} className="hover:bg-[var(--color-surface)]/60">
                  <td className="px-4 py-3">
                    <div className="font-medium text-[var(--color-text)]">{caso.paciente_nombre}</div>
                    <div className="text-xs text-[var(--color-text-muted)]">{caso.paciente_doc_id}</div>
                  </td>
                  <td className="px-4 py-3 text-[var(--color-text-muted)]">
                    {nombreProcedimiento(caso, mapaTipos)}
                  </td>
                  <td className="px-4 py-3 text-[var(--color-text-muted)]">{caso.cirujano_nombre}</td>
                  <td className="px-4 py-3 text-[var(--color-text-muted)]">
                    {formatFechaSolo(caso.fecha_cirugia)}
                  </td>
                  <td className="px-4 py-3">
                    <VinculoTelegramBadge vinculado={caso.vinculado_telegram} />
                    {!caso.vinculado_telegram && caso.codigo_emparejamiento_activo ? (
                      <p className="mt-1 font-mono text-[10px] text-[var(--color-text-subtle)]">
                        Código pendiente: {caso.codigo_emparejamiento_activo}
                      </p>
                    ) : null}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      disabled={regenerarMut.isPending}
                      onClick={() => regenerarMut.mutate(caso)}
                    >
                      {regenerarMut.isPending && regenerarMut.variables?.id === caso.id ? (
                        <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
                      ) : (
                        <RefreshCw className="h-3 w-3" aria-hidden />
                      )}
                      Regenerar código
                    </Button>
                  </td>
                  {esAdmin ? (
                    <td className="px-4 py-3 text-right">
                      {caso.vinculado_telegram ? (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          className="text-[var(--destructive)] hover:text-[var(--destructive)]"
                          disabled={desvincularMut.isPending}
                          onClick={() => confirmarDesvincular(caso)}
                        >
                          {desvincularMut.isPending && desvincularMut.variables?.id === caso.id ? (
                            <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
                          ) : (
                            <Unlink className="h-3 w-3" aria-hidden />
                          )}
                          Desvincular
                        </Button>
                      ) : (
                        <span className="text-xs text-[var(--color-text-subtle)]">—</span>
                      )}
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {modalCodigo ? (
        <CodigoEmparejamientoModal
          data={modalCodigo.data}
          pacienteNombre={modalCodigo.pacienteNombre}
          onClose={() => setModalCodigo(null)}
        />
      ) : null}
    </div>
  )
}
