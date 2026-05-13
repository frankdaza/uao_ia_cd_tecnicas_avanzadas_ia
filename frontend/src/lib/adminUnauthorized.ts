/** Evento global cuando una petición admin recibe 401 (clave inválida o ausente). */

export const EVENTO_ADMIN_NO_AUTORIZADO = 'fvl:admin-no-autorizado'

export function emitirAdminNoAutorizado(): void {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(EVENTO_ADMIN_NO_AUTORIZADO))
}
