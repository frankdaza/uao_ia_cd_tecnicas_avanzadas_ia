/** Alineado con límite por defecto del backend (10 MB). */
export const PROTOCOLO_MAX_BYTES = 10 * 1024 * 1024

/** @deprecated Use PROTOCOLO_MAX_BYTES */
export const PDF_MAX_BYTES = PROTOCOLO_MAX_BYTES

const NOMBRE_ARCHIVO_ASCII = /^[A-Za-z0-9._-]+$/

const MD_MIMES = new Set([
  'text/markdown',
  'text/x-markdown',
  'text/plain',
  'application/octet-stream',
  '',
])

export type FormatoProtocolo = 'pdf' | 'markdown'

export function validarArchivoProtocolo(
  file: File,
): { ok: true; formato: FormatoProtocolo } | { ok: false; error: string } {
  const nombre = file.name
  const lower = nombre.toLowerCase()
  if (!NOMBRE_ARCHIVO_ASCII.test(nombre)) {
    return {
      ok: false,
      error: 'El nombre solo puede usar letras, números, punto, guion y guion bajo.',
    }
  }
  if (file.size > PROTOCOLO_MAX_BYTES) {
    return {
      ok: false,
      error: `Máximo ${PROTOCOLO_MAX_BYTES / (1024 * 1024)} MB.`,
    }
  }
  if (lower.endsWith('.pdf')) {
    if (file.type && file.type !== 'application/pdf') {
      return { ok: false, error: 'El archivo PDF debe ser application/pdf.' }
    }
    return { ok: true, formato: 'pdf' }
  }
  if (lower.endsWith('.md')) {
    if (file.type && !MD_MIMES.has(file.type)) {
      return { ok: false, error: 'Tipo MIME no reconocido para Markdown (.md).' }
    }
    return { ok: true, formato: 'markdown' }
  }
  return { ok: false, error: 'Use un archivo .pdf o .md.' }
}

/** @deprecated Use validarArchivoProtocolo */
export function validarArchivoPdf(file: File): string | null {
  const r = validarArchivoProtocolo(file)
  if (!r.ok) return r.error
  if (r.formato !== 'pdf') return 'Use un archivo PDF (.pdf).'
  return null
}
