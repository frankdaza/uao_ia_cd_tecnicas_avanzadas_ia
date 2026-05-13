/**
 * Validaciones de formulario alineadas al contrato de ``/api/admin/config`` (PATCH).
 */

const LONGITUD_MINIMA_PROMPT_INSTITUCIONAL = 80

export function validarIdentificadorModelo(valor: string): string | null {
  const t = valor.trim()
  if (!t) return 'El identificador del modelo no puede estar vacío.'
  return null
}

export function validarTemperatura(valor: string): string | null {
  const n = Number.parseFloat(valor)
  if (!Number.isFinite(n)) return 'Ingrese un número válido.'
  if (n < 0 || n > 2) return 'La temperatura debe estar entre 0 y 2.'
  return null
}

/** Si ``opcional`` y el campo está vacío, es válido (servidor usa default). */
export function validarTopP(valor: string, opcional: boolean): string | null {
  const t = valor.trim()
  if (t === '') return opcional ? null : 'Ingrese un valor entre 0 y 1 o deje vacío para el default del API.'
  const n = Number.parseFloat(t)
  if (!Number.isFinite(n)) return 'Ingrese un número válido.'
  if (n < 0 || n > 1) return 'top_p debe estar entre 0 y 1.'
  return null
}

export function validarLongitudPromptInstitucional(texto: string): string | null {
  const t = texto.trim()
  if (t.length < LONGITUD_MINIMA_PROMPT_INSTITUCIONAL) {
    return `El prompt institucional debe tener al menos ${LONGITUD_MINIMA_PROMPT_INSTITUCIONAL} caracteres (actual: ${t.length}).`
  }
  return null
}

export { LONGITUD_MINIMA_PROMPT_INSTITUCIONAL }
