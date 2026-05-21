---
id: TASK-111
title: 'Frontend TAAM: administración catálogo procedimientos y PDF (UC-MVP-01)'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
labels:
  - modulo-3
  - taam
  - frontend
  - admin
milestone: m-0
dependencies:
  - TASK-100
  - TASK-110
priority: high
ordinal: 2150
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Pantalla admin para subir PDF y ver estado de indexación (TASK-100, TASK-101).

## Objetivo

Feature `features/admin-procedimientos/`.

## Pantallas

- Listado procedimientos: nombre, versión vector, estado indexación, fecha.
- Formulario alta: nombre, código, archivo PDF (drag-drop), enviar multipart.
- Detalle: reemplazar PDF, botón «reindexar» si API lo expone.
- Feedback: spinner durante ingesta; error si PDF inválido.

## Integración

- Usar `X-Admin-Key` o JWT rol admin según decisión TASK-105.

## Fallas a evitar

- Subir sin indicar estado de indexación (usuario no sabe si RAG listo).
- No validar tamaño en cliente antes de upload.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Alta de procedimiento con PDF muestra éxito y aparece en listado
- [ ] #2 Estado indexacion visible (pendiente/ok/error)
- [ ] #3 Errores API mostrados en toast español
- [ ] #4 Solo rol admin accede (guard de ruta)
- [ ] #5 Responsive usable en laptop de sustentación
<!-- AC:END -->
