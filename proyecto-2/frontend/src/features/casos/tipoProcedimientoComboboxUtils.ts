import type { TipoProcedimientoOpcion } from '@/lib/schemas'

export function etiquetaTipoProcedimiento(t: TipoProcedimientoOpcion): string {
  return `${t.codigo} — ${t.nombre}`
}

export function filtrarTiposProcedimiento(
  items: TipoProcedimientoOpcion[],
  busqueda: string,
): TipoProcedimientoOpcion[] {
  const q = busqueda.trim().toLowerCase()
  if (!q) return items
  return items.filter(
    (t) => t.codigo.toLowerCase().includes(q) || t.nombre.toLowerCase().includes(q),
  )
}
