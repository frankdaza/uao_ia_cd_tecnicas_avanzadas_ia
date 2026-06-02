---
name: codegraph-mcp
description: MCP CodeGraph (codegraph_*). Usar al explorar código por estructura o si falla task must be a non-empty string. Parámetros por tool; codegraph_context exige task, no query ni path.
---

# CodeGraph MCP

> Mantener el mismo contenido en `.cursor/skills/codegraph-mcp/` y `.claude/skills/codegraph-mcp/`.

**Fuente de verdad (Cursor, alwaysApply):** [`.cursor/rules/codegraph.mdc`](../../rules/codegraph.mdc)

Claude Code no carga `.mdc` automáticamente; leer la regla o esta skill antes de `CallMcpTool`.

## Parámetros que no se deben mezclar

| Parámetro | Solo en |
| --- | --- |
| **`task`** | `codegraph_context` (obligatorio, string no vacío) |
| **`query`** | `codegraph_search`, `codegraph_explore` |
| **`symbol`** | `codegraph_node`, `codegraph_callers`, `codegraph_callees`, `codegraph_impact` |
| **`from` / `to`** | `codegraph_trace` |
| **`path`** | `codegraph_files` (subdirectorio en el índice) |
| **`projectPath`** | Cualquier tool (opcional): **otro** repo indexado, no `proyecto-2/...` |

## Error habitual

`task must be a non-empty string` → se llamó `codegraph_context` con `query` y/o `path`. Corregir:

```json
{ "task": "Descripción de la tarea incluyendo proyecto-N si aplica" }
```

## Flujo breve

1. `codegraph_context` → `task`
2. `codegraph_explore` → `query` con nombres de símbolos
3. `codegraph_files` → `path` para árbol de carpetas

## Monorepo

Índice en la raíz del workspace. Acotar con `task` (“en proyecto-2…”) o `codegraph_files` + `path: "proyecto-2/frontend"`.

## Índice ausente

Si el servidor responde not initialized: preguntar si ejecutar `codegraph init -i` en la raíz del repo.
