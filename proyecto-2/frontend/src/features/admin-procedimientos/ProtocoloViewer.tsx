import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ExternalLink, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { ApiError, fetchAdminProcedimientoProtocolo } from '@/lib/api'
import type { Procedimiento } from '@/lib/schemas'

interface ProtocoloViewerProps {
  id: string
  formato: Procedimiento['formato_protocolo']
}

/** Vista previa del protocolo cargado (PDF embebido o Markdown renderizado). */
export function ProtocoloViewer({ id, formato }: ProtocoloViewerProps) {
  const q = useQuery({
    queryKey: ['admin', 'procedimientos', id, 'protocolo'],
    queryFn: () => fetchAdminProcedimientoProtocolo(id),
    staleTime: 60_000,
  })

  const [markdownTexto, setMarkdownTexto] = useState<string | null>(null)
  const [pdfObjectUrl, setPdfObjectUrl] = useState<string | null>(null)

  useEffect(() => {
    if (!q.data) {
      setMarkdownTexto(null)
      setPdfObjectUrl(null)
      return
    }

    let cancelado = false
    const blob = q.data

    if (formato === 'pdf') {
      const url = URL.createObjectURL(blob)
      setPdfObjectUrl(url)
      setMarkdownTexto(null)
      return () => {
        URL.revokeObjectURL(url)
      }
    }

    void blob.text().then((texto) => {
      if (!cancelado) {
        setMarkdownTexto(texto)
        setPdfObjectUrl(null)
      }
    })

    return () => {
      cancelado = true
    }
  }, [q.data, formato])

  if (q.isLoading) {
    return (
      <p className="flex items-center gap-2 text-sm text-[var(--color-text-muted)]">
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
        Cargando protocolo…
      </p>
    )
  }

  if (q.isError) {
    const mensaje =
      q.error instanceof ApiError
        ? (q.error.detail ?? q.error.message)
        : 'No se pudo cargar el protocolo.'
    return <p className="text-sm text-[var(--destructive)]">{mensaje}</p>
  }

  if (formato === 'pdf' && pdfObjectUrl) {
    return (
      <div className="space-y-2">
        <div className="flex justify-end">
          <Button type="button" variant="outline" size="sm" asChild>
            <a href={pdfObjectUrl} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="h-4 w-4" aria-hidden />
              Abrir en nueva pestaña
            </a>
          </Button>
        </div>
        <iframe
          title="Protocolo PDF"
          src={pdfObjectUrl}
          className="h-[70vh] w-full rounded-md border border-[var(--border)] bg-[var(--color-surface)]"
        />
      </div>
    )
  }

  if (formato === 'markdown' && markdownTexto !== null) {
    return (
      <article className="protocolo-markdown max-h-[70vh] overflow-y-auto rounded-md border border-[var(--border)] bg-[var(--color-surface)] p-4 text-sm">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdownTexto}</ReactMarkdown>
      </article>
    )
  }

  return (
    <p className="text-sm text-[var(--color-text-muted)]">
      No hay contenido de protocolo para mostrar.
    </p>
  )
}
