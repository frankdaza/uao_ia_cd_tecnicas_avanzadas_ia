---
id: TASK-107
title: Recordatorios proactivos Telegram y plantillas por procedimiento (UC-MVP-04)
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
labels:
  - modulo-3
  - taam
  - scheduler
  - telegram
milestone: m-0
dependencies:
  - TASK-106
  - TASK-102
priority: medium
ordinal: 2110
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

UC-MVP-04: recordatorios de medicación/terapias. MVP **sin** email ni agenda hospitalaria: plantillas por `tipo_procedimiento` + `fecha_cirugia` del caso.

## Objetivo

Scheduler + envío Telegram usando mismas credenciales TASK-106.

## Diseño

1. CRUD semilla `plantillas_recordatorio` (puede ser migración 0002 o fixture).
2. Al crear caso (TASK-102), calcular `programado_at = fecha_cirugia + offset_horas`.
3. Job cada minuto (APScheduler en lifespan o asyncio task) busca pendientes `programado_at <= now()` y `enviado_at IS NULL`.
4. Enviar mensaje Telegram al `chat_id` del caso; marcar `recordatorios_enviados`.
5. **Demo:** endpoint staff `POST /api/staff/casos/{id}/disparar-recordatorio-prueba` para sustentación sin esperar horas.

## Texto

- Plantilla con placeholders: `{nombre_paciente}`, `{tipo_procedimiento}`, `{texto_cuidado}`.

## Fallas a evitar

- Enviar recordatorio si caso sin vínculo Telegram (skip + log).
- Duplicar envíos (transacción o lock por recordatorio_id).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Plantillas asociadas a tipo_procedimiento existen en BD
- [ ] #2 Job envía al menos un recordatorio en entorno de prueba con fecha_cirugia artificial
- [ ] #3 Endpoint de disparo manual funciona para demo
- [ ] #4 No se envía email (fuera de alcance verificado)
- [ ] #5 Tests unitarios de cálculo de programado_at
<!-- AC:END -->
