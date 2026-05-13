import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import type { RagChunk } from '@/lib/schemas'
import { streamAgente } from '@/lib/sseClient'

describe('streamAgente', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          body: new ReadableStream({
            start(controller) {
              const enc = new TextEncoder()
              controller.enqueue(
                enc.encode(
                  `data: ${JSON.stringify({ tipo: 'pensamiento', herramienta_candidata: 'rag_denso', razon: 'x' })}\n\n`,
                ),
              )
              controller.enqueue(
                enc.encode(`data: ${JSON.stringify({ tipo: 'token', motor: 'agente', texto: 'Ho' })}\n\n`),
              )
              controller.enqueue(
                enc.encode(
                  `data: ${JSON.stringify({ tipo: 'final', motor: 'agente', texto: 'Hola', latencia_ms: 10, modelo: 'x' })}\n\n`,
                ),
              )
              controller.close()
            },
          }),
        } as Response),
      ),
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('emite pensamiento, token y final', async () => {
    const onPensamiento = vi.fn()
    const onToken = vi.fn()
    const onFinal = vi.fn()
    streamAgente(
      '/api/agente/stream',
      {
        session_id: 'user:550e8400-e29b-41d4-a716-446655440000',
        pregunta: 't',
        primer_turno: false,
      },
      {
        onPensamiento,
        onHerramienta: vi.fn(),
        onToken,
        onFuentes: (_c: RagChunk[]) => {},
        onFinal,
        onError: vi.fn(),
      },
    )
    await waitFor(() => {
      expect(onPensamiento).toHaveBeenCalledWith('rag_denso', 'x')
      expect(onToken).toHaveBeenCalledWith('agente', 'Ho')
      expect(onFinal).toHaveBeenCalledWith(
        expect.objectContaining({ motor: 'agente', texto: 'Hola', latencia_ms: 10, modelo: 'x' }),
      )
    })
  })

  it('invoca abort sin lanzar cuando se cancela', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(
        () =>
          new Promise(() => {
            /* nunca resuelve */
          }),
      ),
    )
    const onError = vi.fn()
    const { abort } = streamAgente(
      '/api/agente/stream',
      {
        session_id: 'user:550e8400-e29b-41d4-a716-446655440000',
        pregunta: 't',
        primer_turno: false,
      },
      {
        onPensamiento: vi.fn(),
        onHerramienta: vi.fn(),
        onToken: vi.fn(),
        onFinal: vi.fn(),
        onError,
        onFuentes: () => {},
      },
    )
    abort()
    await waitFor(() => new Promise((r) => setTimeout(r, 20)))
    expect(onError).not.toHaveBeenCalled()
  })
})
