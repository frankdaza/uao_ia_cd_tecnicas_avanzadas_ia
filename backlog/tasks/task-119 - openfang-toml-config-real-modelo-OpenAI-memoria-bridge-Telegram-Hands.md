---
id: TASK-119
title: 'openfang.toml config real modelo OpenAI memoria bridge Telegram Hands'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
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
  - backlog/decisions/decision-8 - Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
  - backlog/docs/doc-007 - Evaluacion-OpenFang-Proyecto-2-TAAM.md
modified_files:
  - proyecto-3/openfang/openfang.toml
  - proyecto-3/README.md
priority: high
ordinal: 1190
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
- [ ] #1 Con `.env` cargado (OpenAI + Telegram placeholders o reales), `cd proyecto-3/openfang && openfang start` arranca sin error de configuración
- [ ] #2 Dashboard accesible en `http://127.0.0.1:4200` (o puerto documentado si difiere)
- [ ] #3 `session_id_format` o equivalente documentado para sesiones `telegram:{chat_id}`
- [ ] #4 **Negativo:** `api_key_env` apunta a `OPENAI_API_KEY`; si falta, el log indica variable no definida (no crash silencioso)
- [ ] #5 **Alterno:** si la versión pinneada no soporta OpenAI nativo, documentar en README el workaround (API compatible) antes de marcar Done
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Descomentar y completar `[agent]`, `[model]`, `[memory]`, `[bridges.telegram]`, `[[hands]]`.
2. Exportar `OPENFANG_HOME` al directorio de datos runtime (`openfang/data/` gitignored).
3. Smoke: `openfang start` + curl al dashboard.
4. Actualizar README con diagrama mínimo agente ↔ bridge ↔ hand.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
```toml
[agent]
name = "bot_lili_taam"
description = "Asistente postoperatorio Fundacion Valle del Lili"

[model]
provider = "openai"
model = "${OPENAI_MODEL}"
api_key_env = "OPENAI_API_KEY"

[memory]
data_dir = "${OPENFANG_HOME}"
vector_store_enabled = true
structured_kv_enabled = true
session_id_format = "telegram:{chat_id}"

[bridges.telegram]
enabled = true
bot_token_env = "TELEGRAM_BOT_TOKEN"

[[hands]]
name = "taam_lili_hand"
path = "hands/taam_lili_hand"
```

```bash
export OPENFANG_HOME="$(pwd)/openfang/data"
set -a && source ../.env && set +a
openfang start
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 TOML validado por arranque real o `openfang config validate` si existe
- [ ] #2 Sin tokens en el archivo versionado
- [ ] #3 Tarea **Done** sin archivar
<!-- DOD:END -->
