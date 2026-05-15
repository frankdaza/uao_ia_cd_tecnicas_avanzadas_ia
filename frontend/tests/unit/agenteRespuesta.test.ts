import { describe, it, expect } from 'vitest'
import {
  RESPUESTA_SIN_CONTEXTO_FRASE,
  respuestaFinalEsSinInformacion,
} from '@/lib/agenteRespuesta'

describe('agenteRespuesta', () => {
  it('detecta la frase canonica con o sin tildes y texto alrededor', () => {
    expect(respuestaFinalEsSinInformacion(RESPUESTA_SIN_CONTEXTO_FRASE)).toBe(true)
    expect(respuestaFinalEsSinInformacion('  No tengo información suficiente.  ')).toBe(true)
    expect(
      respuestaFinalEsSinInformacion(
        'Con gusto le informo que, según la información disponible, no aplica.\nNo tengo información suficiente.',
      ),
    ).toBe(true)
    expect(respuestaFinalEsSinInformacion('No tengo informacion suficiente')).toBe(true)
  })

  it('no marca respuestas con contexto util', () => {
    expect(respuestaFinalEsSinInformacion('La misión institucional es…')).toBe(false)
    expect(respuestaFinalEsSinInformacion('')).toBe(false)
  })
})
