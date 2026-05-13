import { test, expect } from '@playwright/test'

/**
 * Chat M2 con API interceptada (SSE sintético).
 * Evita depender de Postgres/OpenAI en CI; valida login + dos turnos (FAQ y abierta).
 */

function cuerpoSseAgenteStub(pregunta: string): string {
  const esFaq = /PBX|horario|tel[eé]fono/i.test(pregunta)
  const herramienta = esFaq ? 'faq_estructurada' : 'rag_denso'
  const texto = esFaq ? 'Respuesta FAQ (stub Playwright).' : 'Respuesta amplia RAG (stub Playwright).'
  const eventos = [
    { tipo: 'pensamiento', herramienta_candidata: herramienta, razon: 'stub e2e' },
    { tipo: 'herramienta', nombre: herramienta, latencia_ms: 2 },
    { tipo: 'token', motor: 'agente', texto },
    { tipo: 'final', motor: 'agente', texto, latencia_ms: 10, modelo: 'stub', metricas: null },
  ] as const
  return eventos.map((ev) => `data: ${JSON.stringify(ev)}\n`).join('')
}

test.describe('chat modulo 2 (API stub)', () => {
  test.beforeEach(async ({ context }) => {
    await context.addInitScript(() => {
      localStorage.removeItem('fvl-auth-v1')
    })
  })

  test('login y FAQ + pregunta abierta', async ({ page }) => {
    await page.route('**/api/sesiones/actual/historial', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ mensajes: [] }),
      })
    })

    await page.route('**/api/sesiones', async (route) => {
      if (route.request().method() !== 'POST') {
        await route.continue()
        return
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          usuario_id: '00000000-0000-4000-8000-00000000e2e2',
          session_id: 'user:00000000-0000-4000-8000-00000000e2e2',
          nombre: 'Usuario Playwright',
          ya_existia: false,
          ultimo_mensaje_at: null,
        }),
      })
    })

    await page.route('**/api/agente/stream', async (route) => {
      if (route.request().method() !== 'POST') {
        await route.continue()
        return
      }
      let pregunta = ''
      try {
        const data = route.request().postDataJSON() as { pregunta?: string }
        pregunta = data?.pregunta ?? ''
      } catch {
        pregunta = ''
      }
      await route.fulfill({
        status: 200,
        contentType: 'text/event-stream; charset=utf-8',
        body: cuerpoSseAgenteStub(pregunta),
      })
    })

    await page.goto('/')
    await expect(page.getByTestId('auth-screen')).toBeVisible()
    await page.getByLabel(/documento de identidad/i).fill('87654321')
    await page.getByLabel(/nombre completo/i).fill('Usuario Playwright')
    await page.getByRole('button', { name: /continuar al asistente/i }).click()

    const campo = page.getByLabel(/escribe tu pregunta/i)
    await expect(campo).toBeVisible({ timeout: 15_000 })

    await campo.fill('¿Cuál es el teléfono PBX?')
    await page.getByRole('button', { name: /enviar pregunta/i }).click()
    await expect(page.getByText(/Respuesta FAQ \(stub Playwright\)/i)).toBeVisible({ timeout: 15_000 })

    await campo.fill('Explique de forma amplia la misión institucional')
    await page.getByRole('button', { name: /enviar pregunta/i }).click()
    await expect(page.getByText(/Respuesta amplia RAG \(stub Playwright\)/i)).toBeVisible({ timeout: 15_000 })
  })
})
