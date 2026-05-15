/**
 * Deteccion de la respuesta canonica "sin contexto" (alineado a
 * `PROMPT_SISTEMA_DEFECTO` y `respuesta_sin_contexto` del meta-prompt del router).
 */

/** Frase literal que el compositor debe usar cuando no hay contexto suficiente. */
export const RESPUESTA_SIN_CONTEXTO_FRASE = 'No tengo información suficiente' as const

/** True si el texto final del agente indica falta de informacion (ignora mayusculas y tildes). */
export function respuestaFinalEsSinInformacion(texto: string): boolean {
  const t = (texto || '').trim()
  if (!t) return false
  const fold = (s: string) =>
    s
      .normalize('NFD')
      .replace(/\p{M}/gu, '')
      .toLowerCase()
  return fold(t).includes(fold(RESPUESTA_SIN_CONTEXTO_FRASE))
}
