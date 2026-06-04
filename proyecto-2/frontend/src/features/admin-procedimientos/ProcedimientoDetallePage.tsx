import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Loader2, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  ApiError,
  getAdminProcedimiento,
  patchAdminProcedimiento,
  reindexAdminProcedimiento,
} from '@/lib/api'
import type { Procedimiento } from '@/lib/schemas'
import { ProcedimientoMetadataSchema } from '@/lib/schemas'
import { formatFechaAlta } from '@/lib/formatFecha'
import { FormatoProtocoloBadge, IndexacionEstadoBadge } from './indexacionEstado'
import { ProtocolFileDropZone } from './ProtocolFileDropZone'
import { ProtocoloViewer } from './ProtocoloViewer'

interface ProcedimientoDetallePageProps {
  id: string
  onNavigate: (path: string) => void
}

/** Detalle, edición de metadatos, reemplazo de protocolo y reindexación. */
export function ProcedimientoDetallePage({ id, onNavigate }: ProcedimientoDetallePageProps) {
  const qc = useQueryClient()
  const q = useQuery({
    queryKey: ['admin', 'procedimientos', id],
    queryFn: () => getAdminProcedimiento(id),
    refetchInterval: (query) =>
      query.state.data?.indexacion_estado === 'pendiente' ? 3000 : false,
  })

  const [protocoloReemplazo, setProtocoloReemplazo] = useState<File | null>(null)

  const mutProtocolo = useMutation({
    mutationFn: async () => {
      if (!protocoloReemplazo) {
        throw new Error('Seleccione un archivo de protocolo (PDF o Markdown).')
      }
      return patchAdminProcedimiento(id, { archivo: protocoloReemplazo })
    },
    onSuccess: async () => {
      toast.success('Protocolo reemplazado. Indexación en curso.')
      setProtocoloReemplazo(null)
      await qc.invalidateQueries({ queryKey: ['admin', 'procedimientos'] })
      await qc.invalidateQueries({ queryKey: ['admin', 'procedimientos', id] })
      await qc.invalidateQueries({ queryKey: ['admin', 'procedimientos', id, 'protocolo'] })
    },
    onError: (err: unknown) => {
      toast.error(
        err instanceof ApiError
          ? (err.detail ?? err.message)
          : 'Error al subir el protocolo.',
      )
    },
  })

  const mutReindex = useMutation({
    mutationFn: () => reindexAdminProcedimiento(id),
    onSuccess: async () => {
      toast.success('Reindexación solicitada.')
      await qc.invalidateQueries({ queryKey: ['admin', 'procedimientos'] })
      await qc.invalidateQueries({ queryKey: ['admin', 'procedimientos', id] })
    },
    onError: (err: unknown) => {
      toast.error(err instanceof ApiError ? (err.detail ?? err.message) : 'No se pudo reindexar.')
    },
  })

  if (q.isLoading) {
    return <p className="text-sm text-[var(--color-text-muted)]">Cargando procedimiento…</p>
  }

  if (q.isError || !q.data) {
    return (
      <div className="space-y-4">
        <p className="text-sm text-[var(--destructive)]">Procedimiento no encontrado.</p>
        <Button type="button" variant="outline" onClick={() => onNavigate('/admin/procedimientos')}>
          Volver al listado
        </Button>
      </div>
    )
  }

  const fila = q.data

  return (
    <div className="mx-auto max-w-4xl space-y-8">
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

      <header className="space-y-3">
        <h2 className="font-display text-xl font-semibold text-[var(--color-text)]">{fila.nombre}</h2>
        <p className="font-mono text-sm text-[var(--color-text-muted)]">{fila.codigo}</p>
        <div className="flex flex-wrap items-center gap-3">
          <FormatoProtocoloBadge formato={fila.formato_protocolo} />
          <IndexacionEstadoBadge estado={fila.indexacion_estado} />
          {fila.indexacion_estado === 'pendiente' ? (
            <span className="flex items-center gap-1 text-xs text-[var(--color-text-muted)]">
              <Loader2 className="h-3 w-3 animate-spin" aria-hidden />
              Indexando en segundo plano…
            </span>
          ) : null}
          <span className="text-xs text-[var(--color-text-subtle)]">
            Versión vector: {fila.qdrant_collection_version ?? '—'} · Alta:{' '}
            {formatFechaAlta(fila.created_at)}
          </span>
        </div>
      </header>

      <section className="space-y-3 rounded-lg border border-[var(--border)] p-4">
        <h3 className="text-sm font-semibold text-[var(--color-text)]">
          Vista previa del protocolo
        </h3>
        <ProtocoloViewer id={id} formato={fila.formato_protocolo} />
      </section>

      <DetalleMetadataForm
        key={`${fila.id}-${fila.codigo}-${fila.nombre}`}
        fila={fila}
        id={id}
      />

      <section className="space-y-4 rounded-lg border border-[var(--border)] p-4">
        <h3 className="text-sm font-semibold text-[var(--color-text)]">
          Reemplazar protocolo (PDF o Markdown)
        </h3>
        <p className="text-xs text-[var(--color-text-muted)]">
          Al subir un nuevo protocolo se reinicia la indexación y se incrementa la versión vector.
          Puede cambiar entre PDF y Markdown.
        </p>
        <ProtocolFileDropZone
          file={protocoloReemplazo}
          onFileChange={setProtocoloReemplazo}
          disabled={mutProtocolo.isPending}
        />
        <Button
          type="button"
          disabled={!protocoloReemplazo || mutProtocolo.isPending}
          onClick={() => mutProtocolo.mutate()}
        >
          {mutProtocolo.isPending ? 'Subiendo…' : 'Reemplazar protocolo'}
        </Button>
      </section>

      <section className="rounded-lg border border-[var(--border)] p-4">
        <h3 className="text-sm font-semibold text-[var(--color-text)]">Reindexar</h3>
        <p className="mt-1 text-xs text-[var(--color-text-muted)]">
          Vuelve a ejecutar la ingesta Qdrant si hubo un error o tras cambios manuales en el servidor.
        </p>
        <Button
          type="button"
          variant="outline"
          className="mt-3"
          disabled={mutReindex.isPending || fila.indexacion_estado === 'pendiente'}
          onClick={() => mutReindex.mutate()}
        >
          <RefreshCw className="h-4 w-4" aria-hidden />
          {mutReindex.isPending ? 'Solicitando…' : 'Reindexar protocolo'}
        </Button>
      </section>
    </div>
  )
}

function DetalleMetadataForm({ fila, id }: { fila: Procedimiento; id: string }) {
  const qc = useQueryClient()
  const [codigo, setCodigo] = useState(fila.codigo)
  const [nombre, setNombre] = useState(fila.nombre)

  const mut = useMutation({
    mutationFn: async () => {
      const parcial: { codigo?: string; nombre?: string } = {}
      if (codigo.trim() !== fila.codigo) parcial.codigo = codigo.trim()
      if (nombre.trim() !== fila.nombre) parcial.nombre = nombre.trim()
      if (Object.keys(parcial).length === 0) {
        throw new Error('No hay cambios en código o nombre.')
      }
      ProcedimientoMetadataSchema.partial().parse(parcial)
      return patchAdminProcedimiento(id, { metadata: parcial })
    },
    onSuccess: async () => {
      toast.success('Metadatos actualizados.')
      await qc.invalidateQueries({ queryKey: ['admin', 'procedimientos'] })
      await qc.invalidateQueries({ queryKey: ['admin', 'procedimientos', id] })
    },
    onError: (err: unknown) => {
      toast.error(err instanceof ApiError ? (err.detail ?? err.message) : 'Error al guardar.')
    },
  })

  const metadataCambiada = codigo.trim() !== fila.codigo || nombre.trim() !== fila.nombre

  return (
    <section className="space-y-4 rounded-lg border border-[var(--border)] p-4">
      <h3 className="text-sm font-semibold text-[var(--color-text)]">Metadatos</h3>
      <div className="space-y-2">
        <Label htmlFor="det-codigo">Código</Label>
        <Input
          id="det-codigo"
          value={codigo}
          onChange={(e) => setCodigo(e.target.value)}
          disabled={mut.isPending}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="det-nombre">Nombre</Label>
        <Input
          id="det-nombre"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          disabled={mut.isPending}
        />
      </div>
      <Button
        type="button"
        variant="secondary"
        disabled={!metadataCambiada || mut.isPending}
        onClick={() => mut.mutate()}
      >
        {mut.isPending ? 'Guardando…' : 'Guardar metadatos'}
      </Button>
    </section>
  )
}
