/** Rutas del panel admin de webhook Telegram. */
export function esRutaAdminTelegram(path: string): boolean {
  return path === '/admin/telegram' || path.startsWith('/admin/telegram/')
}
