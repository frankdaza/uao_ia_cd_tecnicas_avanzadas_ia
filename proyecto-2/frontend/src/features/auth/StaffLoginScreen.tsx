import { type FormEvent, useState } from 'react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuth } from './AuthContext'
import { ApiError } from '@/lib/api'
import { StaffLoginBodySchema } from '@/lib/schemas'

type Props = {
  onSuccess: () => void
}

/** Pantalla de acceso staff: email y contraseña contra POST /api/auth/staff/login. */
export function StaffLoginScreen({ onSuccess }: Props) {
  const { signIn } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitError(null)
    const parsed = StaffLoginBodySchema.safeParse({ email: email.trim(), password })
    if (!parsed.success) {
      const f = parsed.error.flatten().fieldErrors
      setFieldErrors({
        email: f.email?.[0],
        password: f.password?.[0],
      })
      return
    }
    setFieldErrors({})
    setLoading(true)
    try {
      await signIn(parsed.data)
      toast.success('Sesión iniciada correctamente.')
      onSuccess()
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          const msg = 'Credenciales inválidas. Verifique correo y contraseña.'
          setSubmitError(msg)
          toast.error(msg)
        } else if (err.status === 503) {
          const msg =
            err.detail ??
            'El inicio de sesión no está habilitado en el servidor (falta STAFF_JWT_SECRET).'
          setSubmitError(msg)
          toast.error(msg)
        } else {
          const msg = err.detail ?? err.message
          setSubmitError(msg)
          toast.error(msg)
        }
      } else {
        const msg = 'No se pudo contactar el servidor. Intente de nuevo.'
        setSubmitError(msg)
        toast.error(msg)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[var(--color-background)] px-4 py-10">
      <div className="w-full max-w-md rounded-xl border border-[var(--border)] bg-[var(--color-surface)] p-8 shadow-sm">
        <h1 className="font-display text-2xl font-semibold text-[var(--color-text)]">Acceso staff TAAM</h1>
        <p className="mt-2 text-sm text-[var(--color-text-muted)]">
          Ingrese su correo institucional y contraseña. La contraseña no se guarda en el navegador.
        </p>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit} noValidate>
          <div className="space-y-2">
            <Label htmlFor="staff-email">Correo electrónico</Label>
            <Input
              id="staff-email"
              name="email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(ev) => setEmail(ev.target.value)}
              aria-invalid={fieldErrors.email ? true : undefined}
              aria-describedby={fieldErrors.email ? 'staff-email-error' : undefined}
            />
            {fieldErrors.email ? (
              <p id="staff-email-error" className="text-sm text-[var(--destructive)]" role="alert">
                {fieldErrors.email}
              </p>
            ) : null}
          </div>
          <div className="space-y-2">
            <Label htmlFor="staff-password">Contraseña</Label>
            <Input
              id="staff-password"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(ev) => setPassword(ev.target.value)}
              aria-invalid={fieldErrors.password ? true : undefined}
              aria-describedby={fieldErrors.password ? 'staff-password-error' : undefined}
            />
            {fieldErrors.password ? (
              <p id="staff-password-error" className="text-sm text-[var(--destructive)]" role="alert">
                {fieldErrors.password}
              </p>
            ) : null}
          </div>
          {submitError ? (
            <p className="text-sm text-[var(--destructive)]" role="alert">
              {submitError}
            </p>
          ) : null}
          <Button type="submit" className="w-full" disabled={loading} aria-busy={loading}>
            {loading ? 'Iniciando sesión…' : 'Iniciar sesión'}
          </Button>
        </form>
      </div>
    </div>
  )
}
