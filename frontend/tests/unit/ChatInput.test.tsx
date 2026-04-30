import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatInput } from '@/features/chat/ChatInput'

describe('ChatInput', () => {
  it('renderiza el textarea y el botón Enviar', () => {
    render(<ChatInput onSubmit={vi.fn()} isBusy={false} />)
    expect(screen.getByRole('textbox')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /enviar/i })).toBeInTheDocument()
  })

  it('llama a onSubmit con el texto al hacer clic en Enviar', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()
    render(<ChatInput onSubmit={onSubmit} isBusy={false} />)

    await user.type(screen.getByRole('textbox'), '¿Cuál es la misión de la FVL?')
    await user.click(screen.getByRole('button', { name: /enviar/i }))

    expect(onSubmit).toHaveBeenCalledWith('¿Cuál es la misión de la FVL?')
  })

  it('bloquea el campo y el botón de enviar mientras isBusy', () => {
    render(<ChatInput onSubmit={vi.fn()} isBusy />)
    expect(screen.getByRole('textbox')).toBeDisabled()
    expect(screen.getByRole('button', { name: /enviar/i })).toBeDisabled()
  })

  it('invoca onStop al pulsar Detener', async () => {
    const onStop = vi.fn()
    const user = userEvent.setup()
    render(<ChatInput onSubmit={vi.fn()} isBusy onStop={onStop} />)
    await user.click(screen.getByRole('button', { name: /detener/i }))
    expect(onStop).toHaveBeenCalled()
  })

  it('no llama a onSubmit si el textarea está vacío', async () => {
    const onSubmit = vi.fn()
    const user = userEvent.setup()
    render(<ChatInput onSubmit={onSubmit} isBusy={false} />)
    await user.click(screen.getByRole('button', { name: /enviar/i }))
    expect(onSubmit).not.toHaveBeenCalled()
  })
})
