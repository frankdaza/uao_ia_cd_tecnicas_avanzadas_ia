import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from '@/features/auth/AuthContext'
import {
  ApiError,
  createStaffCaso,
  generateCodigoEmparejamiento,
  listStaffMedicos,
  listStaffTiposProcedimiento,
} from '@/lib/api'
import { CrearCasoBodySchema } from '@/lib/schemas'
import type { CodigoEmparejamiento, MedicoOpcion, TipoProcedimientoOpcion } from '@/lib/schemas'
import { CodigoEmparejamientoModal } from './CodigoEmparejamientoModal'
import { MedicoCombobox } from './MedicoCombobox'
import { TipoProcedimientoCombobox } from './TipoProcedimientoCombobox'

interface CasoNuevoPageProps {
  onNavigate: (path: string) => void
}

function fechaHoyIso(): string {
  return new Date().toISOString().slice(0, 10)
}

/** Formulario de alta de caso y generación de código (UC-MVP-02). */
export function CasoNuevoPage({ onNavigate }: CasoNuevoPageProps) {
  const { user } = useAuth()
  const qc = useQueryClient()
  const [tipoSeleccionado, setTipoSeleccionado] = useState<TipoProcedimientoOpcion | null>(null)
  const [pacienteDocId, setPacienteDocId] = useState('')
  const [pacienteNombre, setPacienteNombre] = useState('')
  const [medicoSeleccionado, setMedicoSeleccionado] = useState<MedicoOpcion | null>(null)
  const [fechaCirugia, setFechaCirugia] = useState(fechaHoyIso())
  const [notas, setNotas] = useState('')
  const [modalCodigo, setModalCodigo] = useState<{
    data: CodigoEmparejamiento
    pacienteNombre: string
  } | null>(null)

  const tiposQ = useQuery({
    queryKey: ['staff', 'tipos-procedimiento'],
    queryFn: listStaffTiposProcedimiento,
  })

  const medicosQ = useQuery({
    queryKey: ['staff', 'medicos'],
    queryFn: listStaffMedicos,
  })

  const crearMut = useMutation({
    mutationFn: async () => {
      if (!tipoSeleccionado) {
        throw new Error('Seleccione un tipo de procedimiento del catálogo.')
      }
      if (!medicoSeleccionado) {
        throw new Error('Seleccione un cirujano del catálogo.')
      }
      const body = CrearCasoBodySchema.parse({
        paciente_doc_id: pacienteDocId.trim(),
        paciente_nombre: pacienteNombre.trim(),
        tipo_procedimiento_id: tipoSeleccionado.id,
        cirujano_id: medicoSeleccionado.codigo_registro,
        cirujano_nombre: medicoSeleccionado.nombre_completo,
        fecha_cirugia: fechaCirugia,
        notas_especificas: notas.trim() || undefined,
      })
      const caso = await createStaffCaso(body)
      const codigo = await generateCodigoEmparejamiento(caso.id)
      return { caso, codigo }
    },
    onSuccess: async ({ caso, codigo }) => {
      await qc.invalidateQueries({ queryKey: ['staff', 'casos'] })
      toast.success('Caso registrado correctamente.')
      setModalCodigo({ data: codigo, pacienteNombre: caso.paciente_nombre })
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof ApiError
          ? (err.detail ?? err.message)
          : err instanceof Error
            ? err.message
            : 'No se pudo registrar el caso.'
      toast.error(msg)
    },
  })

  const bodyPreview = CrearCasoBodySchema.safeParse({
    paciente_doc_id: pacienteDocId.trim(),
    paciente_nombre: pacienteNombre.trim(),
    tipo_procedimiento_id: tipoSeleccionado?.id,
    cirujano_id: medicoSeleccionado?.codigo_registro ?? '',
    cirujano_nombre: medicoSeleccionado?.nombre_completo ?? '',
    fecha_cirugia: fechaCirugia,
    notas_especificas: notas.trim() || undefined,
  })

  const sinTiposIndexados =
    tiposQ.isSuccess && (tiposQ.data?.items.length ?? 0) === 0 && !tiposQ.isFetching

  const sinMedicosActivos =
    medicosQ.isSuccess && (medicosQ.data?.items.length ?? 0) === 0 && !medicosQ.isFetching

  const puedeEnviar =
    bodyPreview.success &&
    tipoSeleccionado != null &&
    medicoSeleccionado != null &&
    (tiposQ.data?.items.length ?? 0) > 0 &&
    (medicosQ.data?.items.length ?? 0) > 0 &&
    !crearMut.isPending

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="-ml-2"
        onClick={() => onNavigate('/casos')}
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Volver al listado
      </Button>

      <div>
        <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">Nuevo caso</h2>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Registre el caso y obtenga el código para que el paciente vincule Telegram.
        </p>
      </div>

      {sinTiposIndexados ? (
        <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 text-sm text-amber-900 dark:text-amber-200">
          No hay procedimientos con indexación lista. Un administrador debe cargar el catálogo y
          esperar estado <strong>listo</strong> antes de registrar casos.
        </p>
      ) : null}

      {sinMedicosActivos ? (
        <p className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-4 text-sm text-amber-900 dark:text-amber-200">
          No hay médicos activos en el catálogo.
          {user?.rol === 'admin' ? (
            <>
              {' '}
              <Button
                type="button"
                variant="link"
                className="h-auto p-0 text-amber-900 underline dark:text-amber-200"
                onClick={() => onNavigate('/admin/medicos')}
              >
                Gestionar médicos
              </Button>
            </>
          ) : (
            ' Solicite a un administrador que registre médicos.'
          )}
        </p>
      ) : null}

      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault()
          if (puedeEnviar) crearMut.mutate()
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="tipo-procedimiento-combobox">Tipo de procedimiento</Label>
          <TipoProcedimientoCombobox
            id="tipo-procedimiento-combobox"
            value={tipoSeleccionado}
            onChange={setTipoSeleccionado}
            items={tiposQ.data?.items ?? []}
            disabled={crearMut.isPending || sinTiposIndexados}
            isLoading={tiposQ.isLoading}
          />
          {tiposQ.isError ? (
            <p className="text-xs text-[var(--destructive)]">
              No se pudo cargar el catálogo de procedimientos. Intente de nuevo.
            </p>
          ) : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="paciente-doc">Documento del paciente</Label>
          <Input
            id="paciente-doc"
            value={pacienteDocId}
            onChange={(e) => setPacienteDocId(e.target.value)}
            placeholder="ej. PAC-DEMO-001"
            autoComplete="off"
            disabled={crearMut.isPending}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="paciente-nombre">Nombre del paciente</Label>
          <Input
            id="paciente-nombre"
            value={pacienteNombre}
            onChange={(e) => setPacienteNombre(e.target.value)}
            placeholder="Nombre completo"
            disabled={crearMut.isPending}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="cirujano-combobox">Cirujano</Label>
          <MedicoCombobox
            id="cirujano-combobox"
            value={medicoSeleccionado}
            onChange={setMedicoSeleccionado}
            items={medicosQ.data?.items ?? []}
            disabled={crearMut.isPending || sinMedicosActivos}
            isLoading={medicosQ.isLoading}
          />
          {medicosQ.isError ? (
            <p className="text-xs text-[var(--destructive)]">
              No se pudo cargar el catálogo de médicos. Intente de nuevo.
            </p>
          ) : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="fecha-cirugia">Fecha de cirugía</Label>
          <Input
            id="fecha-cirugia"
            type="date"
            value={fechaCirugia}
            onChange={(e) => setFechaCirugia(e.target.value)}
            disabled={crearMut.isPending}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="notas">Notas específicas (opcional)</Label>
          <textarea
            id="notas"
            rows={3}
            className="flex w-full rounded-md border border-[var(--border)] bg-transparent px-3 py-2 text-sm text-[var(--color-text)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--ring)]"
            value={notas}
            onChange={(e) => setNotas(e.target.value)}
            disabled={crearMut.isPending}
            maxLength={8000}
          />
        </div>

        <Button type="submit" disabled={!puedeEnviar} className="w-full">
          {crearMut.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              Registrando…
            </>
          ) : (
            'Registrar caso y generar código'
          )}
        </Button>
      </form>

      {modalCodigo ? (
        <CodigoEmparejamientoModal
          data={modalCodigo.data}
          pacienteNombre={modalCodigo.pacienteNombre}
          onClose={() => {
            setModalCodigo(null)
            onNavigate('/casos')
          }}
        />
      ) : null}
    </div>
  )
}
