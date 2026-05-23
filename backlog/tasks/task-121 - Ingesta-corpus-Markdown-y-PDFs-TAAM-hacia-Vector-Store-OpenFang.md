---
id: TASK-121
title: Ingesta corpus Markdown y PDFs TAAM hacia Vector Store OpenFang
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-22 10:00'
updated_date: '2026-05-23 06:31'
labels:
  - modulo-3
  - taam
  - ruta-b
  - openfang
  - ingesta
milestone: m-1
dependencies:
  - TASK-119
references:
  - proyecto-3/ingesta/indexar_corpus_openfang.py
  - proyecto-3/ingesta/README.md
  - data/markdown/
  - data/taam/
  - >-
    backlog/decisions/decision-8 -
    Arquitectura-M3-TAAM-Proyecto-3-Ruta-B-OpenFang-Telegram-tSNE.md
modified_files:
  - proyecto-3/ingesta/indexar_corpus_openfang.py
  - proyecto-3/ingesta/README.md
  - proyecto-3/src/ingesta/
  - proyecto-3/src/configuracion.py
  - proyecto-3/tests/test_indexar_corpus_openfang.py
  - proyecto-3/.env.example
  - proyecto-3/openfang/openfang.toml
  - proyecto-3/pyproject.toml
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC1 parcial:** volcar conocimiento corporativo desde `data/markdown/` (workspace) y PDFs en `data/taam/` hacia el **Vector Store** y **Structured KV** de OpenFang. El script placeholder debe convertirse en CLI real con chunking, idempotencia y `--dry-run`.

**Skills:** `markdown-knowledge-base`, `text-chunking`, `uv-python-env`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `uv run python ingesta/indexar_corpus_openfang.py --dry-run` lista fuentes y cuenta de chunks sin escribir en OpenFang
- [x] #2 Ingesta real inserta chunks con `source_id` estable; segunda ejecución no duplica (idempotencia)
- [x] #3 Soporta flags `--solo-markdown`, `--solo-taam-pdf`, `--limite N`
- [x] #4 **Negativo:** directorio workspace vacío → exit code distinto de 0 y log `sin_fuentes`
- [x] #5 **Edge:** PDF sin texto extraíble se omite con warning, no aborta todo el lote
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Implementar lectura de front matter YAML en `.md` (`pyyaml`).
2. Extraer texto PDF con `pypdf`; normalizar whitespace.
3. Función `fragmentar(texto, tam=1000, solape=150)`.
4. Cliente inserción OpenFang (API/CLI según versión pinneada).
5. Tests unitarios con fixtures y mocks (sin red).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## OpenFang 0.6.9 (validado)

| Tema | Detalle |
| --- | --- |
| API REST | Solo KV (`GET/PUT /api/memory/agents/{id}/kv/...`); sin POST publico para fragmentos semanticos. |
| Vector Store | `{OPENFANG_HOME}/data/openfang.db`, tabla `memories`, `scope=semantic`, `source="Document"`. |
| Embeddings | OpenAI en ingesta Python; BLOB f32 LE (1536 dims con text-embedding-3-small). |
| Agente | `bot_lili_taam` via `OPENFANG_AGENT_ID` o `GET /api/status`. |
| Concurrencia | Preferir `openfang stop` o flag `--permitir-db-en-vivo`. |

Modulos: `proyecto-3/src/ingesta/`; CLI `ingesta/indexar_corpus_openfang.py`; tests `tests/test_indexar_corpus_openfang.py`.

```python
from pathlib import Path
from pypdf import PdfReader
import yaml

def fragmentar(texto: str, tam: int = 1000, solape: int = 150) -> list[str]:
    inicio, salida = 0, []
    while inicio < len(texto):
        fin = min(len(texto), inicio + tam)
        salida.append(texto[inicio:fin])
        if fin >= len(texto):
            break
        inicio = fin - solape
    return salida

def leer_markdown(ruta: Path) -> tuple[dict, str]:
    raw = ruta.read_text(encoding="utf-8")
    if raw.startswith("---"):
        _, fm, cuerpo = raw.split("---", 2)
        return yaml.safe_load(fm) or {}, cuerpo.strip()
    return {}, raw.strip()
```

```bash
uv run python ingesta/indexar_corpus_openfang.py --dry-run --limite 5
uv run python ingesta/indexar_corpus_openfang.py --solo-markdown
```
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Pipeline de ingesta Markdown + PDF TAAM hacia SQLite OpenFang (memories, scope semantic): paquete src/ingesta/, CLI con dry-run/solo-markdown/solo-taam-pdf/limite, idempotencia source_id+content_hash, embeddings OpenAI, KV ingesta:resumen. Tests 9 nuevos + ruff. Sin archivar.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 README ingesta actualizado
- [x] #2 Tests mocks pasan con `uv run pytest`
- [x] #3 Tarea **Done** sin archivar
<!-- DOD:END -->
