---
id: TASK-30
title: Tailwind v4 + shadcn/ui + tokens de diseño institucional + temas claro/oscuro
status: Done
assignee: []
created_date: '2026-04-30 05:44'
updated_date: '2026-05-01 01:21'
labels:
  - frontend
  - design-system
  - tailwind
  - shadcn
dependencies:
  - TASK-29
priority: high
ordinal: 11
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Configurar el sistema de diseño de alto impacto visual:

1. Tailwind CSS v4 con plugin Vite (@tailwindcss/vite)
2. shadcn/ui CLI: inicializar, instalar componentes base (button, input, textarea, select, slider, checkbox, switch, accordion, dialog, dropdown-menu, badge, card, separator, tooltip, skeleton)
3. Paleta institucional Valle del Lili: morado primario (#6B21A8), teal secundario (#0D9488), grises neutros, modo oscuro con clase dark
4. next-themes: ThemeProvider para persistir tema en localStorage
5. sonner: toasts de notificación (instalado y configurado en App.tsx)
6. tailwindcss-animate: animaciones de entrada/salida
7. lucide-react: iconos
8. @tanstack/react-query v5: QueryClient y QueryClientProvider en main.tsx
9. Archivo `frontend/src/styles/globals.css`: @import tailwindcss, variables CSS de tokens
10. Definir tipografía: Inter para cuerpo, JetBrains Mono para código (Google Fonts o bundled)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 pnpm --dir frontend build sin errores con todas las dependencias instaladas
- [ ] #2 shadcn/ui inicializado con components.json correcto apuntando a src/components/ui/
- [ ] #3 Tokens CSS de paleta definidos en globals.css: --color-primary, --color-secondary, etc.
- [ ] #4 ThemeProvider funciona: toggle claro/oscuro persiste en localStorage
- [ ] #5 Al menos 10 componentes shadcn/ui instalados en src/components/ui/
- [ ] #6 Componente ThemeToggle.tsx funcional con lucide-react icons Sun/Moon
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Instalados: @tailwindcss/vite 4.2.4, tailwindcss 4.2.4, tailwindcss-animate (vía @plugin), next-themes, sonner, lucide-react, clsx, tailwind-merge, @radix-ui/* (10 primitivas), class-variance-authority. globals.css con paleta institucional Valle del Lili (morado #6B21A8, teal #0D9488), tokens CSS en :root y .dark, tipografía Inter+JetBrains Mono. Componentes shadcn/ui creados manualmente: button, badge, skeleton, slider, switch, select, separator, tooltip, accordion, textarea. pnpm build: éxito (637KB JS).
<!-- SECTION:FINAL_SUMMARY:END -->
