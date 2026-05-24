---
id: TASK-131
title: Arrancar dev script automatizado end-to-end OpenFang ingesta Hand
status: In Progress
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-24 16:49'
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
- [ ] #1 `./scripts/arrancar_dev.sh` completa sin error en entorno con claves válidas
- [ ] #2 `trap` limpia proceso OpenFang al salir (SIGINT/SIGTERM)
- [ ] #3 **Negativo:** `.env` ausente → mensaje y exit 1 antes de arrancar binario
- [ ] #4 **Edge:** flag `--sin-telegram` omite ping al bot
- [ ] #5 README referencia el script como flujo único de desarrollo
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
```bash
#!/usr/bin/env bash
set -euo pipefail
trap 'kill ${OF_PID:-} 2>/dev/null || true' EXIT INT TERM

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
[[ -f .env ]] || { echo "Falta .env"; exit 1; }
set -a && source .env && set +a
export OPENFANG_HOME="${OPENFANG_HOME:-$ROOT/openfang/data}"

openfang start &
OF_PID=$!
for i in $(seq 1 30); do
  curl -fsS "http://127.0.0.1:4200/health" >/dev/null 2>&1 && break
  sleep 1
done

uv run python ingesta/indexar_corpus_openfang.py
openfang hand activate taam_lili_hand
echo "Listo. Dashboard: http://127.0.0.1:4200"
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Script ejecutable y probado
- [ ] #2 Tarea **Done** sin archivar
<!-- DOD:END -->
