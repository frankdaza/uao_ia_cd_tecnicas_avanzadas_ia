---
id: TASK-115
title: 'Tests integración TAAM: /chat, webhook Telegram mock, alertas, regresión M3'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:18'
updated_date: '2026-05-24 16:36'
labels:
  - modulo-3
  - taam
  - tests
  - pytest
milestone: m-0
dependencies:
  - TASK-106
  - TASK-104
references:
  - proyecto-2/tests/README.md
  - proyecto-2/tests/api/test_chat.py
  - proyecto-2/tests/api/test_telegram_webhook.py
  - proyecto-2/tests/api/test_staff_seguimiento.py
  - proyecto-2/tests/agentes/test_tools_oltp.py
  - proyecto-2/tests/ingesta/test_protocolo_pdf.py
  - proyecto-2/tests/integracion/test_aislamiento_m3.py
  - >-
    backlog/decisions/decision-7 -
    Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md
modified_files:
  - proyecto-2/tests/README.md
  - proyecto-2/tests/integracion/test_aislamiento_m3.py
  - proyecto-2/tests/api/test_chat.py
  - proyecto-2/README.md
priority: high
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La rúbrica M3 valora **calidad de código (~20%)** y trazabilidad UC-MVP-01..05. La demo en vivo (TASK-114) **no sustituye** pruebas automatizadas: el evaluador debe poder ejecutar `uv run pytest` en `proyecto-2/` sin Telegram real, sin OpenAI en el camino caliente de la suite por defecto, y sin depender de M2 (`proyecto-1/`).

**Ámbito:** consolidar y documentar la suite ya iniciada en TASK-104 (`POST /chat`), TASK-106 (webhook Telegram), TASK-108 (alertas staff), TASK-103 (tools agente), ingesta PDF→Qdrant; añadir **regresión de aislamiento M3** frente a M2 según [decision-7](../decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md).

**Dependencias:** TASK-104, TASK-106 (contratos HTTP listos). Reutiliza fixtures de `tests/api/conftest.py` (SQLite en memoria, secretos de prueba, mock `ClienteTelegram.enviar_mensaje`).

## Objetivo

Suite pytest **determinística** en `proyecto-2/tests/` que cubra los caminos críticos del MVP TAAM con mocks (agente, Telegram, embeddings/Qdrant en memoria) y documente cómo ejecutar pruebas opcionales contra Postgres Docker.

## Matriz de cobertura (archivos canónicos)

| UC / capacidad | Ruta o módulo | Archivo de prueba |
|----------------|---------------|-------------------|
| UC-MVP-03 chat | `POST /chat` | `tests/api/test_chat.py` |
| UC-MVP-02 Telegram | `POST /api/integracion/telegram/webhook` | `tests/api/test_telegram_webhook.py` |
| Triage + alerta OLTP | tools `clasificar_triage`, `escalar_a_equipo` | `tests/agentes/test_tools_oltp.py` |
| UC-MVP-05 staff | `GET/PATCH /api/staff/alertas` | `tests/api/test_staff_seguimiento.py` |
| UC-MVP-01 ingesta | hash/idempotencia, Qdrant `:memory:` | `tests/ingesta/test_protocolo_pdf.py` |
| Aislamiento M3 | sin import M2, salud `proyecto=taam` | `tests/integracion/test_aislamiento_m3.py` |
| Postgres opcional | Alembic esquema TAAM | `tests/persistencia/test_migracion_taam_postgres.py` (`@pytest.mark.integration_postgres`) |

## Infraestructura de pruebas

- **Unit/API (default):** `app_api` + `cliente_api` (SQLite `:memory:`, lifespan FastAPI); `RECORDATORIOS_JOB_HABILITADO=false` por autouse.
- **Mocks obligatorios en CI:** `invocar_agente`, `ClienteTelegram.enviar_mensaje`; `OPENAI_API_KEY=sk-test-falso` solo donde ingesta lo exige.
- **Opcional Docker:** `EJECUTAR_INTEGRACION_POSTGRES=1` + Postgres TAAM en `:15433` (ver `tests/README.md`).
- **Marcador:** `integration_postgres` (no confundir con “integration” genérico de otros repos).

## Fallas a evitar

- Tests flakey por el job de recordatorios (mantener deshabilitado en API tests).
- Depender del orden entre tests o de `TELEGRAM_BOT_TOKEN` / claves OpenAI reales.
- Importar código de `proyecto-1` en runtime TAAM (regresión M2).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 `cd proyecto-2 && uv run pytest` pasa en entorno documentado (`tests/README.md`); sin `TELEGRAM_BOT_TOKEN` ni OpenAI real en la suite por defecto
- [x] #2 #2 `tests/api/test_chat.py` cubre 403 sin vínculo y 200 con mock; `tests/api/test_telegram_webhook.py` cubre secret inválido/ausente (403)
- [x] #3 #3 Ningún test en `tests/` lee `TELEGRAM_BOT_TOKEN` del entorno para pasar; envío Telegram mockeado vía `ClienteTelegram.enviar_mensaje`
- [x] #4 #4 `tests/agentes/test_tools_oltp.py::test_escalar_a_equipo_crea_alerta` verifica fila `alertas_triage` con severidad `urgente`
- [x] #5 #5 `proyecto-2/tests/README.md` explica carpetas, mocks, marcador `integration_postgres` y diferencia con tests unitarios/API
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Inventario:** verificar que existen y pasan `test_chat.py`, `test_telegram_webhook.py`, `test_staff_seguimiento.py`, `test_tools_oltp.py` (alerta urgente), `test_protocolo_pdf.py` (idempotencia/Qdrant memoria).
2. **Documentación:** crear `proyecto-2/tests/README.md` (comandos `uv run pytest`, marcador `integration_postgres`, variables de entorno, tabla de carpetas, política sin tokens reales).
3. **Regresión M3:** añadir `tests/integracion/test_aislamiento_m3.py` (sin imports `proyecto_1`/`proyecto-1`, salud TAAM, puertos documentados en compose).
4. **Higiene:** corregir warning de coroutine en `test_chat_503_timeout` si persiste tras `pytest`.
5. **README raíz:** enlace breve a `tests/README.md` en sección de pruebas.
6. **Cierre:** `uv run pytest` verde; actualizar TASK-115 (AC, notas, `finalSummary`, status Done).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Fixtures compartidas API: `tests/api/conftest.py` (`SECRETO_TELEGRAM_TEST`, JWT staff demo, PDF mínimo).
- Agente tools: `tests/agentes/conftest.py` (`caso_vinculado_telegram_123`, `contexto_agente_123`).
- Checkpointer Postgres: `tests/agentes/test_checkpointer_postgres.py` también usa `integration_postgres`.
- Comando CI local documentado: `cd proyecto-2 && uv sync && uv run pytest` (opcional `-m 'not integration_postgres'` implícito: esos tests hacen skip sin env).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Consolidada la suite TAAM de integración/unit con documentación y regresión M3. Añadidos `proyecto-2/tests/README.md` (comandos, marcador `integration_postgres`, mocks, matriz UC→archivos) y `tests/integracion/test_aislamiento_m3.py` (AST sin imports de proyecto-1, salud `taam`, puertos en compose). Corregido `test_chat_503_timeout` para evitar warning de coroutine. Enlace en `proyecto-2/README.md`. Verificación: `uv run pytest` → 151 passed, 2 skipped (Postgres opcional). Descripción, AC, DoD y plan de TASK-115 ampliados en Backlog.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv run pytest` en `proyecto-2/` pasa sin variables de Telegram/OpenAI reales
- [x] #2 `proyecto-2/tests/README.md` describe unit vs `integration_postgres` y comandos
- [x] #3 Regresión M3: tests de aislamiento sin import de `proyecto-1`
- [x] #4 TASK-115 actualizada en Backlog con AC marcados y `finalSummary`
<!-- DOD:END -->
