---
id: TASK-106
title: 'Integración Telegram vía 2: webhook FastAPI, envío mensajes, enlace /chat'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
updated_date: '2026-05-22 00:01'
labels:
  - modulo-3
  - taam
  - telegram
  - integracion
milestone: m-0
dependencies:
  - TASK-104
  - TASK-102
modified_files:
  - proyecto-2/src/integracion/telegram/
  - proyecto-2/src/api/routers/telegram_webhook.py
  - proyecto-2/src/api/main.py
  - proyecto-2/src/persistencia/modelos.py
  - proyecto-2/src/persistencia/repositorios/telegram_updates.py
  - proyecto-2/alembic/versions/0002_telegram_updates_procesados.py
  - proyecto-2/scripts/configurar_webhook_telegram.py
  - proyecto-2/tests/api/test_telegram_webhook.py
  - proyecto-2/README.md
  - proyecto-2/tests/persistencia/test_migracion_taam_postgres.py
  - >-
    backlog/tasks/task-106 -
    Integración-Telegram-vía-2-webhook-FastAPI-envío-mensajes-enlace-chat.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**Vía 2 M3** ([decision-7](../decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md)): el mismo proceso FastAPI recibe updates de Telegram, invoca el agente vía servicio interno de `POST /chat` (TASK-104) y responde con `sendMessage`. Sin N8N. Cubre ~30% de la rúbrica «Integración y despliegue en canal».

**Dependencias:** TASK-102 (`emparejar_codigo`, códigos TTL), TASK-104 (`procesar_turno_chat`, `session_id=telegram:{chat_id}`).

## Objetivo

Paquete `proyecto-2/src/integracion/telegram/` (cliente Bot API async, manejador de `Update`, idempotencia) + router **`POST /api/integracion/telegram/webhook`** (canónico ADR). Mantener `POST /api/telegram/emparejar` para pruebas directas.

## Flujo del webhook

1. Validar cabecera **`X-Telegram-Bot-Api-Secret-Token`** (`requerir_secreto_telegram`, ya en `dependencias.py`).
2. **Idempotencia:** si `update_id` ya está en `telegram_updates_procesados`, responder `{"ok": true}` sin reprocesar.
3. Extraer mensaje de texto del `Update` (ignorar otros tipos en MVP).
4. **`/start`** sin código → mensaje de bienvenida e instrucción de emparejamiento (español).
5. **`/start CODIGO`** → `emparejar_codigo` (TASK-102) → `sendMessage` con `mensaje_confirmacion` o `mensaje_telegram` de error.
6. **Texto normal** → `procesar_turno_chat` con `session_id=telegram:{chat_id}` y `metadata.update_id`.
7. Mapear **403** de chat → mensaje instructivo (sin respuesta clínica). **200** → `sendMessage` con `respuesta` (truncar a 4096). **503** → mensaje genérico de reintento.
8. Responder siempre **200** `{"ok": true}` a Telegram tras encolar envío (no bloquear el event loop con HTTP sync).

## Configuración y despliegue

- Variables: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET` (obligatorias para integración activa).
- Script `scripts/configurar_webhook_telegram.py` para `setWebhook` hacia URL pública HTTPS.
- **Polling:** no implementado en producto; documentar que en local sin túnel (ngrok/Cloudflare) solo se prueba vía `httpx` + mocks o `POST` manual al webhook.

## Anti-patrones (evitar)

- Webhook sin validación de secret (spoofing).
- Reprocesar el mismo `update_id` (doble respuesta al paciente).
- Llamadas **sync** a OpenAI/Telegram en el handler (usar `httpx` async + servicios async existentes).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Webhook sin secret o con secret incorrecto responde 403
- [x] #2 Update de paciente emparejado dispara respuesta del agente y sendMessage con texto no vacio (mock Bot API y mock agente)
- [x] #3 /start CODIGO valido empareja y confirma en espanol via Telegram
- [x] #4 Chat sin emparejar recibe mensaje instructivo; invocar_agente no se llama
- [x] #5 Mismo update_id enviado dos veces solo procesa una vez (idempotencia OLTP)
- [x] #6 README documenta setWebhook, variables TELEGRAM_* y limitacion sin HTTPS/polling
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Fase 1 — Modelo e idempotencia
1. Modelo ORM `TelegramUpdateProcesado` + migración Alembic `0002`.
2. Repositorio `registrar_update_id` (insert; duplicado → skip procesamiento).

## Fase 2 — Integración Telegram
3. `integracion/telegram/esquemas.py` — subset Pydantic de `Update`/`Message`.
4. `integracion/telegram/cliente.py` — `enviar_mensaje` async (`httpx`), truncado 4096.
5. `integracion/telegram/manejador.py` — `/start`, emparejar, `procesar_turno_chat`, mapeo HTTP→texto paciente.

## Fase 3 — API y ops
6. `api/routers/telegram_webhook.py` — `POST /api/integracion/telegram/webhook`.
7. Registrar router en `main.py`.
8. `scripts/configurar_webhook_telegram.py` + README (setWebhook, variables, límite polling).

## Fase 4 — Pruebas
9. `tests/api/test_telegram_webhook.py`: secret 403, `/start CODIGO`, chat sin vínculo, turno mock con vínculo, idempotencia `update_id`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Referencias
- ADR: `backlog/decisions/decision-7` — ruta canónica `/api/integracion/telegram/webhook`.
- Emparejamiento: `src/api/servicios/emparejamiento.py`.
- Chat: `src/api/servicios/chat.py` (`_MENSAJE_SIN_VINCULO` alineado con 403).
- Secret: `requerir_secreto_telegram` en `dependencias.py`.
- Tests patrón: `tests/api/conftest.py` (`cabecera_telegram`, `secreto_telegram`).

## Contrato Telegram → /chat
- `session_id`: `telegram:{chat_id}`.
- `metadata`: `{ "canal": "telegram", "update_id": <int> }`.
- No hacer HTTP loopback a `/chat`; importar `procesar_turno_chat` en el mismo proceso.

## Mock en tests
- Monkeypatch `ClienteTelegram.enviar_mensaje` o función módulo para capturar textos enviados.
- Mock `invocar_agente` para turno conversacional sin OpenAI.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Integracion Telegram via 2: paquete src/integracion/telegram (cliente httpx async, manejador /start y turno chat), POST /api/integracion/telegram/webhook con secret, idempotencia telegram_updates_procesados (Alembic 0002), script configurar_webhook_telegram.py y README. Tests en tests/api/test_telegram_webhook.py (6 casos). Consumo interno de procesar_turno_chat y emparejar_codigo sin loopback HTTP.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Router webhook registrado en `crear_app()` bajo `/api/integracion/telegram`
- [x] #2 Migración `0002` + modelo `telegram_updates_procesados` aplicable con `alembic upgrade head`
- [x] #3 `uv run pytest tests/api/test_telegram_webhook.py` pasa; sin regresión en `tests/api/`
- [x] #4 Script `configurar_webhook_telegram.py` ejecutable con token y URL documentados
- [x] #5 Sin secretos ni tokens reales en backlog ni commits
<!-- DOD:END -->
