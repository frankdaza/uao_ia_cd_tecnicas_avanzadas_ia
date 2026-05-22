import { useCallback, useEffect, useState } from 'react'

/**
 * Ruta actual del SPA basada en ``window.location.pathname`` (sin react-router).
 */
export function useAppPath() {
  const [path, setPathState] = useState(() => window.location.pathname)

  const setPath = useCallback((next: string) => {
    const normalizado = next.startsWith('/') ? next : `/${next}`
    if (normalizado !== window.location.pathname) {
      window.history.pushState(null, '', normalizado)
    }
    setPathState(normalizado)
  }, [])

  useEffect(() => {
    const onPop = () => setPathState(window.location.pathname)
    window.addEventListener('popstate', onPop)
    return () => window.removeEventListener('popstate', onPop)
  }, [])

  return { path, setPath }
}
