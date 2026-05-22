export function esRutaAdminProcedimientos(path: string): boolean {
  return path === '/admin/procedimientos' || path.startsWith('/admin/procedimientos/')
}
