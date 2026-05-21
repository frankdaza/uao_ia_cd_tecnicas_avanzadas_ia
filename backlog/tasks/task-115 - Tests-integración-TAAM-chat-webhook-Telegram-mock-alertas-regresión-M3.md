---
id: TASK-115
title: 'Tests integración TAAM: /chat, webhook Telegram mock, alertas, regresión M3'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:18'
labels:
  - modulo-3
  - taam
  - tests
  - pytest
milestone: m-0
dependencies:
  - TASK-106
  - TASK-104
priority: high
ordinal: 2190
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Rúbrica 20% calidad código; demo en vivo no sustituye tests automatizados.

## Objetivo

Suite pytest en `proyecto-2/tests/` sin llamadas reales a Telegram/OpenAI en CI.

## Casos mínimos

| Módulo | Prueba |
|--------|--------|
| `/chat` | happy path mock LLM, 403 sin vínculo |
| Webhook | secret inválido, update duplicado, /start código |
| Agente | tool clasificar_triage crea alerta |
| Staff API | listar alertas, marcar revisado |
| Ingesta | idempotencia hash PDF (puede usar Qdrant memoria) |

## Infra tests

- Fixtures: AsyncClient FastAPI, DB transaccional, mock `sendMessage`.
- Marcador `@pytest.mark.integration` para tests que requieren Docker.

## Fallas a evitar

- Tests flakey por timing del scheduler (mockear reloj).
- Depender de orden de ejecución entre tests.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 uv run pytest en proyecto-2 pasa en CI local documentado
- [ ] #2 Cobertura de caminos 403 /chat y webhook secret
- [ ] #3 Ningún test requiere TELEGRAM_BOT_TOKEN real en CI
- [ ] #4 Al menos un test verifica creación de alerta_triage tras severidad urgente mock
- [ ] #5 tests/README explica markers integration vs unit
<!-- AC:END -->
