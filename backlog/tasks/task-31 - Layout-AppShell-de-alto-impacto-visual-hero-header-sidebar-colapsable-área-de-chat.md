---
id: TASK-31
title: >-
  Layout AppShell de alto impacto visual: hero header, sidebar colapsable, área
  de chat
status: Done
assignee: []
created_date: '2026-04-30 05:44'
updated_date: '2026-05-01 01:21'
labels:
  - frontend
  - ui
  - layout
dependencies:
  - TASK-30
priority: high
ordinal: 10
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Objetivo

Crear el layout principal de la aplicación:

- `AppShell.tsx`: contenedor principal con grid/flex de 3 zonas (header, [sidebar + main], footer)
- Header con hero: logo/nombre del proyecto, tagline, ThemeToggle, badge de estado de conexión API
- Sidebar colapsable (estado persistido en localStorage): contiene SettingsPanel (placeholder hasta task-34)
- Área principal de chat: ocupa el espacio restante, scrollable
- Footer: créditos del módulo, links a fuentes
- Responsive mobile-first: en móvil el sidebar es un Sheet/Drawer
- Transiciones con tailwindcss-animate: sidebar slide-in, skeleton loaders
- Sin funcionalidad de chat real aún (eso es task-33), solo layout y andamiaje visual
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 AppShell.tsx renderiza sin errores en pnpm dev
- [ ] #2 Header visible con nombre del proyecto y ThemeToggle funcional
- [ ] #3 Sidebar colapsable: click en toggle abre/cierra con animación CSS
- [ ] #4 Estado de colapso persiste en localStorage entre recargas
- [ ] #5 Layout es responsive: en < 768px sidebar se convierte en drawer/sheet
- [ ] #6 Footer con texto de créditos visible
- [ ] #7 Área principal ocupa el espacio disponible y tiene overflow-y-auto
- [ ] #8 App.tsx usa AppShell como contenedor principal
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
AppShell.tsx implementado: header con gradiente institucional, ThemeToggle, botón sidebar toggle. Sidebar colapsable con transición CSS (w-0/w-72), estado persistido en localStorage bajo clave fvl-sidebar-collapsed. Atajo Ctrl/Cmd+K. Area principal flex-1 overflow-hidden. Footer con créditos del módulo. App.tsx usa AppShell con SettingsPanel en sidebar y Chat en área principal.
<!-- SECTION:FINAL_SUMMARY:END -->
