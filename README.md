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

Convierte cada par ``.html`` + ``.json`` de ``data/raw/valledellili-org/`` en un ``.md`` con front matter YAML bajo ``data/markdown/valledellili-org/``. Si el ``hash`` del Markdown ya coincide con ``hash_sha256`` del sidecar, el archivo no se reescribe (idempotencia), salvo que se use ``--forzar``.

```bash
uv run python -m scripts.export_markdown
uv run python -m scripts.export_markdown --forzar
uv run python -m scripts.export_markdown --solo-uno atencion-al-paciente-especialidades
```

Ayuda:

```bash
uv run python -m scripts.export_markdown --help
```

Si aun no hay HTML en ``data/raw/valledellili-org/``, el comando termina con codigo 1 y un mensaje que indica ejecutar el scraping antes.

## App Gradio

Interfaz web (Gradio) para probar el flujo de Q&A: pregunta, elección de modelo (Ollama), prompt de sistema editable y trazabilidad (archivo fuente, URL, score BM25, latencia).

Requisito: Ollama en marcha y modelos usados en la app instalados localmente. Variables de entorno opcionales: `OLLAMA_BASE_URL`, `MODELO_LLM_DEFECTO` (ver `.env.example`).

```bash
uv run python -m src.app.app_gradio
```

Se abre la URL que imprime la consola (por defecto `http://127.0.0.1:7860/`).

## Evaluación por modelo (dataset ≥20)

El archivo `tests/qa/preguntas_evaluacion.yml` versiona un conjunto de al menos 20 preguntas (con `id`, `texto`, `categoría` y `archivo_esperado` opcional) alineado al corpus en `data/markdown/valledellili-org/`.

Con Ollama en marcha y los modelos instalados, genera un informe Markdown por modelo bajo `data/processed/evaluaciones/<slug-modelo>__YYYY-MM-DD.md` (el directorio mantiene un `.gitkeep`; los informes de corridas reales suelen quedar ignorados en git salvo excepciones puntuales).

```bash
uv run python -m scripts.evaluar_qa --modelos llama3.1:8b gemma4:e2b
```

Para depurar una sola pregunta:

```bash
uv run python -m scripts.evaluar_qa --modelos llama3.1:8b --solo-pregunta 1
```

Si un modelo no está instalado, el script notifica el error en consola, escribe un informe mínimo con el detalle y continúa con los demás. Opciones: `--dataset`, `--salida`, `--fecha`.

## Decisiones del MVP

- Recuperación **BM25 a nivel archivo completo** (sin chunking ni embeddings vectoriales en esta fase).
