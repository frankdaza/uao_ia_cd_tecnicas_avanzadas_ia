---
id: TASK-113
title: 'Frontend TAAM: panel seguimiento alertas y conversaciones (UC-MVP-05)'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:18'
labels:
  - modulo-3
  - taam
  - frontend
  - staff
milestone: m-0
dependencies:
  - TASK-108
  - TASK-110
priority: high
ordinal: 2170
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Personal clínico hace doble check del triage (UC-MVP-05). Consume TASK-108.

## Objetivo

Feature `features/seguimiento/`.

## Pantallas

- **Bandeja alertas:** tarjetas por severidad (color semántico: info/seguimiento/urgente), filtro no revisadas.
- **Detalle caso:** hilo conversación (markdown ligero o burbujas), metadatos paciente enmascarados, botón «Marcar revisado».
- **Lista casos** con badge de alertas pendientes.

## UX

- Urgente visible arriba; sonner al cargar nuevas alertas (opcional polling 30s).
- Sin edición de mensajes ni respuesta en Telegram (fuera MVP — tooltip explicativo).

## Fallas a evitar

- Renderizar PHI completo en capturas de demo (usar datos ficticios).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Bandeja lista alertas no revisadas desde API
- [ ] #2 Marcar revisado actualiza UI sin recargar página completa
- [ ] #3 Detalle muestra conversación ordenada
- [ ] #4 Severidad urgente destacada visualmente
- [ ] #5 Rol clinico y asistente acceden (según TASK-105)
<!-- AC:END -->
