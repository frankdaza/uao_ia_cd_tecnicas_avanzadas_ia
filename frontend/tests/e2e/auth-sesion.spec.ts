import { test, expect } from '@playwright/test'

/**
 * Flujo de identificación M2 con API simulado (sin backend real).
 * En CI el mock evita depender de Postgres; no valida cookies HTTP-only reales.
 */

test.describe('auth sesión', () => {
  test.beforeEach(async ({ context }) => {
    await context.addInitScript(() => {
      localStorage.removeItem('fvl-auth-v1')
    })
  })

  test('login simulado y recarga mantienen el chat visible', async ({ page }) => {
    test.skip(process.env.CI === 'true', 'En CI se omite: requiere mock estable de /api/sesiones (ver task-58).')

    await page.route('**/api/sesiones', async (route) => {
      if (route.request().method() !== 'POST') {
        await route.continue()
        return
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          usuario_id: '00000000-0000-4000-8000-0000000000aa',
          session_id: 'user:00000000-0000-4000-8000-0000000000aa',
          nombre: 'Usuario Mock',
          ya_existia: false,
          ultimo_mensaje_at: null,
        }),
      })
    })

    await page.goto('/')
    await expect(page.getByTestId('auth-screen')).toBeVisible()

    await page.getByLabel(/documento de identidad/i).fill('12345678')
    await page.getByLabel(/nombre completo/i).fill('Usuario Mock')
    await page.getByRole('button', { name: /continuar al asistente/i }).click()

    await expect(page.getByPlaceholder(/cuál es tu pregunta/i)).toBeVisible({ timeout: 15_000 })

    await page.reload()
    await expect(page.getByPlaceholder(/cuál es tu pregunta/i)).toBeVisible({ timeout: 15_000 })
    await expect(page.getByTestId('auth-screen')).toHaveCount(0)
  })
})
