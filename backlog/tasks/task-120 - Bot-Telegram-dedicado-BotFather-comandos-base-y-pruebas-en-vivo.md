---
id: TASK-120
title: Bot Telegram dedicado BotFather comandos base y pruebas en vivo
status: In Progress
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-23 05:55'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - telegram
milestone: m-1
dependencies:
  - TASK-119
references:
  - proyecto-3/docs/telegram-bot-setup.md
  - proyecto-3/openfang/openfang.toml
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
  - proyecto-2/README.md
modified_files:
  - proyecto-3/docs/telegram-bot-setup.md
  - proyecto-3/README.md
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Ruta B usa bridge Telegram de OpenFang. El token debe ser **distinto** al de `proyecto-2/` para evitar conflictos de webhook/polling. Se documenta creación vía **BotFather** y comandos `/start`, `/help`, `/version`.

## Objetivo

Bot dedicado operativo contra OpenFang en desarrollo, con guía reproducible y logs sin exponer `chat_id` completo en texto plano.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 `docs/telegram-bot-setup.md` describe: crear bot, copiar token a `.env`, diferenciar de proyecto-2
- [ ] #2 Prueba en vivo: mensaje al bot recibe respuesta del agente OpenFang (eco o respuesta con disclaimer)
- [ ] #3 Comandos `/start` y `/help` documentados; respuesta menciona Bot Lili y límites (no diagnóstico)
- [ ] #4 **Negativo:** token inválido → bridge falla con mensaje claro en logs (401/Unauthorized)
- [ ] #5 **Privacidad:** logs enmascaran `chat_id` (ej. últimos 4 dígitos) en ejemplos del doc
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Crear bot en @BotFather; nombre sugerido `FVL_Lili_RutaB_Dev`.
2. Configurar comandos en BotFather según doc.
3. Arrancar OpenFang (task-119) con `TELEGRAM_BOT_TOKEN` en `.env`.
4. Enviar mensajes de prueba; capturar pantallazo para task-127/133.
5. Documentar troubleshooting (polling vs webhook si aplica).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
```bash
# .env (no commitear)
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# Comandos BotFather (ejemplo)
start - Iniciar conversacion con Bot Lili (TAAM Ruta B)
help - Ayuda y limites del asistente
version - Version OpenFang / hand activo
```

```python
def enmascarar_chat_id(chat_id: str) -> str:
    s = str(chat_id)
    return f"***{s[-4:]}" if len(s) > 4 else "****"
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Doc en español; sin token real en repo
- [ ] #2 Prueba manual registrada en notas de cierre
- [ ] #3 Tarea **Done** sin archivar
<!-- DOD:END -->
