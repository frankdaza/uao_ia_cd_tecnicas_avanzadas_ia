/** Texto relativo para indicador de actualización del dashboard. */
export function formatUpdatedAgo(updatedAtMs: number, nowMs = Date.now()): string {
  const diffSec = Math.max(0, Math.floor((nowMs - updatedAtMs) / 1000))
  if (diffSec < 5) return 'hace unos segundos'
  if (diffSec < 60) return `hace ${diffSec} s`
  const min = Math.floor(diffSec / 60)
  if (min < 60) return `hace ${min} min`
  const h = Math.floor(min / 60)
  return `hace ${h} h`
}
