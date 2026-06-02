import { useCallback, useState, type DragEvent } from 'react'
import { FileText, Upload } from 'lucide-react'
import { cn } from '@/lib/cn'
import { PROTOCOLO_MAX_BYTES, validarArchivoProtocolo } from '@/lib/procedimientosValidacion'

const ACCEPT_PROTOCOL =
  '.pdf,.md,application/pdf,text/markdown,text/x-markdown,text/plain,application/octet-stream'

interface ProtocolFileDropZoneProps {
  file: File | null
  onFileChange: (file: File | null) => void
  disabled?: boolean
}

/** Zona drag-and-drop para protocolo médico en PDF o Markdown (.md). */
export function ProtocolFileDropZone({
  file,
  onFileChange,
  disabled,
}: ProtocolFileDropZoneProps) {
  const [dragOver, setDragOver] = useState(false)
  const [errorLocal, setErrorLocal] = useState<string | null>(null)

  const aplicarArchivo = useCallback(
    (next: File | null) => {
      if (!next) {
        setErrorLocal(null)
        onFileChange(null)
        return
      }
      const resultado = validarArchivoProtocolo(next)
      if (!resultado.ok) {
        setErrorLocal(resultado.error)
        onFileChange(null)
        return
      }
      setErrorLocal(null)
      onFileChange(next)
    },
    [onFileChange],
  )

  const onDrop = (e: DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    if (disabled) return
    const dropped = e.dataTransfer.files[0]
    if (dropped) aplicarArchivo(dropped)
  }

  return (
    <div className="space-y-2">
      <div
        onDragOver={(e) => {
          e.preventDefault()
          if (!disabled) setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={cn(
          'flex flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 text-center transition-colors',
          dragOver && 'border-[var(--primary)] bg-[var(--accent)]',
          !dragOver && 'border-[var(--border)]',
          disabled && 'opacity-50 pointer-events-none',
        )}
      >
        {file ? (
          <>
            <FileText className="h-10 w-10 text-[var(--primary)]" aria-hidden />
            <p className="text-sm font-medium text-[var(--color-text)]">{file.name}</p>
            <p className="text-xs text-[var(--color-text-muted)]">
              {(file.size / 1024).toFixed(1)} KB — máximo {PROTOCOLO_MAX_BYTES / (1024 * 1024)} MB
            </p>
            <button
              type="button"
              className="text-xs text-[var(--primary)] underline-offset-2 hover:underline"
              onClick={() => aplicarArchivo(null)}
            >
              Quitar archivo
            </button>
          </>
        ) : (
          <>
            <Upload className="h-10 w-10 text-[var(--color-text-subtle)]" aria-hidden />
            <p className="text-sm text-[var(--color-text)]">
              Arrastre el protocolo aquí o{' '}
              <label className="cursor-pointer font-medium text-[var(--primary)] hover:underline">
                seleccione un archivo
                <input
                  type="file"
                  accept={ACCEPT_PROTOCOL}
                  className="sr-only"
                  disabled={disabled}
                  onChange={(e) => {
                    const f = e.target.files?.[0]
                    aplicarArchivo(f ?? null)
                    e.target.value = ''
                  }}
                />
              </label>
            </p>
            <p className="text-xs text-[var(--color-text-subtle)]">
              PDF o Markdown (.md), nombre ASCII, hasta {PROTOCOLO_MAX_BYTES / (1024 * 1024)} MB
            </p>
          </>
        )}
      </div>
      {errorLocal ? <p className="text-sm text-[var(--destructive)]">{errorLocal}</p> : null}
    </div>
  )
}
