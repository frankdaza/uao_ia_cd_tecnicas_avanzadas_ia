import { ExternalLink, FileText } from 'lucide-react'
import type { FuenteBm25 } from '@/lib/schemas'
import { Badge } from '@/components/ui/badge'

interface SourcesPanelProps {
  fuentes: FuenteBm25[]
}

/** Panel de cards con las fuentes BM25 recuperadas. */
export function SourcesPanel({ fuentes }: SourcesPanelProps) {
  if (fuentes.length === 0) return null

  return (
    <div className="max-w-3xl mx-auto w-full px-4 mb-4">
      <p className="text-xs font-semibold text-[var(--color-text-muted)] mb-2 flex items-center gap-1.5">
        <FileText className="h-3.5 w-3.5" />
        Fuentes recuperadas por BM25 ({fuentes.length})
      </p>
      <div className="flex flex-col gap-2">
        {fuentes.map((f, i) => (
          <div
            key={`${f.archivo}-${i}`}
            className="flex items-start justify-between gap-3 rounded-lg border border-[var(--border)] bg-[var(--color-surface)] px-3 py-2 text-xs"
          >
            <div className="flex flex-col gap-0.5 min-w-0">
              <span className="font-medium truncate">{f.titulo || f.archivo}</span>
              <span className="text-[var(--color-text-subtle)] truncate">{f.archivo}</span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <Badge variant="secondary" className="text-xs tabular-nums">
                {f.score.toFixed(2)}
              </Badge>
              {f.source_url && (
                <a
                  href={f.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={`Abrir fuente: ${f.titulo || f.archivo}`}
                  className="text-[var(--color-accent)] hover:text-[var(--color-accent-dark)] transition-colors"
                >
                  <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
