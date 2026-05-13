import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthProvider, useAuth } from '@/features/auth/AuthContext'
import { AUTH_STORAGE_KEY } from '@/features/auth/authStorage'
import * as api from '@/lib/api'

vi.mock('@/lib/api', async (importOriginal) => {
  const mod = await importOriginal<typeof import('@/lib/api')>()
  return {
    ...mod,
    postIniciarSesion: vi.fn(),
    postCerrarSesion: vi.fn().mockResolvedValue({ ok: true, mensaje: 'Sesion cerrada' }),
  }
})

function SesionProbe() {
  const { sessionId, iniciarSesion, cerrarSesion } = useAuth()
  return (
    <div>
      <span data-testid="session-id">{sessionId ?? 'none'}</span>
      <button
        type="button"
        onClick={() => {
          void iniciarSesion({ documento_identidad: '12345678', nombre: 'Usuario Prueba' }).catch(
            () => {
              /* errores cubiertos en pruebas de AuthScreen / toast */
            },
          )
        }}
      >
        iniciar-sesion
      </button>
      <button type="button" onClick={() => void cerrarSesion()}>
        cerrar-sesion
      </button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.mocked(api.postIniciarSesion).mockResolvedValue({
      usuario_id: '00000000-0000-4000-8000-000000000099',
      session_id: 'user:00000000-0000-4000-8000-000000000099',
      nombre: 'Usuario Prueba',
      ya_existia: false,
    })
  })

  it('hidrata sesión desde localStorage sin llamar al API', () => {
    localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({
        v: 1,
        usuarioId: '00000000-0000-4000-8000-000000000099',
        sessionId: 'user:00000000-0000-4000-8000-000000000099',
        nombre: 'Persistido',
      }),
    )
    render(
      <AuthProvider>
        <SesionProbe />
      </AuthProvider>,
    )
    expect(screen.getByTestId('session-id')).toHaveTextContent(
      'user:00000000-0000-4000-8000-000000000099',
    )
    expect(api.postIniciarSesion).not.toHaveBeenCalled()
  })

  it('persiste en localStorage tras iniciar sesión exitosa', async () => {
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <SesionProbe />
      </AuthProvider>,
    )
    await user.click(screen.getByRole('button', { name: /iniciar-sesion/i }))
    await waitFor(() => {
      expect(screen.getByTestId('session-id')).toHaveTextContent(
        'user:00000000-0000-4000-8000-000000000099',
      )
    })
    const raw = localStorage.getItem(AUTH_STORAGE_KEY)
    expect(raw).toBeTruthy()
    expect(JSON.parse(raw as string).nombre).toBe('Usuario Prueba')
  })

  it('no persiste sesión si el API falla', async () => {
    vi.mocked(api.postIniciarSesion).mockRejectedValueOnce(new Error('network down'))
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <SesionProbe />
      </AuthProvider>,
    )
    await user.click(screen.getByRole('button', { name: /iniciar-sesion/i }))
    await waitFor(() => expect(api.postIniciarSesion).toHaveBeenCalled())
    expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull()
    expect(screen.getByTestId('session-id')).toHaveTextContent('none')
  })

  it('cerrarSesion limpia estado y localStorage', async () => {
    localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({
        v: 1,
        usuarioId: '00000000-0000-4000-8000-000000000099',
        sessionId: 'user:00000000-0000-4000-8000-000000000099',
        nombre: 'X',
      }),
    )
    const user = userEvent.setup()
    render(
      <AuthProvider>
        <SesionProbe />
      </AuthProvider>,
    )
    await waitFor(() => expect(screen.getByTestId('session-id')).not.toHaveTextContent('none'))
    await user.click(screen.getByRole('button', { name: /cerrar-sesion/i }))
    await waitFor(() => expect(screen.getByTestId('session-id')).toHaveTextContent('none'))
    expect(localStorage.getItem(AUTH_STORAGE_KEY)).toBeNull()
    expect(api.postCerrarSesion).toHaveBeenCalled()
  })
})
