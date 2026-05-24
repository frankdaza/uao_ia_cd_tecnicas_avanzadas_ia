---
id: TASK-127
title: Dashboard OpenFang historial sesiones y JSONL UC4 parcial consulta
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-24 16:36'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - docs
milestone: m-1
dependencies:
  - TASK-122
  - TASK-124
references:
  - proyecto-3/docs/dashboard-openfang.md
  - proyecto-3/openfang/openfang.toml
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
modified_files:
  - proyecto-3/docs/dashboard-openfang.md
  - proyecto-3/tests/test_dashboard_openfang_doc.py
  - proyecto-3/src/openfang/historial_jsonl.py
  - proyecto-3/src/openfang/__init__.py
  - proyecto-3/scripts/consultar_historial_sesion.py
  - proyecto-3/tests/openfang/test_historial_jsonl.py
  - proyecto-3/src/hand/recordatorio_postoperatorio.py
  - proyecto-3/README.md
  - proyecto-3/docs/guion-demo-ruta-b.md
  - proyecto-3/docs/checklist-pruebas-chat-fvl.md
priority: medium
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC4 parcial** y **UC9 parcial** ([decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md)): seguimiento de interacciones por **lectura** del dashboard OpenFang (`http://127.0.0.1:4200`) y archivos **JSONL** bajo `OPENFANG_HOME`. Sin panel React TAAM ni bandeja `alertas_triage` de Ruta A (`proyecto-2/`).

**Dependencias:** TASK-122 (tráfico chat / `openfang sessions`), TASK-124 (auditoría Hand recordatorio). TASK-125 recomendada (evidencia texto + JSONL episódico en `sessions/`).

**Fuera de alcance:** pipeline t-SNE → parquet (TASK-128), guardrails KV (TASK-126; solo enlace), panel staff React.

**Entregable:** [`proyecto-3/docs/dashboard-openfang.md`](../../proyecto-3/docs/dashboard-openfang.md) + contrato pytest + script `consultar_historial_sesion.py`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1a Doc describe acceso al dashboard (`http://127.0.0.1:4200`, coherente con `openfang.toml` y pytest `test_dashboard_puerto_4200`)
- [x] #1b Doc lista árbol de rutas bajo `OPENFANG_HOME` con `find … '*.jsonl'` y tabla `sessions/` vs `audit/` vs SQLite
- [x] #1c Ejemplos `jq` con `session_id` ficticio `telegram:900001` (fixture `openfang_sesion_ejemplo.jsonl`)
- [x] #2 Demo reproducible: mensaje Telegram o fixture → `openfang sessions --json` → línea en `audit/hand_*.jsonl` tras `disparar_*_hand.py`
- [x] #3 **Negativo:** `OPENFANG_HOME` inexistente → doc indica `mkdir`, `.env` y `arrancar_dev.sh`
- [x] #4 Sin PHI: ids enmascarados, extracto ficticio del fixture; sin tokens en doc
- [x] #5 Comandos `jq` por archivo `sessions/{chat_id}.jsonl` y variante si existe `logs/sessions.jsonl`
- [x] #6 `tests/test_dashboard_openfang_doc.py` verde; módulo `src/openfang/historial_jsonl.py` + script consulta con tests
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Generar tráfico (checklist TASK-122 o mensaje Telegram).
2. Inventariar rutas con `find` y `openfang sessions --json` (notas locales, sin PII en repo).
3. Redactar `docs/dashboard-openfang.md` y enlaces cruzados.
4. Extraer `historial_jsonl.py`, script `consultar_historial_sesion.py`, tests doc + openfang.
5. `uv run pytest`; marcar **Done** sin archivar.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Entregado:

- [`proyecto-3/docs/dashboard-openfang.md`](../../proyecto-3/docs/dashboard-openfang.md) — UC4, dashboard :4200, mapa JSONL, `jq`, demo Hand, troubleshooting.
- [`src/openfang/historial_jsonl.py`](../../proyecto-3/src/openfang/historial_jsonl.py) — lectura compartida; `recordatorio_postoperatorio` refactorizado.
- [`scripts/consultar_historial_sesion.py`](../../proyecto-3/scripts/consultar_historial_sesion.py) — alternativa CLI a `jq`.
- Tests: `tests/test_dashboard_openfang_doc.py`, `tests/openfang/test_historial_jsonl.py` (23 tests relacionados en corrida local).

Rutas documentadas (contrato pytest Hands):

- `{OPENFANG_HOME}/sessions/{chat_id}.jsonl`
- `{OPENFANG_HOME}/audit/hand_recordatorio.jsonl`, `hand_evidencia.jsonl`
- Opcional daemon: `{OPENFANG_HOME}/logs/sessions.jsonl`

```bash
uv run pytest tests/test_dashboard_openfang_doc.py tests/openfang/test_historial_jsonl.py -q
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Doc en español latinoamericano
- [x] #2 `uv run pytest tests/test_dashboard_openfang_doc.py tests/openfang/test_historial_jsonl.py -q` verde
- [x] #3 Tarea **Done** sin archivar
<!-- DOD:END -->
