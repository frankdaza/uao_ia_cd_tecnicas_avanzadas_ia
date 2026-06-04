/** Zona operativa TAAM (recordatorios y fechas en panel). */
export const TAAM_TIME_ZONE = 'America/Bogota'

export function formatFechaSolo(isoDate: string): string {
  try {
    return new Intl.DateTimeFormat('es-CO', {
      dateStyle: 'medium',
      timeZone: TAAM_TIME_ZONE,
    }).format(new Date(isoDate))
  } catch {
    return isoDate
  }
}

export function formatFechaAlta(iso: string): string {
  try {
    return new Intl.DateTimeFormat('es-CO', {
      dateStyle: 'medium',
      timeStyle: 'short',
      timeZone: TAAM_TIME_ZONE,
    }).format(new Date(iso))
  } catch {
    return iso
  }
}
