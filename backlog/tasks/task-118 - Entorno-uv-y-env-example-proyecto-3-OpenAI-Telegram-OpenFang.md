---
id: TASK-118
title: Entorno uv y env example proyecto-3 OpenAI Telegram OpenFang
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
  - config
milestone: m-1
dependencies:
  - TASK-117
references:
  - proyecto-3/pyproject.toml
  - proyecto-3/.env.example
  - proyecto-3/.python-version
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
  - .cursor/rules/python-uv-environment.mdc
modified_files:
  - proyecto-3/pyproject.toml
  - proyecto-3/uv.lock
  - proyecto-3/.env.example
  - proyecto-3/README.md
  - proyecto-3/src/configuracion.py
  - proyecto-3/src/__init__.py
  - proyecto-3/tests/test_configuracion.py
  - proyecto-3/ingesta/indexar_corpus_openfang.py
priority: high
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

`proyecto-3/` usa **Python 3.12.12** y **uv** para ingesta y pipeline t-SNE. Faltan `.env.example` completo y módulo `configuracion.py` con **pydantic-settings** para centralizar secretos y rutas (`OPENFANG_HOME`, modelos OpenAI, token Telegram).

## Objetivo

Entorno reproducible: `uv sync` limpio, variables documentadas sin valores reales, `Configuracion` importable desde scripts de ingesta y análisis (`from src.configuracion import obtener_configuracion`).

## Entregables

| # | Artefacto | Criterio |
| --- | --- | --- |
| 1 | `.env.example` | Placeholders para todas las vars del ADR |
| 2 | `pyproject.toml` + `uv.lock` | Deps: `openai`, `tiktoken`, `pypdf`, `python-dotenv`, `pydantic-settings`, pandas, sklearn, etc. |
| 3 | `src/configuracion.py` | Clase `Configuracion` con validación y `model_config` desde `.env` |

**Skill:** `uv-python-env`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Desde `proyecto-3/`, `uv sync` completa sin error y `uv run python -c "from src.configuracion import obtener_configuracion; print(obtener_configuracion())"` carga defaults (sin `.env` real obligatorio si hay defaults seguros)
- [x] #2 `.env.example` lista: `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL`, `TELEGRAM_BOT_TOKEN`, `OPENFANG_HOME`, `LOG_LEVEL`, `OLLAMA_BASE_URL`, `UAO_WORKSPACE_ROOT` — **sin valores secretos**
- [x] #3 **Negativo:** si `OPENAI_API_KEY` está vacío y un script exige red, `Configuracion.exigir_openai_api_key()` lanza error legible (`ValueError` o `ValidationError`)
- [x] #4 `uv run pytest tests/test_configuracion.py` pasa (defaults, `openfang_home` absoluto, workspace, clave vacía)
- [x] #5 **Edge:** `OPENFANG_HOME` por defecto apunta a `proyecto-3/openfang/data` (relativo al proyecto) documentado en comentario del example
- [x] #6 `python = "==3.12.12"` en `pyproject.toml` alineado con `.python-version`
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Verificar `.python-version` = `3.12.12`.
2. `uv add openai tiktoken pypdf python-dotenv pydantic-settings pandas pyyaml scikit-learn umap-learn plotly jupyterlab pytest ruff`.
3. Crear paquete `src/` con `configuracion.py` y resolver `UAO_WORKSPACE_ROOT` (subir a raíz del repo si no está definido).
4. Redactar `.env.example` con comentarios en español.
5. `uv run pytest` (vacío o smoke) y `uv run ruff check src/`.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
`UAO_WORKSPACE_ROOT`: si no está en entorno, `raiz_workspace()` detecta el padre de `proyecto-3/` cuando existe `data/markdown/` (misma heurística que `proyecto-1/src/rutas_workspace.py`).

```bash
cd proyecto-3 && uv sync
uv run python -c "from src.configuracion import obtener_configuracion; c=obtener_configuracion(); print(c.openfang_home_absoluto())"
uv run pytest tests/test_configuracion.py -q
uv run ruff check src/ tests/
```
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Entorno uv reproducible en proyecto-3: pyproject.toml con build-backend uv_build, uv.lock versionado, deps openai/tiktoken/pypdf/pydantic-settings y dev pytest/ruff. Modulo src/configuracion.py (Configuracion, raiz_workspace, openfang_home_absoluto, exigir_openai_api_key). .env.example completo con LOG_LEVEL y OLLAMA_BASE_URL. Cuatro tests en tests/test_configuracion.py. Ingesta placeholder usa obtener_configuracion(). Verificado: uv sync, pytest, ruff check.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 `uv.lock` versionado; sin `pip install` suelto
- [x] #2 Ningún secreto real en commits
- [x] #3 Identificadores Python ASCII; docstrings en español
- [x] #4 Tarea **Done** sin archivar
<!-- DOD:END -->
