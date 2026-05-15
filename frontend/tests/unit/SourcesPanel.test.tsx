import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import type { RagChunk } from '@/lib/schemas'
import { SourcesPanel } from '@/features/chat/SourcesPanel'

const chunks: RagChunk[] = [
  {
    archivo: 'a.md',
    titulo: 'Titulo demo',
    source_url: 'https://demo.test/a',
    score: 1.234,
  },
]

describe('SourcesPanel', () => {
  it('renderiza fichas RAG y enlace externo cuando hay source_url', () => {
    render(<SourcesPanel chunks={chunks} />)
    expect(screen.getByText(/Titulo demo/)).toBeInTheDocument()
    const link = document.querySelector(`a[href='https://demo.test/a']`)
    expect(link).not.toBeNull()
    expect(screen.getByLabelText(/Abrir fuente: Titulo demo/)).toBeInTheDocument()
  })
})
