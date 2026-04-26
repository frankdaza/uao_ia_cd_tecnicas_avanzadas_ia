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

Descarga el sitio permitido hacia `data/raw/valledellili-org/` (HTML y metad JSON) respetando `robots.txt`, con registro en `data/raw/_log.jsonl`.

Variables opcionales en `.env` (ver `.env.example`):

- `URL_BASE_SITIO`: URL semilla si no se pasa `--url-inicio`
- `USER_AGENT`: reemplaza el user-agent del modulo `robots` si no se pasa `--user-agent`

Comando (desde la raiz del repositorio):

```bash
uv run python -m scripts.scrape \
  --url-inicio https://valledellili.org/ \
  --max-paginas 200 \
  --delay 1.5 \
  --profundidad-maxima 5
```

Ayuda:

```bash
uv run python -m scripts.scrape --help
```

Una segunda ejecucion sin cambios en el sitio deberia incrementar `omitidas_por_hash` en el resumen (idempotencia). `Ctrl+C` termina con codigo 130 e imprime resumen parcial.

## Export a Markdown

*(Por implementar: conversión a `data/markdown/` con front matter YAML.)*

## App Gradio

*(Por implementar: interfaz web para probar el flujo de Q&A.)*

## Decisiones del MVP

- Recuperación **BM25 a nivel archivo completo** (sin chunking ni embeddings vectoriales en esta fase).
