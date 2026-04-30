import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { FuenteBm25 } from '@/lib/schemas'
import { SourcesPanel } from '@/features/chat/SourcesPanel'

const fuentes: FuenteBm25[] = [
  {
    archivo: 'a.md',
    titulo: 'Titulo demo',
    source_url: 'https://demo.test/a',
    score: 1.234,
  },
]

describe('SourcesPanel', () => {
  it('renderiza fichas de fuentes y enlace externo', () => {
    render(<SourcesPanel fuentes={fuentes} />)
    expect(screen.getByText(/Titulo demo/)).toBeInTheDocument()
    const link = document.querySelector(`a[href='https://demo.test/a']`)
    expect(link).not.toBeNull()
    expect(screen.getByLabelText(/Abrir fuente: Titulo demo/)).toBeInTheDocument()
  })
})
