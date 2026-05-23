---
id: TASK-119
title: openfang.toml config real modelo OpenAI memoria bridge Telegram Hands
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-23 05:54'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - config
milestone: m-1
dependencies:
  - TASK-117
  - TASK-118
references:
  - proyecto-3/openfang/openfang.toml
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
  - backlog/docs/doc-007 - Evaluacion-OpenFang-Proyecto-2-TAAM.md
  - proyecto-3/openfang/agents/bot_lili_taam/agent.toml
  - proyecto-3/scripts/validar_openfang_config.sh
  - proyecto-3/tests/test_openfang_config.py
modified_files:
  - proyecto-3/openfang/openfang.toml
  - proyecto-3/openfang/agents/bot_lili_taam/agent.toml
  - proyecto-3/openfang/hands/taam_lili_hand/HAND.toml
  - proyecto-3/scripts/validar_openfang_config.sh
  - proyecto-3/scripts/arrancar_dev.sh
  - proyecto-3/README.md
  - proyecto-3/tests/test_openfang_config.py
priority: high
ordinal: 250
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

[`proyecto-3/openfang/openfang.toml`](../../proyecto-3/openfang/openfang.toml) tiene secciones comentadas. Esta tarea las activa para el agente **bot_lili_taam**: modelo **OpenAI**, memoria (Vector Store + Structured KV), bridge **Telegram** y registro del Hand **taam_lili_hand**.

## Objetivo

Configuración real que permita `openfang start` sin errores de parseo y dashboard en `http://127.0.0.1:4200` (puerto según docs OpenFang).

## Entregables

`openfang.toml` descomentado y validado; nota en README sobre `OPENFANG_HOME` y carga de variables desde entorno.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Con `.env` cargado (OpenAI + Telegram placeholders o reales), `cd proyecto-3/openfang && openfang start` arranca sin error de configuración
- [x] #2 Dashboard accesible en `http://127.0.0.1:4200` (o puerto documentado si difiere)
- [x] #3 `session_id_format` o equivalente documentado para sesiones `telegram:{chat_id}`
- [x] #4 **Negativo:** `api_key_env` apunta a `OPENAI_API_KEY`; si falta, el log indica variable no definida (no crash silencioso)
- [x] #5 **Alterno:** si la versión pinneada no soporta OpenAI nativo, documentar en README el workaround (API compatible) antes de marcar Done
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Escribir `openfang.toml` v0.6.9 y `agents/bot_lili_taam/agent.toml`.
2. HAND.toml minimo para `hand install`.
3. Scripts `validar_openfang_config.sh` y `arrancar_dev.sh`.
4. README (OPENFANG_HOME, diagrama, sesiones, fallback Ollama).
5. `tests/test_openfang_config.py`.
6. Smoke: doctor, start, health :4200.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Esquema OpenFang 0.6.9 (validado con `openfang doctor`)

- Config versionada: `proyecto-3/openfang/openfang.toml`
- Runtime: copia/symlink a `{OPENFANG_HOME}/config.toml` (`OPENFANG_HOME=./openfang/data`)
- Secciones: `[default_model]`, `[memory]`, `[channels.telegram]` (no `[bridges.telegram]` ni `[[hands]]`)
- Agente: manifest `openfang/agents/bot_lili_taam/agent.toml` + `openfang agent spawn`
- Hand: `openfang hand install hands/taam_lili_hand` (HAND.toml minimo; ampliacion TASK-123)
- Sesiones: convencion `telegram:{chat_id}` documentada en README; verificacion en vivo TASK-120

```toml
api_listen = "127.0.0.1:4200"

[default_model]
provider = "openai"
model = "gpt-4o-mini"
api_key_env = "OPENAI_API_KEY"

[memory]
decay_rate = 0.05

[channels.telegram]
bot_token_env = "TELEGRAM_BOT_TOKEN"
default_agent = "bot_lili_taam"
allowed_users = []
```

```bash
cd proyecto-3
export PATH="$HOME/.openfang/bin:$PATH"
set -a && source .env && set +a
export OPENFANG_HOME="$(pwd)/openfang/data"
./scripts/validar_openfang_config.sh
openfang start
openfang agent spawn openfang/agents/bot_lili_taam/agent.toml
openfang hand install openfang/hands/taam_lili_hand
```
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Config OpenFang 0.6.9 activa en openfang/openfang.toml ([default_model] OpenAI, [memory], [channels.telegram] con default_agent bot_lili_taam). Agente en openfang/agents/bot_lili_taam/agent.toml; sync a OPENFANG_HOME/agents via validar_openfang_config.sh. HAND.toml minimo para hand install. Scripts arrancar_dev y validar; README con OPENFANG_HOME, diagrama, sesiones telegram:{chat_id}, fallback Ollama. Tests test_openfang_config.py (5). Smoke: doctor, start, GET /api/health :4200, doctor sin OPENAI_API_KEY reporta variable.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 TOML validado por arranque real o `openfang config validate` si existe
- [x] #2 Sin tokens en el archivo versionado
- [x] #3 Tarea **Done** sin archivar
<!-- DOD:END -->
