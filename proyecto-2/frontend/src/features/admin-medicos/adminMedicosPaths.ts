export function esRutaAdminMedicos(path: string): boolean {
  return path === '/admin/medicos' || path.startsWith('/admin/medicos/')
}
