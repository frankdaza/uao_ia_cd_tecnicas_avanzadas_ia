import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError, actualizarMedico, desactivarMedico, obtenerMedico } from '@/lib/api'
import type { Medico } from '@/lib/schemas'
import { formatFechaAlta } from '@/lib/formatFecha'
import { MedicoActivoBadge } from './medicoActivoBadge'
import { MedicoParcheSchema } from './medicosValidacion'

interface MedicoDetallePageProps {
  id: string
  onNavigate: (path: string) => void
}

const MENSAJE_DESACTIVAR_409 =
  'No se puede desactivar: tiene casos postoperatorio activos asociados.'

function mensajeErrorDesactivar(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 409) {
      return MENSAJE_DESACTIVAR_409
    }
    return err.detail ?? err.message
  }
  return 'No se pudo desactivar el médico.'
}

/** Detalle, edición y desactivación de un médico del catálogo. */
export function MedicoDetallePage({ id, onNavigate }: MedicoDetallePageProps) {
  const qc = useQueryClient()
  const q = useQuery({
    queryKey: ['admin', 'medicos', id],
    queryFn: () => obtenerMedico(id),
  })

  const mutDesactivar = useMutation({
    mutationFn: () => desactivarMedico(id),
    onSuccess: async () => {
      toast.success('Médico desactivado.')
      await qc.invalidateQueries({ queryKey: ['admin', 'medicos'] })
      await qc.invalidateQueries({ queryKey: ['admin', 'medicos', id] })
    },
    onError: (err: unknown) => {
      toast.error(mensajeErrorDesactivar(err))
    },
  })

  if (q.isLoading) {
    return <p className="text-sm text-[var(--color-text-muted)]">Cargando médico…</p>
  }

  if (q.isError || !q.data) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-[var(--destructive)]">Médico no encontrado.</p>
        <Button type="button" variant="outline" onClick={() => onNavigate('/admin/medicos')}>
          Volver al listado
        </Button>
      </div>
    )
  }

  const fila = q.data

  const handleDesactivar = () => {
    if (!fila.activo) return
    const ok = window.confirm('¿Desactivar este médico? No se eliminará del historial.')
    if (ok) mutDesactivar.mutate()
  }

  return (
    <div className="mx-auto max-w-lg space-y-8">
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="-ml-2"
        onClick={() => onNavigate('/admin/medicos')}
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Volver al listado
      </Button>

      <header className="space-y-3">
        <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">
          {fila.nombre_completo}
        </h2>
        <p className="font-mono text-sm text-[var(--color-text-muted)]">{fila.codigo_registro}</p>
        <div className="flex flex-wrap items-center gap-3">
          <MedicoActivoBadge activo={fila.activo} />
          {fila.especialidad ? (
            <span className="text-sm text-[var(--color-text-muted)]">{fila.especialidad}</span>
          ) : null}
          <span className="text-xs text-[var(--color-text-subtle)]">
            Alta: {formatFechaAlta(fila.created_at)}
          </span>
        </div>
      </header>

      <DetalleMedicoForm
        key={`${fila.id}-${fila.codigo_registro}-${fila.nombre_completo}-${fila.especialidad ?? ''}-${fila.activo}`}
        fila={fila}
        id={id}
      />

      <section className="rounded-lg border border-[var(--border)] p-4">
        <h3 className="text-sm font-semibold text-[var(--color-text)]">Desactivar médico</h3>
        <p className="mt-1 text-xs text-[var(--color-text-muted)]">
          Marca el registro como inactivo. No se puede desactivar si tiene casos postoperatorio
          activos asociados a su código de registro.
        </p>
        <Button
          type="button"
          variant="destructive"
          className="mt-3"
          disabled={!fila.activo || mutDesactivar.isPending}
          onClick={handleDesactivar}
        >
          {mutDesactivar.isPending ? 'Desactivando…' : 'Desactivar médico'}
        </Button>
      </section>
    </div>
  )
}

function DetalleMedicoForm({ fila, id }: { fila: Medico; id: string }) {
  const qc = useQueryClient()
  const [codigoRegistro, setCodigoRegistro] = useState(fila.codigo_registro)
  const [nombreCompleto, setNombreCompleto] = useState(fila.nombre_completo)
  const [especialidad, setEspecialidad] = useState(fila.especialidad ?? '')

  const mut = useMutation({
    mutationFn: async () => {
      const parcial: {
        codigo_registro?: string
        nombre_completo?: string
        especialidad?: string | null
      } = {}
      const codigoTrim = codigoRegistro.trim()
      const nombreTrim = nombreCompleto.trim()
      const espTrim = especialidad.trim()

      if (codigoTrim !== fila.codigo_registro) parcial.codigo_registro = codigoTrim
      if (nombreTrim !== fila.nombre_completo) parcial.nombre_completo = nombreTrim
      const espActual = fila.especialidad ?? ''
      if (espTrim !== espActual) {
        parcial.especialidad = espTrim || null
      }

      MedicoParcheSchema.parse(parcial)
      return actualizarMedico(id, parcial)
    },
    onSuccess: async () => {
      toast.success('Datos del médico actualizados.')
      await qc.invalidateQueries({ queryKey: ['admin', 'medicos'] })
      await qc.invalidateQueries({ queryKey: ['admin', 'medicos', id] })
    },
    onError: (err: unknown) => {
      toast.error(
        err instanceof ApiError
          ? (err.detail ?? err.message)
          : err instanceof Error
            ? err.message
            : 'Error al guardar.',
      )
    },
  })

  const datosCambiados =
    codigoRegistro.trim() !== fila.codigo_registro ||
    nombreCompleto.trim() !== fila.nombre_completo ||
    especialidad.trim() !== (fila.especialidad ?? '')

  return (
    <section className="space-y-4 rounded-lg border border-[var(--border)] p-4">
      <h3 className="text-sm font-semibold text-[var(--color-text)]">Editar datos</h3>
      <div className="space-y-2">
        <Label htmlFor="det-codigo">Código de registro</Label>
        <Input
          id="det-codigo"
          value={codigoRegistro}
          onChange={(e) => setCodigoRegistro(e.target.value)}
          disabled={mut.isPending || !fila.activo}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="det-nombre">Nombre completo</Label>
        <Input
          id="det-nombre"
          value={nombreCompleto}
          onChange={(e) => setNombreCompleto(e.target.value)}
          disabled={mut.isPending || !fila.activo}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="det-especialidad">Especialidad</Label>
        <Input
          id="det-especialidad"
          value={especialidad}
          onChange={(e) => setEspecialidad(e.target.value)}
          placeholder="Opcional"
          disabled={mut.isPending || !fila.activo}
        />
      </div>
      {!fila.activo ? (
        <p className="text-xs text-[var(--color-text-muted)]">
          El médico está inactivo; reactive desde soporte o registre uno nuevo.
        </p>
      ) : null}
      <Button
        type="button"
        variant="secondary"
        disabled={!datosCambiados || mut.isPending || !fila.activo}
        onClick={() => mut.mutate()}
      >
        {mut.isPending ? 'Guardando…' : 'Guardar cambios'}
      </Button>
    </section>
  )
}
