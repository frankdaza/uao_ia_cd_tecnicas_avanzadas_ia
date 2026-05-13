import { useId, useState, type FormEvent } from 'react'
import { z } from 'zod'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError } from '@/lib/api'
import type { SesionPeticion } from '@/lib/schemas'
import { useAuth } from './AuthContext'

const AuthIdentificacionFormSchema = z.object({
  documento_identidad: z
    .string()
    .trim()
    .min(5, 'Ingresa al menos 5 caracteres.')
    .max(128, 'Máximo 128 caracteres.')
    .regex(/^[0-9A-Za-z-]+$/, 'Solo se permiten letras sin tilde, números y guiones.'),
  nombre: z
    .string()
    .trim()
    .min(2, 'Ingresa al menos 2 caracteres.')
    .max(512, 'Máximo 512 caracteres.'),
})

/** Pantalla inicial M2: documento de identidad y nombre antes del chat. */
export function AuthScreen() {
  const { iniciarSesion } = useAuth()
  const baseId = useId()
  const idDoc = `${baseId}-documento`
  const idNombre = `${baseId}-nombre`
  const errDocId = `${baseId}-err-documento`
  const errNombreId = `${baseId}-err-nombre`

  const [documento, setDocumento] = useState('')
  const [nombre, setNombre] = useState('')
  const [errores, setErrores] = useState<{ documento?: string; nombre?: string }>({})
  const [cargando, setCargando] = useState(false)

  const enviar = async (e: FormEvent) => {
    e.preventDefault()
    const parsed = AuthIdentificacionFormSchema.safeParse({
      documento_identidad: documento,
      nombre,
    })
    if (!parsed.success) {
      const f = parsed.error.flatten().fieldErrors
      setErrores({
        documento: f.documento_identidad?.[0],
        nombre: f.nombre?.[0],
      })
      return
    }
    setErrores({})
    setCargando(true)
    const cuerpo: SesionPeticion = {
      documento_identidad: parsed.data.documento_identidad,
      nombre: parsed.data.nombre,
    }
    try {
      await iniciarSesion(cuerpo)
      toast.success('Identificación correcta. Bienvenido.')
    } catch (err) {
      if (err instanceof ApiError) {
        toast.error(err.detail ?? err.message)
      } else {
        toast.error('No se pudo contactar el servidor. Intenta de nuevo.')
      }
    } finally {
      setCargando(false)
    }
  }

  return (
    <div
      className="flex min-h-screen flex-col items-center justify-center bg-[var(--color-background)] px-4 py-10"
      data-testid="auth-screen"
    >
      <div className="w-full max-w-md space-y-8 rounded-xl border border-[var(--border)] bg-[var(--color-surface)] p-8 shadow-sm">
        <header className="space-y-2 text-center">
          <h1 className="text-xl font-semibold text-[var(--foreground)]">Identificación</h1>
          <p className="text-sm text-[var(--color-text-muted)]">
            Para continuar, ingresa tu documento de identidad y tu nombre. Estos datos se usan solo
            para asociar la conversación en este asistente.
          </p>
        </header>

        <form className="space-y-6" onSubmit={enviar} noValidate>
          <div className="space-y-2">
            <Label htmlFor={idDoc}>Documento de identidad</Label>
            <Input
              id={idDoc}
              name="documento_identidad"
              autoComplete="username"
              inputMode="text"
              aria-invalid={errores.documento ? true : undefined}
              aria-describedby={errores.documento ? errDocId : undefined}
              value={documento}
              onChange={(ev) => setDocumento(ev.target.value)}
              disabled={cargando}
            />
            {errores.documento ? (
              <p id={errDocId} className="text-sm text-[var(--destructive)]" role="alert">
                {errores.documento}
              </p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor={idNombre}>Nombre completo</Label>
            <Input
              id={idNombre}
              name="nombre"
              autoComplete="name"
              aria-invalid={errores.nombre ? true : undefined}
              aria-describedby={errores.nombre ? errNombreId : undefined}
              value={nombre}
              onChange={(ev) => setNombre(ev.target.value)}
              disabled={cargando}
            />
            {errores.nombre ? (
              <p id={errNombreId} className="text-sm text-[var(--destructive)]" role="alert">
                {errores.nombre}
              </p>
            ) : null}
          </div>

          <Button type="submit" className="w-full" disabled={cargando}>
            {cargando ? 'Ingresando…' : 'Continuar al asistente'}
          </Button>
        </form>
      </div>
    </div>
  )
}
