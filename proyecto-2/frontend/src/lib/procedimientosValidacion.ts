/** Alineado con ``TAAM_PDF_MAX_MB`` por defecto en backend (10). */
export const PDF_MAX_BYTES = 10 * 1024 * 1024

const NOMBRE_ARCHIVO_ASCII = /^[A-Za-z0-9._-]+$/

export function validarArchivoPdf(file: File): string | null {
  if (file.type !== 'application/pdf') {
    return 'El archivo debe ser PDF (application/pdf).'
  }
  if (file.size > PDF_MAX_BYTES) {
    return `El PDF no puede superar ${PDF_MAX_BYTES / (1024 * 1024)} MB.`
  }
  if (!NOMBRE_ARCHIVO_ASCII.test(file.name)) {
    return 'El nombre del archivo solo puede usar letras, números, punto, guion y guion bajo (ASCII).'
  }
  return null
}
