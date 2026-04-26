---
name: uv-python-env
description: Configura y mantiene el proyecto con Python 3.12.12 exacto y uv. Usar al iniciar el repo, al agregar dependencias o cuando falle el entorno.
---

# Entorno uv y Python 3.12.12

> Mantener el mismo contenido en `.cursor/skills/uv-python-env/` y `.claude/skills/uv-python-env/`.

## Requisitos

- Python **3.12.12** (exacto).
- Herramienta **uv** instalada en el sistema.

## Inicializacion (proyecto nuevo)

1. `uv init` en la raiz del repo (si aun no existe `pyproject.toml`).
2. Fijar en `pyproject.toml` la restriccion de Python `==3.12.12`.
3. Crear `.python-version` con una sola linea: `3.12.12`.
4. `uv python install 3.12.12`
5. `uv sync` y verificar con `uv run python -V` que muestra 3.12.12.

## Dependencias por area

- Scraping: `uv add requests beautifulsoup4 selenium`
- App: `uv add streamlit` o `uv add gradio`
- LLM: `uv add langchain` **o** `uv add llama-index` (uno solo, segun decision del equipo).
- API: `uv add openai` si aplica; Ollama suele ser servicio externo + cliente HTTP segun stack.

## Ejecucion

- Siempre preferir `uv run <comando>` para no depender de un `activate` manual.

## Problemas frecuentes

- Version incorrecta: borrar `.venv`, confirmar `.python-version`, `uv python install 3.12.12`, `uv sync`.
- Lock desincronizado: `uv lock` y commitear `uv.lock`.
