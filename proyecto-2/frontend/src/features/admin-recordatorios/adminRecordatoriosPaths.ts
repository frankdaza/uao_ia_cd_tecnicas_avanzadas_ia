/** Rutas del panel admin de recordatorios programados. */
export function esRutaAdminRecordatorios(path: string): boolean {
  return path === '/admin/recordatorios' || path.startsWith('/admin/recordatorios/')
}
