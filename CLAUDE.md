# Proyecto: Técnicas avanzadas de IA (Módulo 1)

## Gestión de tareas

Lee y sigue **[AGENTS.md](AGENTS.md)** para el flujo con **Backlog.md** (MCP): cuándo crear, ejecutar y cerrar tareas. **No** archivar tareas (no usar `task_complete` del MCP) salvo que el **usuario** lo pida: al terminar, dejar la tarea en `backlog/tasks/` con `status: Done` (ver `.cursor/rules/backlog-workflow.mdc` y la skill `backlog-md`).

## Entorno

- **Python 3.12.12** (versión exacta). Archivo `.python-version` y restricción equivalente en `pyproject.toml`.
- Dependencias y ejecución solo con **`uv`** (`uv sync`, `uv run`, `uv.lock` versionado). No usar `pip` suelto, Poetry ni Conda como fuente de verdad.

## Stack (actividad Módulo 1)

- Scraping: `requests`, `beautifulsoup4`, `selenium`.
- Base documental: artefactos crudos en **`data/raw/`**; corpus textual canónico en **`data/markdown/`** (Markdown con front matter YAML). Conversión HTML→Markdown con **`markdownify`** (por defecto) o **`html2text`** (alternativa); **`pyyaml`** para el front matter; **`pdfplumber`** opcional si hay PDF.
- Orquestación LLM: **LangChain** *o* **LlamaIndex** (una opción por equipo).
- Modelo: **Ollama** (local) *o* **API** (p. ej. OpenAI).
- Backend HTTP: **FastAPI** + **Uvicorn** + **sse-starlette** en `src/api/` (expone `PipelineQa` vía REST + SSE).
- Interfaz: **React 19** + **Vite 7** + **TypeScript** + **Tailwind v4** + **shadcn/ui** + **Vercel AI SDK** en `frontend/`.

## Idioma

- Documentación, comentarios, docstrings, mensajes de UI y commits en **español latinoamericano**.
- **Identificadores de código** (nombres de símbolos y archivos de código) en español con **ASCII puro**: sin `ñ` ni tildes en esos nombres. Las cadenas y la documentación sí pueden usar caracteres propios del español.

## Skills del repositorio

Instrucciones reutilizables en **`.claude/skills/`** (espejo de `.cursor/skills/`). Mantén ambas carpetas alineadas al editar una skill. Para crear guías bajo **`backlog/docs/`**, usar la skill **`backlog-docs`** (`doc-<N>` y front matter al estilo [Backlog.md upstream](https://github.com/MrLesk/Backlog.md/blob/main/backlog/docs/doc-001%20-%20Testing-Style-Guide.md?plain=1)).

| Skill | Uso |
| --- | --- |
| `uv-python-env` | Entorno `uv` y Python 3.12.12 |
| `web-scraping` | Descarga a `data/raw/` |
| `markdown-knowledge-base` | `raw/` → `data/markdown/` con front matter |
| `text-chunking` | `data/markdown/` → `data/processed/` |
| `qa-prompt-engineering` | Prompts y pruebas (≥20 preguntas) |
| `llm-backend` | Ollama o API + framework LLM + exposición vía SSE |
| `fastapi-sse-api` | Backend HTTP FastAPI + SSE en `src/api/` |
| `react-vite-qa-ui` | Interfaz React 19 + Vite 7 + shadcn/ui en `frontend/` |
| `gradio-qa-ui` | **DEPRECADO** — reemplazado por `react-vite-qa-ui` |
| `backlog-md` | Tareas Backlog: estado `Done` sin completar o archivar; archivo manual |
| `backlog-docs` | Documentación en `backlog/docs/` |
| `cursor-ignore-files` | Ignores, secretos, índice vs runtime (`data/markdown/`), alinear con `.claude/settings.json` |

## Reglas de Cursor

Convenciones adicionales en **`.cursor/rules/`** (archivos `.mdc`). Claude Code no las carga automáticamente; este archivo resume lo esencial. La regla **`backlog-docs-format.mdc`** aplica cuando se editan **`backlog/docs/**/*.md`** (naming y YAML de documentación del proyecto). La regla **`cursor-ignore-files.mdc`** describe `.cursorignore`, `.cursorindexingignore` y el alcance frente a Claude Code.

## Indexación, ignores y Claude Code

- En Cursor, [`.cursorignore`](.cursorignore) y [`.cursorindexingignore`](.cursorindexingignore) (ver [Ignore file](https://cursor.com/docs/reference/ignore-file)): secretos ampliados, `data/raw/`, `data/markdown/` solo fuera del **índice** del IDE (el backend sigue leyendo el corpus en disco), `!uv.lock` cuando aplica la lista por defecto.
- **Importante**: la terminal y MCP **no** respetan `.cursorignore`; no volcar claves en `backlog/` ni en el código.
- En **Claude Code**, [`.claude/settings.json`](.claude/settings.json) define `permissions.deny` con `Read(/...)` en sintaxis de proyecto (ver [permisos](https://code.claude.com/docs/en/permissions#permission-rule-syntax)). No sustituye buenas prácticas: variables locales y sin secretos en tareas. Documentación general: [Claude Code — configuración](https://code.claude.com/docs/en/configuration).
