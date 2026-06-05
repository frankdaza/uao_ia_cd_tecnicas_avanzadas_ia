/** Rutas del panel admin de escalamiento HITL del agente. */
export const ADMIN_AGENTE_HITL_PATH = '/admin/agente-hitl'

export function esRutaAdminAgenteHitl(path: string): boolean {
  return path === ADMIN_AGENTE_HITL_PATH || path.startsWith(`${ADMIN_AGENTE_HITL_PATH}/`)
}
