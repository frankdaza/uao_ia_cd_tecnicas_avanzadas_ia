import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { ReactElement } from 'react'
import { ThemeProvider } from 'next-themes'
import { MessageBubble } from '@/features/chat/MessageBubble'

function wrapper(ui: ReactElement) {
  return (
    <ThemeProvider attribute="class" defaultTheme="light" enableSystem={false}>
      {ui}
    </ThemeProvider>
  )
}

const baseMessage = {
  id: 'test-1',
  role: 'user' as const,
  content: 'Hola, ¿cuáles son los servicios?',
}

describe('MessageBubble', () => {
  it('renderiza el contenido del mensaje de usuario', () => {
    render(wrapper(<MessageBubble message={baseMessage} />))
    expect(screen.getByText(/cuáles son los servicios/i)).toBeInTheDocument()
  })

  it('renderiza Markdown en mensajes del asistente', () => {
    const msg = {
      id: 'test-2',
      role: 'assistant' as const,
      content: '**Negritas** y `código`',
    }
    render(wrapper(<MessageBubble message={msg} />))
    expect(screen.getByRole('strong') ?? document.querySelector('strong')).not.toBeNull()
  })

  it('muestra skeleton cuando isStreaming=true y content=""', () => {
    const msg = { id: 'test-3', role: 'assistant' as const, content: '', isStreaming: true }
    render(wrapper(<MessageBubble message={msg} />))
    // El skeleton tiene clase animate-pulse
    const skelElements = document.querySelectorAll('.animate-pulse')
    expect(skelElements.length).toBeGreaterThan(0)
  })
})
