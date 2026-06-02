# Ingesta — corpus workspace → memoria OpenFang

Scripts auxiliares en Python para cargar el conocimiento corporativo en el **Vector Store** (tabla `memories` de SQLite) y **Structured KV** del agente OpenFang (requisito Ruta B, Modulo 3).

## Fuentes de datos

| Origen | Ruta workspace | Contenido |
| --- | --- | --- |
| Corpus Markdown M1/M2 | `data/markdown/` | Paginas institucionales con front matter YAML |
| Protocolos TAAM (PDF) | `data/taam/` | Recomendaciones postoperatorias por procedimiento |

Resolver la raiz del workspace con `UAO_WORKSPACE_ROOT` o subir dos niveles desde `proyecto-3/` hasta la raiz del repositorio.

## OpenFang 0.6.9 — como se escribe la memoria

| Tema | Detalle |
| --- | --- |
| API REST | Solo **KV** (`/api/memory/agents/{id}/kv/...`). No hay `POST` publico para fragmentos semanticos. |
| Vector Store | SQLite `{OPENFANG_HOME}/data/openfang.db`, tabla **`memories`**, `scope=semantic`, `source="Document"`. |
| Embeddings | OpenAI (`OPENAI_EMBEDDING_MODEL`), BLOB f32 little-endian; el script los inserta en ingesta. |
| Agente | `bot_lili_taam` — UUID via `OPENFANG_AGENT_ID` o `GET /api/status`. |
| Idempotencia | `source_id` estable (`markdown:...` / `taam-pdf:...`); segunda corrida omite si `content_hash` no cambia. |

Recomendacion: detener el daemon (`openfang stop`) antes de ingesta masiva, o usar `--permitir-db-en-vivo`.

## Uso

```bash
cd proyecto-3
uv sync

# Vista previa (sin OpenAI ni SQLite)
uv run python ingesta/indexar_corpus_openfang.py --dry-run --limite 5

# Solo corpus Markdown
uv run python ingesta/indexar_corpus_openfang.py --solo-markdown --limite 10

# Solo PDFs TAAM
uv run python ingesta/indexar_corpus_openfang.py --solo-taam-pdf

# Ingesta real (requiere OPENAI_API_KEY y agente registrado)
uv run python ingesta/indexar_corpus_openfang.py --permitir-db-en-vivo
```

Variables en `.env`: `OPENAI_API_KEY`, `OPENFANG_HOME`, `OPENFANG_API_URL`, `OPENFANG_AGENT_ID` (opcional).

## Verificacion rubrica

- Log sin errores criticos; resumen de chunks insertados/omitidos.
- Pregunta de prueba en Telegram sobre contenido del corpus (p. ej. cuidados FVL).
- Tras ingesta, KV `ingesta:resumen` en el agente (si el daemon responde).

## Referencias

- [decision-8](../../backlog/decisions/decision-8%20-%20Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md)
- [markdown-knowledge-base](../../.cursor/skills/markdown-knowledge-base/SKILL.md)
