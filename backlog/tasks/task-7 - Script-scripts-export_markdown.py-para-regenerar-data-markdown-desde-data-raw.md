---
id: TASK-7
title: >-
  Script scripts/export_markdown.py para regenerar data/markdown/ desde
  data/raw/
status: To Do
assignee: []
created_date: '2026-04-26 20:13'
labels:
  - markdown
  - setup
dependencies:
  - TASK-6
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Necesitamos un comando reproducible que tome todos los `.html` de `data/raw/valledellili-org/` y produzca/actualice los `.md` en `data/markdown/valledellili-org/`. Debe ser idempotente para no reescribir archivos cuyo hash no haya cambiado.

## Objetivo

Crear `scripts/export_markdown.py` que orqueste la conversión de toda la base documental de un único disparo.

## Comando esperado

```bash
uv run python -m scripts.export_markdown
uv run python -m scripts.export_markdown --forzar       # reescribe todo
uv run python -m scripts.export_markdown --solo-uno <slug>  # debug
```

## Funcionalidad

1. Recorrer `data/raw/valledellili-org/*.html` (excluyendo `_log.jsonl`).
2. Para cada `.html`:
   - Cargar el sidecar `.json` correspondiente.
   - Si existe `data/markdown/valledellili-org/<slug>.md` y `front_matter.hash == sidecar.hash_sha256` y NO se pasó `--forzar`, **omitir**.
   - En caso contrario: llamar `convertir_html_a_md` y `escribir_markdown`.
3. Imprimir resumen:

   ```text
   Resumen:
     creados: A
     actualizados: B
     omitidos_por_hash: C
     errores: D
   ```

## Manejo de errores

- Si la conversión falla para un archivo concreto, registrar en stderr y continuar con los demás (no abortar todo el proceso). Acumular errores en el resumen.
- Si `data/raw/valledellili-org/` está vacío, salir con código 1 y mensaje `"No hay HTML descargado; corre scripts.scrape primero"`.

## Identificadores ASCII

- `parsear_argumentos`, `exportar_todo`, `procesar_archivo`, `imprimir_resumen`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 uv run python -m scripts.export_markdown --help muestra --forzar y --solo-uno
- [ ] #2 Primera ejecución sobre data/raw/ con N archivos genera N .md en data/markdown/valledellili-org/ y reporta creados=N
- [ ] #3 Segunda ejecución sin cambios reporta omitidos_por_hash=N y creados=0, actualizados=0
- [ ] #4 Con --forzar todos los .md son reescritos aunque el hash coincida
- [ ] #5 Si un .html falla en la conversión, los demás se procesan y el error se reporta en el resumen
- [ ] #6 Si no hay archivos en data/raw/, el script sale con código 1 y mensaje informativo
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1) Crear scripts/export_markdown.py con argparse
2) Listar HTMLs y procesarlos uno a uno
3) Comparar hash del .md existente (parsear front matter) vs sidecar
4) Llamar convertir_html_a_md y escribir_markdown solo cuando corresponda
5) Capturar excepciones por archivo y acumular para el resumen
6) Smoke test con datos de prueba
7) Documentar en README
<!-- SECTION:PLAN:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [ ] #1 Comando documentado en README sección 'Export a Markdown'
- [ ] #2 scripts/export_markdown.py es ejecutable con 'uv run python -m scripts.export_markdown'
- [ ] #3 Idempotencia validada manualmente con dos corridas consecutivas
<!-- DOD:END -->
