import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError, crearMedico } from '@/lib/api'
import { MedicoCuerpoSchema } from './medicosValidacion'

interface MedicoNuevoPageProps {
  onNavigate: (path: string) => void
}

/** Alta de médico en el catálogo (JSON). */
export function MedicoNuevoPage({ onNavigate }: MedicoNuevoPageProps) {
  const qc = useQueryClient()
  const [codigoRegistro, setCodigoRegistro] = useState('')
  const [nombreCompleto, setNombreCompleto] = useState('')
  const [especialidad, setEspecialidad] = useState('')

  const mut = useMutation({
    mutationFn: async () => {
      const cuerpo = MedicoCuerpoSchema.parse({
        codigo_registro: codigoRegistro.trim(),
        nombre_completo: nombreCompleto.trim(),
        especialidad: especialidad.trim() || undefined,
      })
      return crearMedico(cuerpo)
    },
    onSuccess: async (creado) => {
      toast.success('Médico registrado correctamente.')
      await qc.invalidateQueries({ queryKey: ['admin', 'medicos'] })
      onNavigate(`/admin/medicos/${creado.id}`)
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof ApiError
          ? (err.detail ?? err.message)
          : err instanceof Error
            ? err.message
            : 'No se pudo registrar el médico.'
      toast.error(msg)
    },
  })

  const preview = MedicoCuerpoSchema.safeParse({
    codigo_registro: codigoRegistro.trim(),
    nombre_completo: nombreCompleto.trim(),
    especialidad: especialidad.trim() || undefined,
  })
  const puedeEnviar = preview.success && !mut.isPending

  return (
    <div className="mx-auto max-w-lg space-y-6">
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

      <div>
        <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">
          Nuevo médico
        </h2>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Registre el código de registro, nombre completo y especialidad opcional.
        </p>
      </div>

      <form
        className="space-y-4"
        onSubmit={(e) => {
          e.preventDefault()
          if (puedeEnviar) mut.mutate()
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="codigo-registro">Código de registro</Label>
          <Input
            id="codigo-registro"
            value={codigoRegistro}
            onChange={(e) => setCodigoRegistro(e.target.value)}
            placeholder="ej. dr.garcia"
            autoComplete="off"
            disabled={mut.isPending}
          />
          <p className="text-xs text-[var(--color-text-subtle)]">
            ASCII: letras, números, punto, guion y guion bajo. Debe ser único.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="nombre-completo">Nombre completo</Label>
          <Input
            id="nombre-completo"
            value={nombreCompleto}
            onChange={(e) => setNombreCompleto(e.target.value)}
            placeholder="Nombre visible del médico"
            disabled={mut.isPending}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="especialidad">Especialidad (opcional)</Label>
          <Input
            id="especialidad"
            value={especialidad}
            onChange={(e) => setEspecialidad(e.target.value)}
            placeholder="ej. Cirugía general"
            disabled={mut.isPending}
          />
        </div>

        {!preview.success && (codigoRegistro || nombreCompleto || especialidad) ? (
          <p className="text-sm text-[var(--destructive)]">
            {preview.error.issues[0]?.message ?? 'Revise los campos del formulario.'}
          </p>
        ) : null}

        <Button type="submit" disabled={!puedeEnviar} className="w-full sm:w-auto">
          {mut.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              Guardando…
            </>
          ) : (
            'Registrar médico'
          )}
        </Button>
      </form>
    </div>
  )
}
