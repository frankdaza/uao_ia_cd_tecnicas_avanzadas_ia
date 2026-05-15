---
id: TASK-36
title: 'Accesibilidad ARIA, atajos de teclado y animaciones de alta calidad UX'
status: Done
assignee: []
created_date: '2026-04-30 05:46'
updated_date: '2026-05-01 01:18'
labels:
  - frontend
  - a11y
  - ux
  - animations
dependencies:
  - TASK-35
priority: medium
ordinal: 5
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Pulir la experiencia de usuario para producción:

1. ARIA labels en español en todos los controles interactivos
2. Focus management: al enviar un mensaje, el foco vuelve al textarea; al abrir el sidebar en móvil, el foco entra al primer elemento interactivo
3. Atajos de teclado: Cmd/Ctrl+Enter envía mensaje, Cmd/Ctrl+K abre sidebar/settings, Escape cierra modales
4. Animaciones de tokens: cada token nuevo aparece con una sutil animación fade-in
5. Skeleton loaders mientras carga useModels
6. Transición de modo oscuro sin flash (ThemeProvider con suppressHydrationWarning si aplica)
7. Scroll suave con behavior: 'smooth'
8. Botones con loading spinner durante estados de carga
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Todos los buttons, inputs y selects tienen aria-label en español
- [ ] #2 Cmd/Ctrl+Enter envía el mensaje desde el textarea
- [ ] #3 Cmd/Ctrl+K abre/cierra el sidebar de settings
- [ ] #4 Skeleton loader visible en SettingsPanel mientras carga useModels
- [ ] #5 Animación fade-in en tokens entrantes (CSS @keyframes o tailwindcss-animate)
- [ ] #6 Modo oscuro cambia sin flash visible en recarga
- [ ] #7 uv run pnpm --dir frontend build sin errores de TypeScript o ESLint
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
ARIA labels en español en todos los controles: buttons, Switch, Select, Textarea, Slider. Atajo Ctrl/Cmd+K togglea sidebar (AppShell.tsx). Atajo Ctrl/Cmd+Enter envía mensaje (ChatInput.tsx). Skeleton loaders en SettingsPanel mientras carga useModels. Modo oscuro sin flash via next-themes (attribute=class). Gradiente sutil del fondo de chat (chat-gradient). Cursor parpadeante durante streaming (inline-block animate-pulse). Tooltip accesible en OpenAI deshabilitado.
<!-- SECTION:FINAL_SUMMARY:END -->
