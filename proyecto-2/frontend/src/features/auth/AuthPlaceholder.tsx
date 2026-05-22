import { Button } from '@/components/ui/button'
import { useAuth } from './AuthContext'

/** Pantalla provisional hasta TASK-110 (login staff). */
export function AuthPlaceholder() {
  const { setDevSession } = useAuth()

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-[var(--color-background)] px-4">
      <div className="max-w-md text-center space-y-3">
        <h1 className="font-display text-2xl font-semibold text-[var(--color-text)]">
          Acceso staff TAAM
        </h1>
        <p className="text-sm text-[var(--color-text-muted)]">
          El inicio de sesión con correo y contraseña se implementará en la tarea de autenticación.
          Mientras tanto puede abrir el shell de desarrollo para revisar layout y conexión con la API.
        </p>
      </div>
      <Button
        type="button"
        onClick={() =>
          setDevSession({
            email: 'dev@fvl.local',
            nombre: 'Usuario desarrollo',
            rol: 'staff',
          })
        }
      >
        Continuar (desarrollo)
      </Button>
    </div>
  )
}
