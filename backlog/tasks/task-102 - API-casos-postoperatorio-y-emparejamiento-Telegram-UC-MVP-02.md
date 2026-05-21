---
id: TASK-102
title: API casos postoperatorio y emparejamiento Telegram (UC-MVP-02)
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:16'
labels:
  - modulo-3
  - taam
  - fastapi
milestone: m-0
dependencies:
  - TASK-99
  - TASK-100
priority: high
ordinal: 2060
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

UC-MVP-02: el asistente registra el caso quirúrgico de un paciente y habilita el bot. Sin caso activo + vínculo Telegram, UC-MVP-03 falla en demo.

## Objetivo

API para alta de `casos_postoperatorio` y flujo de emparejamiento paciente↔`telegram_chat_id`.

## Endpoints

- `POST /api/staff/casos` — body: paciente_doc_id, paciente_nombre, tipo_procedimiento_id, cirujano_id, cirujano_nombre, fecha_cirugia (ISO), notas_especificas opcional.
- `GET /api/staff/casos` — filtros estado, paginación.
- `POST /api/staff/casos/{id}/codigo-emparejamiento` — genera código corto (6-8 chars, TTL 24h).
- `POST /api/telegram/emparejar` — body: codigo + chat_id (invocado desde webhook al recibir `/start CODIGO`).

## Reglas de negocio

- Un `telegram_chat_id` solo a un caso **activo** a la vez.
- Código expirado → mensaje Telegram amable con instrucción de contactar asistente.
- Validar que `tipo_procedimiento_id` exista y tenga `indexacion_estado=ok` antes de activar caso.

## Fallas a evitar

- Permitir chat sin emparejar (el agente no debe responder clínico hasta vínculo).
- Código reutilizable infinitamente (usar one-time o invalidar tras uso).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 POST caso persiste fila y devuelve id + estado activo
- [ ] #2 Generación de código guarda TTL y asocia a caso_id
- [ ] #3 Emparejar con código válido crea vinculo_telegram y responde 200
- [ ] #4 Código inválido/expirado devuelve error manejado por capa Telegram
- [ ] #5 Tests cubren doble emparejamiento mismo chat_id (409) y caso sin procedimiento indexado (422)
<!-- AC:END -->
