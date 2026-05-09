---
name: backlog-md
description: Tareas y Backlog.md MCP. Usar al crear, actualizar o cerrar tareas en backlog/tasks.
---

# Backlog.md en este repositorio

> Mantener el mismo contenido en `.cursor/skills/backlog-md/` y `.claude/skills/backlog-md/`.

## Cierre al terminar una tarea

1. Dejar el archivo en `backlog/tasks/` (no mover a `backlog/completed/`).
2. Ajustar el **status** a **Done** (p. ej. herramienta `task_edit` del MCP: `status: Done`).
3. Rellenar criterios, Definition of Done, notas o `finalSummary` segun toque.
4. **Prohibido** invocar `task_complete` o cualquier accion que archieve la tarea de forma **automatica**. El archivado es **manual** y solo si la persona pide de forma **explicita** mover o “completar” en el sentido de sacar de `backlog/tasks/`.

## Regla vinculada

Ver detalle en **`.cursor/rules/backlog-workflow.mdc`**.

## Documentacion en `backlog/docs/`

Las guías y referencias en **`backlog/docs/`** (no las tareas de `backlog/tasks/`) siguen naming `doc-<N> - Titulo-Slug.md` y front matter con `id`, `title`, `type`, `created_date`. Ver la skill **`backlog-docs`** y la regla **`.cursor/rules/backlog-docs-format.mdc`**.

## Referencia

- Resumen alineado en `AGENTS.md` (despues del bloque de Backlog.md MCP) y en `CLAUDE.md` (sección *Gestión de tareas*).
