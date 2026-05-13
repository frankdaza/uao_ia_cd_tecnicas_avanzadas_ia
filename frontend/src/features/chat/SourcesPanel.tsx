import { ExternalLink, FileText } from 'lucide-react'
import type { RagChunk } from '@/lib/schemas'
import { Badge } from '@/components/ui/badge'

interface SourcesPanelProps {
  chunks: RagChunk[]
}

function tituloChunk(c: RagChunk): string {
  const t = typeof c.titulo === 'string' ? c.titulo : ''
  const a = typeof c.archivo === 'string' ? c.archivo : ''
  return t || a || 'Fragmento'
}

function scoreChunk(c: RagChunk): number | null {
  const s = c.score
  return typeof s === 'number' && Number.isFinite(s) ? s : null
}

/** Panel de fragmentos RAG (Qdrant) con enlaces cuando hay `source_url`. */
export function SourcesPanel({ chunks }: SourcesPanelProps) {
  if (chunks.length === 0) return null

  return (
    <div className="max-w-3xl mx-auto w-full px-4 mb-4">
      <p className="text-xs font-semibold text-[var(--color-text-muted)] mb-2 flex items-center gap-1.5">
        <FileText className="h-3.5 w-3.5" />
        Fuentes RAG — Qdrant ({chunks.length})
      </p>
      <div className="flex flex-col gap-2">
        {chunks.map((c, i) => {
          const url = typeof c.source_url === 'string' ? c.source_url : ''
          const archivo = typeof c.archivo === 'string' ? c.archivo : ''
          const sc = scoreChunk(c)
          return (
            <div
              key={`${archivo}-${i}`}
              className="flex items-start justify-between gap-3 rounded-lg border border-[var(--border)] bg-[var(--color-surface)] px-3 py-2 text-xs"
            >
              <div className="flex flex-col gap-0.5 min-w-0">
                <span className="font-medium truncate">{tituloChunk(c)}</span>
                {archivo ? (
                  <span className="text-[var(--color-text-subtle)] truncate">{archivo}</span>
                ) : null}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {sc != null && (
                  <Badge variant="secondary" className="text-xs tabular-nums">
                    {sc.toFixed(2)}
                  </Badge>
                )}
                {url ? (
                  <a
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`Abrir fuente: ${tituloChunk(c)}`}
                    className="text-[var(--color-accent)] hover:text-[var(--color-accent-dark)] transition-colors"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                ) : null}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
