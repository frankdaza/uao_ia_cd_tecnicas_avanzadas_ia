
<!-- BACKLOG.MD MCP GUIDELINES START -->

<CRITICAL_INSTRUCTION>

## BACKLOG WORKFLOW INSTRUCTIONS

This project uses Backlog.md MCP for all task and project management activities.

**CRITICAL GUIDANCE**

- If your client supports MCP resources, read `backlog://workflow/overview` to understand when and how to use Backlog for this project.
- If your client only supports tools or the above request fails, call `backlog.get_backlog_instructions()` to load the tool-oriented overview. Use the `instruction` selector when you need `task-creation`, `task-execution`, or `task-finalization`.

- **First time working here?** Read the overview resource IMMEDIATELY to learn the workflow
- **Already familiar?** You should have the overview cached ("## Backlog.md Overview (MCP)")
- **When to read it**: BEFORE creating tasks, or when you're unsure whether to track work

These guides cover:
- Decision framework for when to create tasks
- Search-first workflow to avoid duplicates
- Links to detailed guides for task creation, execution, and finalization
- MCP tools reference

You MUST read the overview resource to understand the complete workflow. The information is NOT summarized here.

</CRITICAL_INSTRUCTION>

<!-- BACKLOG.MD MCP GUIDELINES END -->

**Convención (este repositorio):** al finalizar el trabajo de una tarea, el agente debe poner su estado en **Done** (p. ej. con `task_edit` del MCP) y **no** invocar `task_complete` ni archivar. El movimiento a `backlog/completed/` es **siempre manual** y solo con instrucción expresa de la persona. Ver la regla `.cursor/rules/backlog-workflow.mdc` y la skill `backlog-md`.

# Proyecto: técnicas avanzadas de IA (Módulos 1 y 2)

Además del flujo con **Backlog.md** (arriba), usa este contexto al implementar o revisar código en el repositorio. Un resumen paralelo para agentes está en **[CLAUDE.md](CLAUDE.md)** (útil cuando el cliente no carga reglas `.mdc` de Cursor).

## Entorno

- **Python 3.12.12** (versión exacta): `.python-version` y restricción equivalente en `pyproject.toml`.
- Dependencias y ejecución solo con **`uv`** (`uv sync`, `uv run`, `uv.lock` versionado). No usar `pip` suelto, Poetry ni Conda como fuente de verdad.

## Flujo de datos (base documental)

1. **`data/raw/`**: descargas en el formato nativo (HTML, JSON, XML, PDF, etc.); suele ignorarse en git por volumen.
2. **`data/markdown/`**: corpus textual canónico en **Markdown con front matter YAML** (generado desde `raw/`).
3. **`data/processed/`**: chunks (p. ej. JSONL) derivados de `markdown/` para Q&A.

Código sugerido M1: `src/scraping/` (descarga) → `src/markdown_export/` (conversión a `.md`) → `src/knowledge_base/` (chunking) → `src/qa/` → `src/api/` (FastAPI + SSE) → `frontend/` (React + Vite).

**Módulo 2 (agente):** `src/persistencia/` → `src/agentes/` (LangGraph + tools + memoria Postgres) → `src/rag/` (Qdrant denso) → `src/api/routers/sesiones.py` / `agente.py` → `frontend/` (`features/auth/`, chat con SSE extendido). Ingesta: `scripts/indexar_corpus_qdrant.py` desde `data/markdown/`. Decisiones: `backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md` (cuando exista); guía: `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md` (cuando exista).

## Stack (Módulo 1)

- Scraping: `requests`, `beautifulsoup4`, `selenium`.
- Markdown: **`markdownify`** (por defecto) o **`html2text`** (alternativa); **`pyyaml`** para front matter; **`pdfplumber`** opcional para PDF.
- Orquestación LLM: **LangChain** o **LlamaIndex** (una opción por equipo en la cadena simple M1).
- Modelo: **Ollama** (local) o **API** (p. ej. OpenAI).
- Backend HTTP: **FastAPI** + **Uvicorn** + **sse-starlette** en `src/api/` (puede exponer `PipelineQa` vía REST + SSE mientras exista en el árbol).
- Interfaz: **React 19** + **Vite 8** + **TypeScript 6** + **Tailwind v4** + **shadcn/ui** + **Vercel AI SDK** en `frontend/`.

## Stack (Módulo 2 — agente)

- Orquestación: **LangGraph** (router) + **LangChain** (tools, `langchain-postgres` memoria) + **LlamaIndex** (RAG denso **Qdrant**). OpenAI (u compatible) como camino típico del agente.
- Datos: **PostgreSQL** (usuarios + historial LangChain), **Qdrant** (vectores); **SQLAlchemy 2 async**, **Alembic**, `asyncpg`, `psycopg` según capa.
- API: `POST /api/sesiones`, `GET` historial, `POST /api/agente/stream` (SSE multi-evento). Ver skills **`agente-modulo-2`** y **`fastapi-sse-api`**.

## Idioma y código

- Documentación, comentarios, docstrings, UI y mensajes de commit en **español latinoamericano**.
- **Identificadores** (nombres de símbolos y archivos de código) en español con **ASCII puro** (sin `ñ` ni tildes en esos nombres). Las cadenas y la documentación pueden usar caracteres propios del español.

## Reglas de Cursor (`.cursor/rules/`)

| Archivo | Propósito |
| --- | --- |
| `language-conventions.mdc` | Idioma; identificadores ASCII en español (Python) / inglés (TS/JS) |
| `python-uv-environment.mdc` | Python 3.12.12 y `uv` |
| `project-stack.mdc` | Stack completo: scraping, LLM, M2 agente Qdrant, FastAPI, React+Vite+shadcn |
| `project-structure.mdc` | Carpetas `data/`, `src/`, `frontend/` y flujo M1/M2 |
| `agente-modulo-2.mdc` | Buenas prácticas M2: `src/agentes/`, `src/rag/`, `src/persistencia/`, ingesta Qdrant |
| `python-style.mdc` | Estilo en `**/*.py` |
| `scraping-ethics.mdc` | Ética de scraping en `src/scraping/**` |
| `frontend-style.mdc` | Estilo React+TS+Tailwind en `frontend/**` |
| `api-fastapi.mdc` | Patrones FastAPI+SSE en `src/api/**` |
| `backlog-workflow.mdc` | Cierre con Backlog MCP: `Done` sin archivar; `task_complete` solo si el usuario lo pide |
| `backlog-docs-format.mdc` | Naming `doc-<N>` y front matter YAML en `backlog/docs/**/*.md` (estilo Backlog.md upstream) |
| `cursor-ignore-files.mdc` | Ignores: secretos ampliados, `data/raw/`; corpus `data/markdown/` solo en indice; limites agente/MCP/terminal y backlog sin claves |

### Indexación e ignores (Cursor y Claude Code)

- **Cursor**: en la raíz del repo, [`.cursorignore`](.cursorignore) (exclusión fuerte para el agente, `@` y búsqueda semántica) y [`.cursorindexingignore`](.cursorindexingignore) (solo índice). Documentación: [Ignore file](https://cursor.com/docs/reference/ignore-file). La terminal y las herramientas MCP **no** quedan bloqueadas por `.cursorignore`.
- **Corpus**: el índice del IDE **no** es el mismo contexto que el runtime del backend: `data/markdown/` puede figurar en `.cursorindexingignore` para aligerar búsquedas en el editor; el backend puede seguir usando el corpus en disco para **ingesta** (M2 → Qdrant) o lectura directa en fases M1.
- **Claude Code**: no hay `.claudeignore` estándar en la raíz; lecturas sensibles compartidas vía [`.claude/settings.json`](.claude/settings.json) con `permissions.deny` y patrones `Read(/...)` (ver [sintaxis de permisos](https://code.claude.com/docs/en/permissions#permission-rule-syntax)). **No** incluir secretos en `backlog/tasks/` ni en comentarios. Referencia general: [Claude Code — configuración](https://code.claude.com/docs/en/configuration).

## Skills (`.cursor/skills/` y `.claude/skills/`)

Mismo contenido en ambas carpetas; al editar una skill, mantén la otra alineada.

| Skill | Uso |
| --- | --- |
| `uv-python-env` | Entorno `uv` y Python 3.12.12 |
| `web-scraping` | Descarga a `data/raw/` |
| `markdown-knowledge-base` | `raw/` → `data/markdown/` con front matter |
| `text-chunking` | `data/markdown/` → `data/processed/` |
| `qa-prompt-engineering` | Prompts y pruebas (≥20 preguntas) |
| `llm-backend` | M1 PipelineQa / Ollama-OpenAI; M2 resumen + delegación a `agente-modulo-2` |
| `agente-modulo-2` | Agente M2: LangGraph, LangChain tools/memoria, LlamaIndex+Qdrant, persistencia |
| `fastapi-sse-api` | Backend HTTP FastAPI + SSE en `src/api/` |
| `react-vite-qa-ui` | Interfaz React 19 + Vite 8 + shadcn/ui en `frontend/` |
| `gradio-qa-ui` | **DEPRECADO** — reemplazado por `react-vite-qa-ui`; código legacy en `src/app/legacy/` |
| `backlog-md` | Tareas Backlog: estado `Done` sin completar o archivar; archivo manual |
| `backlog-docs` | Documentacion en `backlog/docs/` (prefijo `doc-<N>` y YAML `id`/`title`/`type`/`created_date`) |
| `cursor-ignore-files` | Ignores, secretos, indice vs runtime (`data/markdown/`), alinear con `.claude/settings.json` |
