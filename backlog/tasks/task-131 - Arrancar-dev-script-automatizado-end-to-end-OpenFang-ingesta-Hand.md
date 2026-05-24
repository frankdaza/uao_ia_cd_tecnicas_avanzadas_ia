---
id: TASK-131
title: Arrancar dev script automatizado end-to-end OpenFang ingesta Hand
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-24 16:55'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - config
milestone: m-1
dependencies:
  - TASK-121
  - TASK-122
  - TASK-123
references:
  - proyecto-3/scripts/arrancar_dev.sh
  - proyecto-3/scripts/instalar_openfang.sh
modified_files:
  - proyecto-3/scripts/arrancar_dev.sh
  - proyecto-3/README.md
  - proyecto-3/docs/guion-demo-ruta-b.md
  - proyecto-3/tests/test_arrancar_dev.py
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Unificar arranque local: validar `.env`, exportar `OPENFANG_HOME`, iniciar OpenFang, healthcheck `:4200`, ingesta corpus, activar Hand y ping opcional a Telegram. Reemplaza pasos manuales del README.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `./scripts/arrancar_dev.sh` completa sin error en entorno con claves válidas
- [x] #2 `trap` limpia proceso OpenFang al salir (SIGINT/SIGTERM)
- [x] #3 **Negativo:** `.env` ausente → mensaje y exit 1 antes de arrancar binario
- [x] #4 **Edge:** flag `--sin-telegram` omite ping al bot
- [x] #5 README referencia el script como flujo único de desarrollo
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Validar prerequisitos (`openfang`, `uv`, archivos).
2. `openfang start` en background; loop healthcheck curl.
3. `uv run python ingesta/indexar_corpus_openfang.py`.
4. `openfang hand activate taam_lili_hand`.
5. Documentar flags y logs.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Flujo: validar .env + OPENAI_API_KEY → validar_openfang_config → openfang start (si hace falta) + loop curl /api/health (30s) → sincronizar prompt → agent spawn → hand install → ingesta --permitir-db-en-vivo → hand activate → verificar_telegram_bot (salvo --sin-telegram).

trap limpiar INT TERM: openfang stop solo si INICIAMOS_DAEMON=1; en exito el daemon sigue corriendo.

Tests: uv run pytest tests/test_arrancar_dev.py -q

E2E manual (AC#1): ./scripts/arrancar_dev.sh y ./scripts/arrancar_dev.sh --sin-telegram con claves reales.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Script arrancar_dev.sh end-to-end: .env obligatorio, healthcheck /api/health, ingesta --permitir-db-en-vivo, hand activate, verificar Telegram opcional (--sin-telegram), trap INT/TERM solo si este script inicio el daemon. Tests pytest (falta .env, contrato estatico). README con flujo unico y guion demo actualizado.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Script ejecutable y probado
- [x] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
