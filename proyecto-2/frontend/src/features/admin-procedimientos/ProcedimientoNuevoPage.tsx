import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError, createAdminProcedimiento } from '@/lib/api'
import { ProcedimientoMetadataSchema } from '@/lib/schemas'
import { ProtocolFileDropZone } from './ProtocolFileDropZone'

interface ProcedimientoNuevoPageProps {
  onNavigate: (path: string) => void
}

/** Alta de procedimiento con protocolo PDF o Markdown (multipart). */
export function ProcedimientoNuevoPage({ onNavigate }: ProcedimientoNuevoPageProps) {
  const qc = useQueryClient()
  const [codigo, setCodigo] = useState('')
  const [nombre, setNombre] = useState('')
  const [protocolo, setProtocolo] = useState<File | null>(null)

  const mut = useMutation({
    mutationFn: async () => {
      const meta = ProcedimientoMetadataSchema.parse({ codigo: codigo.trim(), nombre: nombre.trim() })
      if (!protocolo) {
        throw new Error('Seleccione un archivo de protocolo (PDF o Markdown).')
      }
      return createAdminProcedimiento(meta, protocolo)
    },
    onSuccess: async (creado) => {
      toast.success('Procedimiento creado. La indexación puede tardar unos segundos.')
      await qc.invalidateQueries({ queryKey: ['admin', 'procedimientos'] })
      onNavigate(`/admin/procedimientos/${creado.id}`)
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof ApiError
          ? (err.detail ?? err.message)
          : err instanceof Error
            ? err.message
            : 'No se pudo crear el procedimiento.'
      toast.error(msg)
    },
  })

  const metaPreview = ProcedimientoMetadataSchema.safeParse({
    codigo: codigo.trim(),
    nombre: nombre.trim(),
  })
  const puedeEnviar = metaPreview.success && protocolo != null && !mut.isPending

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <Button
        type="button"
        variant="ghost"
        size="sm"
        className="-ml-2"
        onClick={() => onNavigate('/admin/procedimientos')}
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        Volver al listado
      </Button>

      <div>
        <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">
          Nuevo procedimiento
        </h2>
        <p className="mt-1 text-sm text-[var(--color-text-muted)]">
          Registre el código, nombre y el protocolo general en PDF o Markdown.
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
          <Label htmlFor="codigo">Código</Label>
          <Input
            id="codigo"
            value={codigo}
            onChange={(e) => setCodigo(e.target.value)}
            placeholder="ej. colecistectomia-v1"
            autoComplete="off"
            disabled={mut.isPending}
          />
          <p className="text-xs text-[var(--color-text-subtle)]">
            ASCII: letras, números, guion y guion bajo. Debe ser único.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="nombre">Nombre</Label>
          <Input
            id="nombre"
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Nombre visible del procedimiento"
            disabled={mut.isPending}
          />
        </div>

        <div className="space-y-2">
          <Label>Protocolo (PDF o Markdown)</Label>
          <ProtocolFileDropZone
            file={protocolo}
            onFileChange={setProtocolo}
            disabled={mut.isPending}
          />
        </div>

        {!metaPreview.success && (codigo || nombre) ? (
          <p className="text-sm text-[var(--destructive)]">
            {metaPreview.error.issues[0]?.message ?? 'Revise código y nombre.'}
          </p>
        ) : null}

        <Button type="submit" disabled={!puedeEnviar} className="w-full sm:w-auto">
          {mut.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              Subiendo e indexando…
            </>
          ) : (
            'Registrar procedimiento'
          )}
        </Button>
      </form>
    </div>
  )
}
