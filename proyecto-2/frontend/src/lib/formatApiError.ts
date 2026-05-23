/** Convierte ``detail`` de FastAPI (string o lista de errores 422) a texto legible. */
export function formatApiDetail(detail: unknown): string | undefined {
  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }
  if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
    const obj = detail as Record<string, unknown>
    if (typeof obj.mensaje === 'string' && obj.mensaje.trim()) {
      return obj.mensaje
    }
    if (typeof obj.mensaje_telegram === 'string' && obj.mensaje_telegram.trim()) {
      return obj.mensaje_telegram
    }
  }
  if (Array.isArray(detail)) {
    const partes = detail
      .map((item) => {
        if (item && typeof item === 'object' && 'msg' in item) {
          const loc = 'loc' in item && Array.isArray(item.loc) ? item.loc.join('.') : ''
          const msg = String((item as { msg: unknown }).msg)
          return loc ? `${loc}: ${msg}` : msg
        }
        return null
      })
      .filter((s): s is string => Boolean(s))
    if (partes.length > 0) {
      return partes.join('; ')
    }
  }
  return undefined
}
