---
id: TASK-2
title: 'Inicializar entorno uv, estructura src/ y archivos base del proyecto'
status: Done
assignee: []
created_date: '2026-04-26 20:11'
updated_date: '2026-05-01 01:22'
labels:
  - setup
dependencies:
  - TASK-1
references:
  - AGENTS.md
  - .cursor/rules/python-uv-environment.mdc
ordinal: 39
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Punto de partida del MVP: el repo aún no tiene `pyproject.toml`, `uv.lock`, ni la estructura de carpetas `src/`. Esta task deja el esqueleto listo para que las tasks siguientes solo agreguen módulos y dependencias específicas.

## Objetivo

Tener un entorno reproducible con Python **3.12.12** exacto, gestionado con `uv`, y la estructura de carpetas alineada con `project-structure.mdc`.

## Pasos clave

1. `uv init` en la raíz (si aún no hay `pyproject.toml`).
2. Fijar restricción de Python en `pyproject.toml`: `requires-python = "==3.12.12"` (o el campo equivalente en la tabla `[project]`).
3. Crear `.python-version` con una sola línea: `3.12.12`.
4. `uv python install 3.12.12` y `uv sync`.
5. Crear paquetes Python con `__init__.py` vacío:
   - `src/__init__.py`
   - `src/scraping/__init__.py`
   - `src/markdown_export/__init__.py`
   - `src/retrieval/__init__.py`
   - `src/qa/__init__.py`
   - `src/app/__init__.py`
   - `scripts/__init__.py`
   - `tests/__init__.py`
6. Crear `.env.example`:

   ```bash
   OLLAMA_BASE_URL=http://localhost:11434
   MODELO_LLM_DEFECTO=llama3.1:8b
   URL_BASE_SITIO=https://valledellili.org/
   ```
7. Actualizar `.gitignore` añadiendo (si no existen): `data/raw/`, `data/processed/`, `.env`, `.venv/`, `__pycache__/`.
8. Crear `README.md` esqueleto con secciones (se completarán en tareas posteriores):
   - Descripción del proyecto
   - Requisitos (Python 3.12.12 y uv)
   - Instalación (`uv sync`)
   - Scraping (placeholder)
   - Export a Markdown (placeholder)
   - App Gradio (placeholder)
   - Decisiones del MVP (BM25 a nivel archivo, sin chunking ni vectores)

## Notas

- No agregar dependencias funcionales todavía (las tasks específicas las agregan: scraping, markdown, retrieval, llm, ui).
- Sí dejar configurado `pyproject.toml` para que `[tool.hatch]`/`[build-system]` u otros sean coherentes con `uv` (por defecto que deja `uv init`).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 uv run python -V imprime exactamente 'Python 3.12.12'
- [x] #2 uv.lock existe y está versionado
- [x] #3 uv run python -c 'import src' no falla
- [x] #4 Existen __init__.py en src/, src/scraping/, src/markdown_export/, src/retrieval/, src/qa/, src/app/, scripts/, tests/
- [x] #5 .python-version contiene exactamente '3.12.12'
- [x] #6 pyproject.toml restringe Python a ==3.12.12
- [x] #7 .env.example existe con las 3 variables (OLLAMA_BASE_URL, MODELO_LLM_DEFECTO, URL_BASE_SITIO) y .env está en .gitignore
- [x] #8 README.md existe con las secciones esqueleto definidas
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) uv init en la raíz
2) Editar pyproject.toml para fijar requires-python==3.12.12
3) Crear .python-version con 3.12.12
4) uv python install 3.12.12 y uv sync
5) Crear estructura src/ y scripts/ con __init__.py
6) Crear .env.example y actualizar .gitignore
7) Escribir README.md esqueleto en español latinoamericano
8) Ejecutar uv run python -V y uv run python -c \"import src\" para validar
<!-- SECTION:PLAN:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 uv run pytest -q corre sin errores aunque no haya tests aún
- [x] #2 git status limpio luego de commitear
<!-- DOD:END -->
