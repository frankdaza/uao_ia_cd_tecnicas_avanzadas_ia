import { describe, expect, it } from 'vitest'
import {
  LONGITUD_MINIMA_PROMPT_INSTITUCIONAL,
  validarHistorialTurnosMax,
  validarIdentificadorModelo,
  validarLongitudPromptInstitucional,
  validarTemperatura,
  validarTopP,
} from './adminFormValidators'

describe('validarIdentificadorModelo', () => {
  it('rechaza vacío o solo espacios', () => {
    expect(validarIdentificadorModelo('')).not.toBeNull()
    expect(validarIdentificadorModelo('   ')).not.toBeNull()
  })
  it('acepta identificador no vacío', () => {
    expect(validarIdentificadorModelo(' gpt-4o-mini ')).toBeNull()
  })
})

describe('validarTemperatura', () => {
  it('rechaza fuera de rango', () => {
    expect(validarTemperatura('-0.1')).not.toBeNull()
    expect(validarTemperatura('2.1')).not.toBeNull()
  })
  it('acepta límites', () => {
    expect(validarTemperatura('0')).toBeNull()
    expect(validarTemperatura('2')).toBeNull()
  })
})

describe('validarTopP', () => {
  it('permite vacío si es opcional', () => {
    expect(validarTopP('', true)).toBeNull()
  })
  it('valida rango cuando hay valor', () => {
    expect(validarTopP('0.5', true)).toBeNull()
    expect(validarTopP('1.1', true)).not.toBeNull()
  })
})

describe('validarHistorialTurnosMax', () => {
  it('rechaza fuera de rango o no entero', () => {
    expect(validarHistorialTurnosMax('0')).not.toBeNull()
    expect(validarHistorialTurnosMax('201')).not.toBeNull()
    expect(validarHistorialTurnosMax('3.5')).not.toBeNull()
  })
  it('acepta enteros en rango', () => {
    expect(validarHistorialTurnosMax('1')).toBeNull()
    expect(validarHistorialTurnosMax('20')).toBeNull()
    expect(validarHistorialTurnosMax('200')).toBeNull()
  })
})

describe('validarLongitudPromptInstitucional', () => {
  it('exige longitud mínima', () => {
    const corto = 'x'.repeat(LONGITUD_MINIMA_PROMPT_INSTITUCIONAL - 1)
    expect(validarLongitudPromptInstitucional(corto)).not.toBeNull()
    const ok = 'x'.repeat(LONGITUD_MINIMA_PROMPT_INSTITUCIONAL)
    expect(validarLongitudPromptInstitucional(ok)).toBeNull()
  })
})
