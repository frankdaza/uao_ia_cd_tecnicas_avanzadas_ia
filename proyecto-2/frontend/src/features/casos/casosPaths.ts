/** Rutas SPA del módulo casos (UC-MVP-02). */
export const CASOS_LIST_PATH = '/casos'
export const CASOS_NUEVO_PATH = '/casos/nuevo'

export function esRutaCasos(path: string): boolean {
  return path === CASOS_LIST_PATH || path.startsWith(`${CASOS_LIST_PATH}/`)
}
