import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { waitFor } from '@testing-library/react'
import { ThemeProvider } from 'next-themes'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { TooltipProvider } from '@/components/ui/tooltip'
import { Toaster } from 'sonner'
import * as sonner from 'sonner'
import { SettingsProvider } from '@/features/settings/SettingsContext'
import { Chat } from '@/features/chat/Chat'

const mocks = vi.hoisted(() => ({
  abort: vi.fn(),
  streamQa: vi.fn(),
}))

vi.mock('@/lib/sseClient', () => ({
  streamQa: (...args: unknown[]) => mocks.streamQa(...args),
}))

function renderChat() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
        <TooltipProvider>
          <SettingsProvider>
            <Chat />
            <Toaster />
          </SettingsProvider>
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>,
  )
}

describe('Chat', () => {
  beforeEach(() => {
    mocks.abort.mockReset()
    mocks.streamQa.mockReset()
  })

  it('muestra la bienvenida y ejecuta una consulta vía SSE', async () => {
    mocks.streamQa.mockImplementation((_ep, _peticion, handlers) => {
      handlers.onToken('openai', 'Hola')
      handlers.onFinal('openai', { motor: 'openai', texto: 'Hola', latencia_ms: 1, modelo: 'test' })
      return { abort: mocks.abort }
    })
    const user = userEvent.setup()
    renderChat()

    expect(screen.getByRole('heading', { name: /¿en qué puedo ayudarte hoy/i })).toBeInTheDocument()

    await user.type(screen.getByRole('textbox'), '¿Misión institucional?')
    await user.click(screen.getByRole('button', { name: /enviar/i }))

    await waitFor(() =>
      expect(mocks.streamQa).toHaveBeenCalledWith(
        '/api/qa/stream',
        expect.objectContaining({ pregunta: '¿Misión institucional?' }),
        expect.any(Object),
      ),
    )
    await waitFor(() => expect(screen.getByText('Hola')).toBeInTheDocument())
  })

  it('muestra toast de error cuando el SSE reporta fallo', async () => {
    const toastSpy = vi.spyOn(sonner.toast, 'error').mockImplementation(() => 'id')
    mocks.streamQa.mockImplementation((_ep, _peticion, handlers) => {
      handlers.onError('sistema', 'fallo-demo')
      return { abort: mocks.abort }
    })
    const user = userEvent.setup()
    renderChat()

    await user.type(screen.getByRole('textbox'), '¿Test error?')
    await user.click(screen.getByRole('button', { name: /enviar/i }))

    await waitFor(() =>
      expect(toastSpy).toHaveBeenCalledWith(expect.stringContaining('fallo-demo')),
    )
    toastSpy.mockRestore()
  })

  it('el botón Detener invoca abort mientras hay stream activo', async () => {
    mocks.streamQa.mockImplementation(() => ({ abort: mocks.abort }))
    const user = userEvent.setup()
    renderChat()

    await user.type(screen.getByRole('textbox'), '¿Stream largo?')
    await user.click(screen.getByRole('button', { name: /enviar/i }))

    const detener = await screen.findByRole('button', { name: /detener/i })
    await user.click(detener)

    await waitFor(() => expect(mocks.abort).toHaveBeenCalled())
  })
})
