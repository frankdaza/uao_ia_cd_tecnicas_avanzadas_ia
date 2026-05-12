import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { waitFor } from '@testing-library/react'
import type { FuenteBm25 } from '@/lib/schemas'
import { streamQa } from '@/lib/sseClient'

describe('streamQa', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() =>
        Promise.resolve({
          ok: true,
          body: new ReadableStream({
            start(controller) {
              const enc = new TextEncoder()
              controller.enqueue(enc.encode(`data: ${JSON.stringify({ tipo: 'token', motor: 'openai', texto: 'Ho' })}\n\n`))
              controller.enqueue(
                enc.encode(
                  `data: ${JSON.stringify({ tipo: 'final', motor: 'openai', texto: 'Hola', latencia_ms: 10, modelo: 'x' })}\n\n`,
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

  it('emis eventos tipo token y final', async () => {
    const onToken = vi.fn()
    const onFinal = vi.fn()
    streamQa(
      '/api/qa/stream',
      {
        pregunta: 't',
        modelo_openai: 'gpt-4o-mini',
        temperatura: 0.2,
        top_p: 1,
      },
      {
        onToken,
        onFinal,
        onError: vi.fn(),
        onFuentes: (_f: FuenteBm25[]) => {},
      },
    )
    await waitFor(() => {
      expect(onToken).toHaveBeenCalledWith('openai', 'Ho')
      expect(onFinal).toHaveBeenCalled()
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
    const { abort } = streamQa(
      '/api/qa/stream',
      {
        pregunta: 't',
        modelo_openai: 'gpt-4o-mini',
        temperatura: 0.2,
        top_p: 1,
      },
      {
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
