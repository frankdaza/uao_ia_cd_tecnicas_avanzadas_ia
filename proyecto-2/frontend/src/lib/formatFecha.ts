export function formatFechaSolo(isoDate: string): string {
  try {
    return new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium' }).format(new Date(isoDate))
  } catch {
    return isoDate
  }
}

export function formatFechaAlta(iso: string): string {
  try {
    return new Intl.DateTimeFormat('es-CO', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(new Date(iso))
  } catch {
    return iso
  }
}
