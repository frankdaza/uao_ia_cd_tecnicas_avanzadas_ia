import '@testing-library/jest-dom'
import { vi } from 'vitest'

/** ``next-themes`` consulta ``matchMedia`` en el efecto de hidratación del tema. */
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

/** Jsdom no implementa ``scrollIntoView`` usado por la lista del chat. */
Element.prototype.scrollIntoView = vi.fn()
