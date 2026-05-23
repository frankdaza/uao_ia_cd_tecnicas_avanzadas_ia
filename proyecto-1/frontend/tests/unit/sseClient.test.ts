import { describe, expect, it, vi } from 'vitest'
import { crearAcumuladorBloqueSse, normalizarSaltosLineaSse } from '@/lib/sseClient'

describe('normalizarSaltosLineaSse', () => {
  it('convierte CRLF y CR sueltos a LF', () => {
    expect(normalizarSaltosLineaSse('a\r\nb\rc')).toBe('a\nb\nc')
  })
})

describe('crearAcumuladorBloqueSse', () => {
  it('acepta data: con o sin espacio', () => {
    const payloads: string[] = []
    const acc = crearAcumuladorBloqueSse((raw) => payloads.push(raw))

    acc.pushLinea('event: mensaje')
    acc.pushLinea('data:{"tipo":"token","motor":"x","texto":"h"}')
    acc.pushLinea('')
    acc.pushLinea('data:  {"tipo":"token","motor":"x","texto":"i"}')
    acc.pushLinea('')
    expect(payloads).toEqual([
      '{"tipo":"token","motor":"x","texto":"h"}',
      '{"tipo":"token","motor":"x","texto":"i"}',
    ])
  })

  it('ignora comentarios y emite al delimitar con linea en blanco', () => {
    const payloads: string[] = []
    const acc = crearAcumuladorBloqueSse((raw) => payloads.push(raw))

    acc.pushLinea(':keepalive')
    acc.pushLinea('data:{"tipo":"pensamiento","herramienta_candidata":"rag_denso","razon":"x"}')
    acc.pushLinea('')
    expect(payloads).toHaveLength(1)
    expect(JSON.parse(payloads[0] as string)).toMatchObject({
      tipo: 'pensamiento',
      herramienta_candidata: 'rag_denso',
    })
  })

  it('finalizar vacia un bloque sin linea en blanco final', () => {
    const onPayload = vi.fn()
    const acc = crearAcumuladorBloqueSse(onPayload)
    acc.pushLinea('data:{"ok":true}')
    acc.finalizar()
    expect(onPayload).toHaveBeenCalledTimes(1)
    expect(onPayload).toHaveBeenCalledWith('{"ok":true}')
  })
})
