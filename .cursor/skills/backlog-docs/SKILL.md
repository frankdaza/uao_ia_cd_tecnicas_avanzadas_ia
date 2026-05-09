---
name: backlog-docs
description: >-
  Formato nombre de archivo y front matter YAML para documentacion en backlog/docs
  (estilo Backlog.md upstream: doc-001 - Slug.md).
---

# Documentacion en `backlog/docs/`

> Mantener el mismo contenido en `.cursor/skills/backlog-docs/` y `.claude/skills/backlog-docs/`.

Usar esta skill al **crear o migrar** guias, referencias o documentos de arquitectura bajo `backlog/docs/` (no aplica de forma estricta a PDFs u otros binarios en subcarpetas como `actividades/`).

## Cuando aplicar

- Se va a añadir un nuevo `.md` de documentacion de proyecto en `backlog/docs/`.
- Se renombra o estandariza un documento existente para alinearlo con Backlog.md.

## Formato de archivo (upstream)

Referencia oficial: [doc-001 - Testing Style Guide](https://github.com/MrLesk/Backlog.md/blob/main/backlog/docs/doc-001%20-%20Testing-Style-Guide.md?plain=1) en el repositorio MrLesk/Backlog.md.

## Nombre del archivo

```text
doc-<N> - <Titulo-Slug-Title-Case-ASCII>.md
```

- `doc-<N>` alineado con el campo `id` del front matter (`doc-001`, `doc-002`, ...).
- Slug en **ASCII** (sin tildes ni ene en el nombre), palabras separadas por guion, estilo Title-Case por palabra.
- Separador literal ` - ` (espacio-guion-espacio) entre el prefijo y el slug.

## Front matter obligatorio

```yaml
---
id: doc-001
title: Titulo legible del documento
type: guide
created_date: 'YYYY-MM-DD'
---
```

- **Campos requeridos**: `id`, `title`, `type`, `created_date` (fecha ISO entre comillas simples).
- **`type`**: una etiqueta corta; valores habituales en este repo: `guide`, `reference`, `architecture`, `tutorial`, `policy`.
- **Opcional**: `updated_date`, `status`, `modulo`, u otras claves de metadatos del equipo; nombres de clave en ASCII.

Tras el segundo `---`, una linea en blanco y el cuerpo del documento en Markdown. El cuerpo y los titulos pueden estar en **español latinoamericano** segun convenciones del repositorio.

## Numeracion

1. Buscar en `backlog/docs/` los archivos `doc-* - *.md` existentes.
2. Asignar el siguiente entero **N** sin colision.
3. Si solo hay material legacy sin prefijo `doc-`, numerar a partir de `001` o continuar la serie existente.

## Regla vinculada

Detalle y checklist: **`.cursor/rules/backlog-docs-format.mdc`**.

## Relacion con otras piezas

- **Tareas** Backlog (`backlog/tasks/`): skill `backlog-md`.
- **Decisiones / ADR** (`backlog/decisions/`): skill `backlog-decisions` y regla `backlog-decisions-format.mdc`.
- **Contenido del corpus** (`data/markdown/`): skill `markdown-knowledge-base` (otro esquema de front matter).
