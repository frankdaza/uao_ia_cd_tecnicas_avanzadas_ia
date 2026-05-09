import { test, expect } from '@playwright/test'

/**
 * Tests E2E básicos del flujo principal de la UI.
 * Requieren que el frontend esté corriendo en localhost:5173.
 * En modo CI, el webServer del playwright.config.ts arranca automáticamente.
 */

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
