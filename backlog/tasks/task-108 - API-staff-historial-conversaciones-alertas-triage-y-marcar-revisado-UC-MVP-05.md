---
id: TASK-108
title: >-
  API staff: historial conversaciones, alertas triage y marcar revisado
  (UC-MVP-05)
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
labels:
  - modulo-3
  - taam
  - fastapi
  - staff
milestone: m-0
dependencies:
  - TASK-104
  - TASK-105
  - TASK-102
priority: high
ordinal: 2120
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

UC-MVP-05: personal clínico revisa interacciones y valida triage. El checkpointer PostgresSaver guarda hilos; hace falta **vista API** para el frontend staff.

## Objetivo

Endpoints de lectura/actualización para panel (TASK-113).

## Endpoints

- `GET /api/staff/casos/{id}/conversacion` — mensajes del thread `telegram:{chat_id}` (desde PostgresSaver o tabla espejo); enmascarar PII según rol.
- `GET /api/staff/alertas` — filtros: `revisado=false`, severidad, `caso_id`, paginación.
- `PATCH /api/staff/alertas/{id}` — `{ "revisado": true }` + timestamp y opcional `staff_id`.
- `GET /api/staff/casos/{id}/resumen` — último triage, conteo mensajes, próximo recordatorio.

## Privacidad

- No exponer `telegram_chat_id` completo a rol asistente si política lo exige (últimos 4 dígitos).
- Auditoría: quién marcó revisado.

## Fallas a evitar

- Leer todo chat_history M2 por error (prefijo tablas TAAM).
- Listar alertas sin índice por `revisado, created_at` (performance).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 GET conversacion devuelve lista ordenada de mensajes para caso con vínculo
- [ ] #2 GET alertas filtra no revisadas
- [ ] #3 PATCH marca revisado idempotente
- [ ] #4 Tests con fixture de alerta y thread mock
- [ ] #5 OpenAPI tag staff documentado
<!-- AC:END -->
