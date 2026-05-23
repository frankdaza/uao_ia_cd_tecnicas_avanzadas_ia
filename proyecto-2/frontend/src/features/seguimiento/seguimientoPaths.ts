export const SEGUIMIENTO_PATH = '/seguimiento'
export const SEGUIMIENTO_CASOS_PATH = '/seguimiento/casos'

const CASO_DETALLE_RE = /^\/seguimiento\/caso\/([0-9a-f-]{36})$/i

export function casoSeguimientoPath(casoId: string, alertaId?: string): string {
  const base = `/seguimiento/caso/${casoId}`
  return alertaId ? `${base}?alerta=${alertaId}` : base
}

export function parseCasoIdFromPath(path: string): string | null {
  const m = path.match(CASO_DETALLE_RE)
  return m?.[1] ?? null
}

export function esRutaSeguimiento(path: string): boolean {
  return path === SEGUIMIENTO_PATH || path.startsWith(`${SEGUIMIENTO_PATH}/`)
}
