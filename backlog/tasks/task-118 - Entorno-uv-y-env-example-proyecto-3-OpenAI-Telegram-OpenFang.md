---
id: TASK-118
title: 'Entorno uv y env example proyecto-3 OpenAI Telegram OpenFang'
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
references:
  - proyecto-3/pyproject.toml
  - proyecto-3/.env.example
  - proyecto-3/.python-version
  - backlog/decisions/decision-8 - Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
  - .cursor/rules/python-uv-environment.mdc
modified_files:
  - proyecto-3/pyproject.toml
  - proyecto-3/uv.lock
  - proyecto-3/.env.example
  - proyecto-3/src/configuracion.py
  - proyecto-3/src/__init__.py
priority: high
ordinal: 1180
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

`proyecto-3/` usa **Python 3.12.12** y **uv** para ingesta y pipeline t-SNE. Faltan `.env.example` completo y módulo `configuracion.py` con **pydantic-settings** para centralizar secretos y rutas (`OPENFANG_HOME`, modelos OpenAI, token Telegram).

## Objetivo

Entorno reproducible: `uv sync` limpio, variables documentadas sin valores reales, `Settings` importable desde scripts de ingesta y análisis.

## Entregables

| # | Artefacto | Criterio |
| --- | --- | --- |
| 1 | `.env.example` | Placeholders para todas las vars del ADR |
| 2 | `pyproject.toml` + `uv.lock` | Deps: `openai`, `tiktoken`, `pypdf`, `python-dotenv`, `pydantic-settings`, pandas, sklearn, etc. |
| 3 | `src/configuracion.py` | Clase `Settings` con validación y `model_config` desde `.env` |

**Skill:** `uv-python-env`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Desde `proyecto-3/`, `uv sync` completa sin error y `uv run python -c "from configuracion import Settings; print(Settings())"` carga defaults (sin `.env` real obligatorio si hay defaults seguros)
- [ ] #2 `.env.example` lista: `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL`, `TELEGRAM_BOT_TOKEN`, `OPENFANG_HOME`, `LOG_LEVEL`, `OLLAMA_BASE_URL`, `UAO_WORKSPACE_ROOT` — **sin valores secretos**
- [ ] #3 **Negativo:** si `OPENAI_API_KEY` está vacío y un script exige red, `Settings` o el caller lanza error legible (`ValidationError` o mensaje custom)
- [ ] #4 **Edge:** `OPENFANG_HOME` por defecto apunta a `proyecto-3/openfang/data` (relativo al proyecto) documentado en comentario del example
- [ ] #5 `python = "==3.12.12"` en `pyproject.toml` alineado con `.python-version`
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
```python
# proyecto-3/src/configuracion.py
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL"
    )
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    openfang_home: Path = Field(
        default=Path("openfang/data"), alias="OPENFANG_HOME"
    )
    uao_workspace_root: Path = Field(
        default=Path("../..").resolve(), alias="UAO_WORKSPACE_ROOT"
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434", alias="OLLAMA_BASE_URL"
    )
```

```bash
# Verificacion
cd proyecto-3 && uv sync && uv run python -c "from configuracion import Settings; s=Settings(); print(s.openfang_home)"
```
<!-- SECTION:NOTES:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 `uv.lock` versionado; sin `pip install` suelto
- [ ] #2 Ningún secreto real en commits
- [ ] #3 Identificadores Python ASCII; docstrings en español
- [ ] #4 Tarea **Done** sin archivar
<!-- DOD:END -->
