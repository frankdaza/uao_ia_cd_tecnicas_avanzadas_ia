import { useCallback, useState, type DragEvent } from 'react'
import { FileText, Upload } from 'lucide-react'
import { cn } from '@/lib/cn'
import { PDF_MAX_BYTES, validarArchivoPdf } from '@/lib/procedimientosValidacion'

interface PdfDropZoneProps {
  file: File | null
  onFileChange: (file: File | null) => void
  disabled?: boolean
}

/** Zona drag-and-drop para seleccionar un PDF de protocolo. */
export function PdfDropZone({ file, onFileChange, disabled }: PdfDropZoneProps) {
  const [dragOver, setDragOver] = useState(false)
  const [errorLocal, setErrorLocal] = useState<string | null>(null)

  const aplicarArchivo = useCallback(
    (next: File | null) => {
      if (!next) {
        setErrorLocal(null)
        onFileChange(null)
        return
      }
      const err = validarArchivoPdf(next)
      if (err) {
        setErrorLocal(err)
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
              {(file.size / 1024).toFixed(1)} KB — máximo {PDF_MAX_BYTES / (1024 * 1024)} MB
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
              Arrastre el PDF aquí o{' '}
              <label className="cursor-pointer font-medium text-[var(--primary)] hover:underline">
                seleccione un archivo
                <input
                  type="file"
                  accept="application/pdf"
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
              PDF, nombre ASCII, hasta {PDF_MAX_BYTES / (1024 * 1024)} MB
            </p>
          </>
        )}
      </div>
      {errorLocal ? <p className="text-sm text-[var(--destructive)]">{errorLocal}</p> : null}
    </div>
  )
}
