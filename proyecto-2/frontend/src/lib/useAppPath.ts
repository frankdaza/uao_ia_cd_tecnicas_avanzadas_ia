import { useCallback, useEffect, useState } from 'react'

/**
 * Ruta actual del SPA basada en ``window.location.pathname`` (sin react-router).
 */
export function useAppPath() {
  const [path, setPathState] = useState(() => window.location.pathname)

  const setPath = useCallback((next: string) => {
    const raw = next.startsWith('/') ? next : `/${next}`
    const url = new URL(raw, window.location.origin)
    const destino = `${url.pathname}${url.search}`
    if (destino !== `${window.location.pathname}${window.location.search}`) {
      window.history.pushState(null, '', destino)
    }
    setPathState(url.pathname)
  }, [])

  useEffect(() => {
    const onPop = () => setPathState(window.location.pathname)
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  return { path, setPath }
}
