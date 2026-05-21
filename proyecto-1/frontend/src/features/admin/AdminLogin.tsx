import { type FormEvent, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { verificarClaveAdministracion } from '@/lib/adminApi'
import { ApiError } from '@/lib/api'

type Props = {
  onSuccess: (clave: string) => void
}

/** Pantalla inicial del panel: captura la clave en memoria (no se persiste en localStorage). */
export function AdminLogin({ onSuccess }: Props) {
  const [clave, setClave] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [cargando, setCargando] = useState(false)

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const t = clave.trim()
    if (!t) {
      setError('Ingrese la clave de administración.')
      return
    }
    setCargando(true)
    try {
      await verificarClaveAdministracion(t)
      onSuccess(t)
      setClave('')
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401 || err.status === 403) {
          setError('No se pudo acceder. Verifique la clave o la configuración del servidor.')
        } else if (err.status === 503) {
          setError('El panel administrativo no está habilitado en el servidor (falta ADMIN_API_KEY).')
        } else {
          setError(err.detail ?? err.message)
        }
      } else {
        setError('No se pudo conectar con el servidor. Intente de nuevo.')
      }
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="min-h-svh flex flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-8 shadow-sm">
        <h1 className="font-display text-2xl font-semibold text-foreground">Panel administrativo</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Acceso restringido. La clave se envía solo en la cabecera HTTP y no se guarda en el navegador.
        </p>
        <form className="mt-6 space-y-4" onSubmit={enviar}>
          <div className="space-y-2">
            <Label htmlFor="admin-key">Clave de administración</Label>
            <Input
              id="admin-key"
              name="admin-key"
              type="password"
              autoComplete="off"
              value={clave}
              onChange={(ev) => setClave(ev.target.value)}
              aria-invalid={error ? true : undefined}
              aria-describedby={error ? 'admin-login-error' : undefined}
            />
            {error ? (
              <p id="admin-login-error" className="text-sm text-destructive" role="alert">
                {error}
              </p>
            ) : null}
          </div>
          <Button type="submit" className="w-full" disabled={cargando} aria-busy={cargando}>
            {cargando ? 'Verificando…' : 'Continuar'}
          </Button>
        </form>
      </div>
    </div>
  )
}
