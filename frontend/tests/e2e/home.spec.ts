import { test, expect } from '@playwright/test'

const SESION_LOCAL = {
  v: 1,
  usuarioId: '00000000-0000-4000-8000-000000000001',
  sessionId: 'user:00000000-0000-4000-8000-000000000001',
  nombre: 'Usuario E2E',
}

/**
 * Tests E2E básicos del flujo principal de la UI.
 * Requieren que el frontend esté corriendo en localhost:5173.
 * En modo CI, el webServer del playwright.config.ts arranca automáticamente.
 */

test.beforeEach(async ({ context }) => {
  await context.addInitScript(
    ({ key, value }) => {
      localStorage.setItem(key, value)
    },
    { key: 'fvl-auth-v1', value: JSON.stringify(SESION_LOCAL) },
  )
})
test('la página carga el título correcto', async ({ page }) => {
  await page.goto('/')
  await expect(page).toHaveTitle(/Valle del Lili/i)
})

test('el área de chat muestra el mensaje de bienvenida', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText(/cuál es tu pregunta/i)).toBeVisible()
})

test('el toggle de tema claro/oscuro es visible', async ({ page }) => {
  await page.goto('/')
  const toggleBtn = page.getByRole('button', { name: /cambiar a modo/i })
  await expect(toggleBtn).toBeVisible()
})
