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

/** Entero 1–50 alineado a ``RAG_TOP_K`` / columna ``rag_top_k`` del admin. */
export function validarRagTopK(valor: string): string | null {
  const t = valor.trim()
  const n = Number.parseInt(t, 10)
  if (!Number.isFinite(n) || String(n) !== t) return 'Ingrese un entero válido entre 1 y 50.'
  if (n < 1 || n > 50) return 'rag_top_k debe estar entre 1 y 50.'
  return null
}

/** Umbral 0–1 alineado a ``RAG_SCORE_MINIMO``. */
export function validarRagScoreMinimo(valor: string): string | null {
  const n = Number.parseFloat(valor)
  if (!Number.isFinite(n)) return 'Ingrese un número válido.'
  if (n < 0 || n > 1) return 'rag_score_minimo debe estar entre 0 y 1.'
  return null
}

/** Entero 1–200 alineado a ``HISTORIAL_TURNOS_MAX`` / columna admin. */
export function validarHistorialTurnosMax(valor: string): string | null {
  const t = valor.trim()
  const n = Number.parseInt(t, 10)
  if (!Number.isFinite(n) || String(n) !== t) return 'Ingrese un entero válido entre 1 y 200.'
  if (n < 1 || n > 200) return 'historial_turnos_max debe estar entre 1 y 200.'
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
