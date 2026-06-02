import type { MedicoOpcion } from '@/lib/schemas'

export function etiquetaMedico(m: MedicoOpcion): string {
  const esp = m.especialidad?.trim() || 'Sin especialidad'
  return `${m.nombre_completo} — ${esp}`
}

export function filtrarMedicos(items: MedicoOpcion[], busqueda: string): MedicoOpcion[] {
  const q = busqueda.trim().toLowerCase()
  if (!q) return items
  return items.filter(
    (m) =>
      m.nombre_completo.toLowerCase().includes(q) ||
      m.codigo_registro.toLowerCase().includes(q) ||
      (m.especialidad ?? '').toLowerCase().includes(q),
  )
}
