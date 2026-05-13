import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { waitFor } from '@testing-library/react'
import { ThemeProvider } from 'next-themes'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Toaster } from 'sonner'
import * as sonner from 'sonner'
import { Chat } from '@/features/chat/Chat'

const mocks = vi.hoisted(() => ({
  abort: vi.fn(),
  streamAgente: vi.fn(),
  getHistorialSesion: vi.fn(() => Promise.resolve({ mensajes: [] as { rol: 'human'; contenido: string }[] })),
}))

vi.mock('@/lib/sseClient', () => ({
  streamAgente: (...args: unknown[]) => mocks.streamAgente(...args),
}))

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>()
  return {
    ...actual,
    getHistorialSesion: (...args: unknown[]) => mocks.getHistorialSesion(...args),
  }
})

vi.mock('@/features/auth/AuthContext', () => ({
  useAuth: () => ({
    usuario: {
      usuarioId: '550e8400-e29b-41d4-a716-446655440000',
      sessionId: 'user:550e8400-e29b-41d4-a716-446655440000',
      nombre: 'Usuario prueba',
    },
    sessionId: 'user:550e8400-e29b-41d4-a716-446655440000',
    nombreMostrado: 'Usuario prueba',
    iniciarSesion: vi.fn(),
    cerrarSesion: vi.fn(),
  }),
}))

function renderChat() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
        <TooltipProvider>
          <Chat />
          <Toaster />
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>,
  )
}

describe('Chat', () => {
  beforeEach(() => {
    mocks.abort.mockReset()
    mocks.streamAgente.mockReset()
    mocks.getHistorialSesion.mockReset()
    mocks.getHistorialSesion.mockResolvedValue({ mensajes: [] })
  })

  it('muestra la bienvenida y ejecuta una consulta vía SSE del agente', async () => {
    mocks.streamAgente.mockImplementation((_ep, peticion, handlers) => {
      expect(peticion).toMatchObject({ pregunta: '¿Misión institucional?' })
      handlers.onToken('agente', 'Hola')
      handlers.onFinal({ motor: 'agente', texto: 'Hola', latencia_ms: 1, modelo: 'test', metricas: null })
      return { abort: mocks.abort }
    })
    const user = userEvent.setup()
    renderChat()

    await waitFor(() => {
      expect(mocks.getHistorialSesion).toHaveBeenCalled()
    })

    expect(screen.getByRole('heading', { name: /¿en qué puedo ayudarte hoy/i })).toBeInTheDocument()

    await user.type(screen.getByRole('textbox'), '¿Misión institucional?')
    await user.click(screen.getByRole('button', { name: /enviar/i }))

    await waitFor(() =>
      expect(mocks.streamAgente).toHaveBeenCalledWith(
        '/api/agente/stream',
        expect.objectContaining({ pregunta: '¿Misión institucional?' }),
        expect.any(Object),
      ),
    )
    await waitFor(() => expect(screen.getByText('Hola')).toBeInTheDocument())
  })

  it('muestra toast de error cuando el SSE reporta fallo', async () => {
    const toastSpy = vi.spyOn(sonner.toast, 'error').mockImplementation(() => 'id')
    mocks.streamAgente.mockImplementation((_ep, _peticion, handlers) => {
      handlers.onError('sistema', 'fallo-demo', 'x')
      return { abort: mocks.abort }
    })
    const user = userEvent.setup()
    renderChat()

    await waitFor(() => expect(mocks.getHistorialSesion).toHaveBeenCalled())

    await user.type(screen.getByRole('textbox'), '¿Test error?')
    await user.click(screen.getByRole('button', { name: /enviar/i }))

    await waitFor(() =>
      expect(toastSpy).toHaveBeenCalledWith(expect.stringContaining('fallo-demo')),
    )
    toastSpy.mockRestore()
  })

  it('el botón Detener invoca abort mientras hay stream activo', async () => {
    mocks.streamAgente.mockImplementation(() => ({ abort: mocks.abort }))
    const user = userEvent.setup()
    renderChat()

    await waitFor(() => expect(mocks.getHistorialSesion).toHaveBeenCalled())

    await user.type(screen.getByRole('textbox'), '¿Stream largo?')
    await user.click(screen.getByRole('button', { name: /enviar/i }))

    const detener = await screen.findByRole('button', { name: /detener/i })
    await user.click(detener)

    await waitFor(() => expect(mocks.abort).toHaveBeenCalled())
  })
})
