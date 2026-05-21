---
id: TASK-106
title: 'Integración Telegram vía 2: webhook FastAPI, envío mensajes, enlace /chat'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
labels:
  - modulo-3
  - taam
  - telegram
  - integracion
milestone: m-0
dependencies:
  - TASK-104
  - TASK-102
priority: high
ordinal: 2100
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**Vía 2 M3:** servidor de integración propio en FastAPI (sin N8N). Es el 30% de la rúbrica «Integración y despliegue en canal».

## Objetivo

Módulo `proyecto-2/src/integracion/telegram/` + router webhook.

## Flujo

1. `POST /api/telegram/webhook` — validar `X-Telegram-Bot-Api-Secret-Token` (o query secret).
2. Parsear `Update`: mensaje texto, `/start`, `/start CODIGO`.
3. `/start CODIGO` → llamar emparejamiento (TASK-102) → mensaje confirmación español.
4. Mensaje normal → construir `session_id=telegram:{chat_id}` → `POST` interno a servicio `/chat` (TASK-104).
5. `sendMessage` vía Bot API con texto respuesta; truncar si >4096 chars.
6. Manejar 403 de /chat → mensaje «debe vincularse con código».

## Configuración

- Script o doc para `setWebhook` apuntando a URL pública (ngrok/cloudflare tunnel en dev).
- Modo polling **solo** para desarrollo local sin HTTPS (documentar limitación).

## Fallas a evitar

- No validar secret del webhook (spoofing).
- Procesar el mismo `update_id` dos veces sin control (guardar últimos N ids en memoria/Redis opcional; MVP: tabla `telegram_updates_procesados`).
- Bloquear event loop con llamadas sync a OpenAI (usar async).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Webhook con secret inválido responde 403
- [ ] #2 Mensaje de usuario emparejado recibe respuesta del agente en Telegram (test con mock Bot API)
- [ ] #3 /start CODIGO válido empareja y confirma en español
- [ ] #4 Chat sin emparejar recibe mensaje instructivo, no respuesta clínica
- [ ] #5 README documenta setWebhook y variables TELEGRAM_*
<!-- AC:END -->
