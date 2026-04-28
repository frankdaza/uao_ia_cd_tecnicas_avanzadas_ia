
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

# Proyecto: técnicas avanzadas de IA (Módulo 1)

Además del flujo con **Backlog.md** (arriba), usa este contexto al implementar o revisar código en el repositorio. Un resumen paralelo para agentes está en **[CLAUDE.md](CLAUDE.md)** (útil cuando el cliente no carga reglas `.mdc` de Cursor).

## Entorno

- **Python 3.12.12** (versión exacta): `.python-version` y restricción equivalente en `pyproject.toml`.
- Dependencias y ejecución solo con **`uv`** (`uv sync`, `uv run`, `uv.lock` versionado). No usar `pip` suelto, Poetry ni Conda como fuente de verdad.

## Flujo de datos (base documental)

1. **`data/raw/`**: descargas en el formato nativo (HTML, JSON, XML, PDF, etc.); suele ignorarse en git por volumen.
2. **`data/markdown/`**: corpus textual canónico en **Markdown con front matter YAML** (generado desde `raw/`).
3. **`data/processed/`**: chunks (p. ej. JSONL) derivados de `markdown/` para Q&A.

Código sugerido: `src/scraping/` (descarga) → `src/markdown_export/` (conversión a `.md`) → `src/knowledge_base/` (chunking) → `src/qa/` → `src/app/` (Gradio).

## Stack (Módulo 1)

- Scraping: `requests`, `beautifulsoup4`, `selenium`.
- Markdown: **`markdownify`** (por defecto) o **`html2text`** (alternativa); **`pyyaml`** para front matter; **`pdfplumber`** opcional para PDF.
- Orquestación LLM: **LangChain** o **LlamaIndex** (una opción por equipo).
- Modelo: **Ollama** (local) o **API** (p. ej. OpenAI).
- Interfaz: **Gradio**.

## Idioma y código

- Documentación, comentarios, docstrings, UI y mensajes de commit en **español latinoamericano**.
- **Identificadores** (nombres de símbolos y archivos de código) en español con **ASCII puro** (sin `ñ` ni tildes en esos nombres). Las cadenas y la documentación pueden usar caracteres propios del español.

## Reglas de Cursor (`.cursor/rules/`)

| Archivo | Propósito |
| --- | --- |
| `language-conventions.mdc` | Idioma; identificadores ASCII en español |
| `python-uv-environment.mdc` | Python 3.12.12 y `uv` |
| `project-stack.mdc` | Dependencias y conversión a Markdown |
| `project-structure.mdc` | Carpetas `data/` y `src/` |
| `python-style.mdc` | Estilo en `**/*.py` |
| `scraping-ethics.mdc` | Ética de scraping en `src/scraping/**` |
| `backlog-workflow.mdc` | Cierre con Backlog MCP: `Done` sin archivar; `task_complete` solo si el usuario lo pide |
| `backlog-docs-format.mdc` | Naming `doc-<N>` y front matter YAML en `backlog/docs/**/*.md` (estilo Backlog.md upstream) |

## Skills (`.cursor/skills/` y `.claude/skills/`)

Mismo contenido en ambas carpetas; al editar una skill, mantén la otra alineada.

| Skill | Uso |
| --- | --- |
| `uv-python-env` | Entorno `uv` y Python 3.12.12 |
| `web-scraping` | Descarga a `data/raw/` |
| `markdown-knowledge-base` | `raw/` → `data/markdown/` con front matter |
| `text-chunking` | `data/markdown/` → `data/processed/` |
| `qa-prompt-engineering` | Prompts y pruebas (≥20 preguntas) |
| `llm-backend` | Ollama o API + framework LLM |
| `gradio-qa-ui` | Interfaz de prueba |
| `backlog-md` | Tareas Backlog: estado `Done` sin completar o archivar; archivo manual |
| `backlog-docs` | Documentacion en `backlog/docs/` (prefijo `doc-<N>` y YAML `id`/`title`/`type`/`created_date`) |
