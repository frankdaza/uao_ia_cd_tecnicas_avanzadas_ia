import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { AdminLogin } from '@/features/admin/AdminLogin'
import { AdminRutas } from '@/features/admin/AdminRutas'
import { EVENTO_ADMIN_NO_AUTORIZADO } from '@/lib/adminUnauthorized'

type Props = {
  pathActual: string
  onNavigate: (ruta: string) => void
}

/**
 * Raíz del panel ``/admin``: login en memoria y rutas internas.
 */
export function AdminEntrada({ pathActual, onNavigate }: Props) {
  const [adminKey, setAdminKey] = useState<string | null>(null)
  const adminKeyRef = useRef<string | null>(null)
  const queryClient = useQueryClient()

  useEffect(() => {
    adminKeyRef.current = adminKey
  }, [adminKey])

  useEffect(() => {
    const fn = () => {
      if (adminKeyRef.current != null) {
        toast.error('La clave de administración ya no es válida o no fue aceptada. Ingrese de nuevo.')
      }
      queryClient.removeQueries({ queryKey: ['admin'] })
      setAdminKey(null)
    }
    window.addEventListener(EVENTO_ADMIN_NO_AUTORIZADO, fn)
    return () => window.removeEventListener(EVENTO_ADMIN_NO_AUTORIZADO, fn)
  }, [queryClient])

  if (!adminKey) {
    return <AdminLogin onSuccess={setAdminKey} />
  }

  return (
    <AdminRutas
      adminKey={adminKey}
      pathActual={pathActual}
      onNavigate={onNavigate}
      onSalirAdmin={() => {
        setAdminKey(null)
        onNavigate('/')
      }}
    />
  )
}
