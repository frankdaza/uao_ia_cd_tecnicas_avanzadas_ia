---
id: TASK-104
title: 'Endpoint REST POST /chat para canal externo (contrato JSON, sin SSE)'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:16'
labels:
  - modulo-3
  - taam
  - fastapi
  - api
milestone: m-0
dependencies:
  - TASK-103
priority: high
ordinal: 2080
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La actividad M3 exige API REST `POST /chat` con mensaje + identificador de sesión (teléfono/chat). El SSE de M2 no aplica a Telegram.

## Objetivo

Endpoint síncrono (o async con timeout) que invoque el agente TASK-103 y devuelva JSON.

## Contrato request

```json
{
  "session_id": "telegram:123456789",
  "mensaje": "texto del paciente",
  "metadata": { "canal": "telegram", "caso_id": "uuid-opcional" }
}
```

## Contrato response

```json
{
  "respuesta": "texto para el paciente",
  "severidad_triage": "info|seguimiento|urgente|null",
  "requiere_revision_humana": false,
  "fuentes": [{"titulo": "...", "fragmento": "..."}],
  "error": null
}
```

## Comportamiento

- 404/403 si session_id sin vínculo Telegram activo (salvo modo mantenimiento documentado).
- Timeout LLM → 503 con mensaje genérico, sin stack trace.
- Idempotencia: no requerida en MVP; documentar que Telegram puede reenviar updates.
- Logging: correlación `session_id` + `update_id` si viene en metadata.

## OpenAPI

Tag `chat`; ejemplos en español latinoamericano.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 POST /chat válido devuelve 200 con respuesta no vacía en entorno mock
- [ ] #2 session_id sin emparejar devuelve 403 con detail en español
- [ ] #3 Timeout simulado del LLM devuelve 503 sin filtrar secretos
- [ ] #4 Tests httpx AsyncClient cubren happy path y sin vínculo
- [ ] #5 OpenAPI documenta schemas request/response
<!-- AC:END -->
