---
id: TASK-40
title: 'Branding FVL (valledellili.org): auditoría y aplicación visual al frontend Q&A'
status: Done
assignee: []
created_date: '2026-05-01 01:06'
updated_date: '2026-05-01 01:15'
labels:
  - frontend
  - design-system
  - branding
  - ux
dependencies:
  - TASK-30
  - TASK-31
references:
  - 'https://valledellili.org/'
  - frontend/src/styles/globals.css
  - frontend/src/components/AppShell.tsx
documentation:
  - frontend/src/features/chat/
  - .cursor/rules/language-conventions.mdc
priority: high
ordinal: 1
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

TASK-30 ya configuró Tailwind v4, shadcn/ui, temas claro/oscuro y tokens institucionales aproximados (morado + teal) en `frontend/src/styles/globals.css`. TASK-31 definió el layout en `AppShell.tsx`. Esta tarea **valida y refina** contra el sitio público real, no sustituye el design system base.

## Fase 1 — Auditoría de branding desde la web

- Fuente principal: https://valledellili.org/
- Documentar en esta tarea (descripción ampliada o notas al avanzar/cerrar): colores primarios, secundarios, acentos, gradientes, neutros, estados hover/focus si son distinguibles; **tipografía** (familias que usa el sitio).
- Comparación explícita con TASK-30 / `globals.css`: coincide o hay correcciones necesarias.
- Verificar **contraste AA** (modo claro y oscuro) para texto sobre fondos institucionales.

## Fase 2 — Aplicación al frontend actual

- Actualizar tokens en `frontend/src/styles/globals.css` (`:root` y `.dark`); si hace falta, ajustes en `frontend/components.json` o componentes con colores hardcodeados.
- Refinar piezas de alto impacto: **AppShell** (hero, gradientes, bordes), **área de chat** (`frontend/src/features/chat/`), paneles (settings, fuentes), botones primarios y **focus rings** alineados con la marca FVL.
- Convenciones del proyecto: textos de UI en español latinoamericano; identificadores TS en inglés (`.cursor/rules/language-conventions.mdc`).

## Fuera de alcance

Scraping del corpus, cambios de backend; solo identidad visual y capa React/Tailwind/shadcn.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Documentación breve en la tarea (descripción o notas): paleta y tipografía derivadas del sitio, con lista o tabla de hex y rol (primario, secundario, superficie, texto).
- [x] #2 Tokens CSS actualizados en globals.css según la auditoría (claro y oscuro); sin regresiones graves de contraste (orientación AA).
- [x] #3 UI revisada en AppShell y flujo principal de chat: aspecto cohesivo (gradientes, cards, inputs) acorde a la marca FVL.
- [x] #4 `pnpm --dir frontend build` sin errores tras los cambios.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Auditoría de marca (2026-05-01)

Fuente: https://valledellili.org/ — bloque `global-styles-inline-css` y tema `vstheme/assets/css/main.min.css`.

| Rol | Hex | Uso en sitio |
| --- | --- | --- |
| Primario (marca) | #023739 | Títulos, texto principal, `--wp--preset--color--primary` |
| Acento | #02B57D | Enlaces, hovers, `--wp--preset--color--accent` |
| Secundario (lima) | #95D31D | Acentos secundarios, `--wp--preset--color--secondary` |
| Superficie suave | #F6F4FF | `--wp--preset--color--bg-2` |
| Superficie / hover UI | #EBE8F7 | Estados en componentes (p. ej. búsqueda) |
| Borde | #CCC5E9 | Controles y bloques |
| Texto secundario | #585B6D | `--wp--preset--color--gray` |
| Fondo página | #FFFFFF | Base |

**Tipografía en sitio:** `@font-face` Aloevera (primary-*) y Gilroy (secondary-*). **En esta app:** Outfit (display) + Plus Jakarta Sans (UI), cargadas por Google Fonts — equivalentes legibles sin copiar OTF propietarios.

**Comparación TASK-30 / globals anterior:** la paleta morada (#6B21A8) y teal genérico (#0D9488) no coincidían con la marca pública FVL. Se alineó al preset WP y se mapeó el botón primario shadcn al acento #02B57D para CTAs; burbujas de usuario usan #023739 (AA sobre blanco).

**Contraste:** texto #023739 sobre #FFFFFF y #FFFFFF sobre #023739 cumplen orientación AA; avatar usuario lima + texto #023739 mejora respecto a blanco sobre lima.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Auditoría desde HTML/CSS público de valledellili.org (preset global-styles + theme vstheme/main.min.css): primario #023739, acento #02B57D, secundario lima #95D31D, superficie #F6F4FF / #EBE8F7, borde #CCC5E9, texto gris #585B6D. Tipografía web: Aloevera (display) + Gilroy (cuerpo); en el frontend se usan Outfit + Plus Jakarta Sans (Google Fonts) como sustitutos sin archivos OTF del sitio. TASK-30 usaba morado #6B21A8 y teal genérico: se reemplazó por la paleta WP anterior. Cambios: globals.css (tokens claro/oscuro, --color-message-user-*, .chat-gradient, .font-display), index.html (fuentes), AppShell (barra acento, tipografía display, degradado título), MessageBubble/MessageList/SourcesPanel (acentos y burbujas), SettingsPanel (cabecera), button hover en acento, ApiStatusFooter (punto en línea). Build: pnpm --dir frontend build OK.
<!-- SECTION:FINAL_SUMMARY:END -->
