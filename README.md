# Técnicas avanzadas de IA — Módulo 1

## Descripción del proyecto

Interfaz de preguntas y respuestas sobre un corpus en Markdown derivado de sitios públicos, con recuperación textual y modelo de lenguaje local o por API. Este repositorio es el punto de partida del MVP; los módulos se irán completando en tareas posteriores.

## Requisitos

- Python **3.12.12** (versión exacta).
- [uv](https://docs.astral.sh/uv/) para dependencias y entornos virtuales.

## Instalación

```bash
uv python install 3.12.12
uv sync
```

Comprobar intérprete:

```bash
uv run python -V
```

## Scraping

*(Por implementar: descarga respetando `robots.txt` hacia `data/raw/`.)*

## Export a Markdown

*(Por implementar: conversión a `data/markdown/` con front matter YAML.)*

## App Gradio

*(Por implementar: interfaz web para probar el flujo de Q&A.)*

## Decisiones del MVP

- Recuperación **BM25 a nivel archivo completo** (sin chunking ni embeddings vectoriales en esta fase).
