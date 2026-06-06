import { useEffect, useState } from 'react'
import { ImageOff, Loader2 } from 'lucide-react'
import type { AdjuntoMensaje } from '@/lib/schemas'
import { fetchStaffAdjuntoBlob } from '@/lib/api'
import { cn } from '@/lib/cn'

interface AdjuntoMensajeVistaProps {
  adjunto: AdjuntoMensaje
  className?: string
  compacto?: boolean
}

/** Renderiza imagen, video o audio de un adjunto staff (blob autenticado). */
export function AdjuntoMensajeVista({
  adjunto,
  className,
  compacto = false,
}: AdjuntoMensajeVistaProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [error, setError] = useState(false)
  const [cargando, setCargando] = useState(true)

  useEffect(() => {
    let activo = true
    let urlLocal: string | null = null
    setCargando(true)
    setError(false)

    void fetchStaffAdjuntoBlob(adjunto.id)
      .then((blob) => {
        if (!activo) return
        urlLocal = URL.createObjectURL(blob)
        setBlobUrl(urlLocal)
      })
      .catch(() => {
        if (activo) setError(true)
      })
      .finally(() => {
        if (activo) setCargando(false)
      })

    return () => {
      activo = false
      if (urlLocal) URL.revokeObjectURL(urlLocal)
    }
  }, [adjunto.id])

  if (cargando) {
    return (
      <div
        className={cn(
          'flex items-center justify-center rounded-md border border-[var(--border)] bg-[var(--color-surface)]',
          compacto ? 'h-16 w-16' : 'h-32 w-full max-w-xs',
          className,
        )}
      >
        <Loader2 className="h-5 w-5 animate-spin text-[var(--color-text-muted)]" aria-hidden />
      </div>
    )
  }

  if (error || !blobUrl) {
    return (
      <div
        className={cn(
          'flex items-center gap-2 rounded-md border border-dashed border-[var(--border)] p-2 text-xs text-[var(--color-text-muted)]',
          className,
        )}
      >
        <ImageOff className="h-4 w-4 shrink-0" aria-hidden />
        No se pudo cargar el adjunto
      </div>
    )
  }

  if (adjunto.tipo === 'imagen') {
    return (
      <figure className={cn('space-y-1', className)}>
        <img
          src={blobUrl}
          alt={adjunto.caption ?? 'Imagen del paciente'}
          className={cn(
            'rounded-md border border-[var(--border)] object-cover',
            compacto ? 'h-16 w-16' : 'max-h-64 w-full max-w-sm',
          )}
        />
        {adjunto.caption && !compacto ? (
          <figcaption className="text-xs italic text-[var(--color-text-muted)]">
            {adjunto.caption}
          </figcaption>
        ) : null}
      </figure>
    )
  }

  if (adjunto.tipo === 'video') {
    return (
      <div className={cn('space-y-1', className)}>
        <video
          src={blobUrl}
          controls
          preload="metadata"
          className="max-h-64 w-full max-w-sm rounded-md border border-[var(--border)]"
        >
          <track kind="captions" />
        </video>
        {adjunto.caption ? (
          <p className="text-xs italic text-[var(--color-text-muted)]">{adjunto.caption}</p>
        ) : null}
      </div>
    )
  }

  return (
    <div className={cn('space-y-1', className)}>
      <audio src={blobUrl} controls preload="metadata" className="w-full max-w-sm" />
      {adjunto.caption ? (
        <p className="text-xs italic text-[var(--color-text-muted)]">{adjunto.caption}</p>
      ) : null}
    </div>
  )
}

interface ListaAdjuntosProps {
  adjuntos: AdjuntoMensaje[]
  compacto?: boolean
  className?: string
}

/** Lista horizontal de adjuntos (alertas o mensajes). */
export function ListaAdjuntosMensaje({ adjuntos, compacto, className }: ListaAdjuntosProps) {
  if (adjuntos.length === 0) return null
  return (
    <div className={cn('flex flex-wrap gap-2', className)}>
      {adjuntos.map((adj) => (
        <AdjuntoMensajeVista key={adj.id} adjunto={adj} compacto={compacto} />
      ))}
    </div>
  )
}
