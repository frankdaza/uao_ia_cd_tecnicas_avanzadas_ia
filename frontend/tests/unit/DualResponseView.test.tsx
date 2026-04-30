import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { Message } from '@/features/chat/MessageBubble'
import { DualResponseView } from '@/features/chat/DualResponseView'

const mensajeDemo: Message = {
  id: '1',
  role: 'assistant',
  motor: 'ollama',
  content: '**Texto demo**',
  isStreaming: false,
}

describe('DualResponseView', () => {
  it('renderiza columna cuando hay sólo mensaje Ollama', () => {
    render(<DualResponseView mensajeOllama={mensajeDemo} mensajeOpenai={null} />)
    expect(screen.getByText(/Texto demo/)).toBeInTheDocument()
    expect(screen.getAllByText(/Ollama \(local\)/).length).toBeGreaterThanOrEqual(1)
  })
})
