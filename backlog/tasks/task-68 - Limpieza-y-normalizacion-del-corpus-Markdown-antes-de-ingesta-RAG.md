---
id: TASK-68
title: >-
  Limpieza y normalización del corpus Markdown
  (`data/processed/markdown_limpio/`) antes de la ingesta RAG: remoción de
  plantillas, exclusión de páginas hub y dedup intra-documento
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-14 16:30'
updated_date: '2026-05-14 22:15'
labels:
  - rag
  - qdrant
  - corpus
  - scripts
  - limpieza
  - modulo-2
dependencies: []
references:
  - data/markdown/valledellili-org/
  - scripts/indexar_corpus_qdrant.py
  - scripts/agrupar_corpus_markdown.py
  - config/agrupacion_corpus_valledellili.yaml
  - src/rag/recuperador_denso.py
  - scripts/limpiar_corpus_markdown.py
  - config/limpieza_corpus_valledellili.yaml
  - tests/scripts/test_limpiar_corpus_markdown.py
documentation:
  - .claude/skills/markdown-knowledge-base/SKILL.md
  - .claude/skills/text-chunking/SKILL.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
modified_files:
  - scripts/limpiar_corpus_markdown.py
  - config/limpieza_corpus_valledellili.yaml
  - tests/scripts/test_limpiar_corpus_markdown.py
  - scripts/README.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

### Problema

El RAG actual entrega resultados pobres en consultas frecuentes:

- "¿Cuál es la misión institucional de la Fundación?" → el agente responde "No tengo información suficiente" y el panel de fuentes RAG devuelve cinco chunks de páginas **no** institucionales (sedes, educación, buscador integral). El chunk con la misión real, presumiblemente en algún `la-fundacion-*.md`, **no llega** al top_k=5.
- "¿Cuántos pediatras hay?" → trae nombres parciales (problema de agregación, fuera del alcance de esta task; ver **TASK-70**).

La causa raíz cubierta aquí es **el ruido del corpus**: cada uno de los 987 archivos en `data/markdown/valledellili-org/` arrastra bloques de **chrome** y **plantilla repetida** (menú, redes sociales, "Otros especialistas", consentimiento de cookies, pie legal) que dominan el embedding y desplazan el contenido útil. Además, hay **93 páginas `buscador-integral-q-*`** que son resultados generados sin valor semántico propio y que duplican el bloque base.

### Objetivo

Implementar un pipeline de limpieza determinista y reproducible que produzca un corpus paralelo y limpio en `data/processed/markdown_limpio/valledellili-org/`, listo para ser consumido por `scripts/indexar_corpus_qdrant.py --markdown-dir data/processed/markdown_limpio/valledellili-org`.

- **Nuevo script**: `scripts/limpiar_corpus_markdown.py`.
- **Reglas externalizadas** en `config/limpieza_corpus_valledellili.yaml`:
  - `excluir_archivos`: patrones `fnmatch` (p. ej. `buscador-integral-q-*.md`).
  - `remover_bloques`: lista de patrones regex multilínea o marcadores delimitadores (`#### Otros especialistas` … hasta el siguiente `##` o EOF).
  - `remover_lineas`: regex por línea (redes sociales, "Volver al inicio", etc.).
  - `minimo_caracteres_utiles`: umbral debajo del cual el archivo se descarta como "no aporta".
- **Front matter preservado** intacto en cada `.md` de salida; sólo se modifica el cuerpo.
- **Idempotente**: si el archivo de salida ya existe y su `content_hash` coincide, no se reescribe.
- **Manifiesto** `_manifest_limpieza.json` en la raíz de salida con métricas (in/out, bytes removidos por regla, archivos excluidos, archivos vacíos resultantes).

### Alcance

- Salida derivada bajo `data/processed/markdown_limpio/valledellili-org/`. **No** sobrescribir `data/markdown/`.
- Esta task **reemplaza funcionalmente** el flujo `markdown_agrupado/` (TASK-67) como fuente recomendada para la ingesta. TASK-67 queda como contexto histórico; no se elimina ni se archiva.
- Pruebas con fixtures pequeños bajo `tests/scripts/`.

### Decisión sobre macro-agrupación (TASK-67)

La agrupación grosera por prefijo (consolidar todos los `directorio-medico-*` en un único `directorio-medico.md`) genera chunks con frontera arbitraria que **mezclan especialidades distintas** y disminuyen la relevancia marginal. **No** continuar por ese camino. La granularidad por archivo se mantiene; la mejora de calidad viene de: limpiar + chunking semántico (**TASK-69**) + payload enriquecido + recuperación adaptativa (**TASK-70**).

### Ejemplos concretos del problema (a documentar en `Implementation Notes` con líneas exactas)

1. **`directorio-medico-ana-maria-gomez-bedoya.md`** contiene tras el cuerpo útil un bloque tipo:

    ```markdown
    #### Otros especialistas

    [María Pérez](https://valledellili.org/directorio-medico/maria-perez/)
    [Juan García](https://valledellili.org/directorio-medico/juan-garcia/)
    ...
    ```

    Repetido (con variaciones) en ~539 fichas → el embedding tiende a captar "directorio de médicos" en lugar de la especialidad de la ficha. **Acción**: regla `remover_bloques` que match `^####\s+Otros especialistas\s*$` hasta el siguiente `^##\s` o EOF.

2. **`buscador-integral-q-afd291be.md`** (y otros 92): listados generados que duplican texto base y no aportan información única. **Acción**: `excluir_archivos: ["buscador-integral-q-*.md"]`.

3. Páginas con `<!-- bloque-redes -->` o variantes de menú lateral fijo ("Encuentra…", "Servicios para ti"). **Acción**: `remover_lineas` con regex que reconozca esos marcadores y bullets de navegación.

4. Archivos resultantes con < `minimo_caracteres_utiles` (p. ej. 200) tras la limpieza → descartar y reportar en manifiesto.

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [x] #1 Script ejecutable: `uv run python -m scripts.limpiar_corpus_markdown` con `--help` claro (`--config`, `--entrada`, `--salida`, `--limpiar-salida`, `--limit`, `-v`).
- [x] #2 Reglas declarativas en `config/limpieza_corpus_valledellili.yaml` con secciones `excluir_archivos`, `remover_bloques`, `remover_lineas`, `minimo_caracteres_utiles`, validadas con esquema mínimo (errores de YAML descriptivos como en `cargar_configuracion_grupos` de [`scripts/agrupar_corpus_markdown.py`](scripts/agrupar_corpus_markdown.py)).
- [x] #3 Front matter YAML del archivo fuente preservado **literal** en la salida; sólo cambia el cuerpo.
- [x] #4 Manifiesto `_manifest_limpieza.json` en la raíz de la salida con: `version`, `fecha_limpieza`, `entrada_posix`, `salida_posix`, `archivos_leidos`, `archivos_excluidos`, `archivos_descartados_por_minimo`, `archivos_escritos`, `bytes_removidos_por_regla` (map regla→bytes), `advertencias` (lista).
- [x] #5 Idempotencia: si el archivo de salida ya existe y su `content_hash` (sha256 del nuevo cuerpo limpio + front matter) coincide, no se reescribe; se contabiliza en `archivos_omitidos_sin_cambio`.
- [x] #6 Tests en `tests/scripts/test_limpiar_corpus_markdown.py` con ≥ 4 fixtures: (a) ficha de médico con bloque "Otros especialistas" → cuerpo limpio sin ese bloque; (b) `buscador-integral-q-*.md` → excluido; (c) archivo bajo `minimo_caracteres_utiles` tras limpieza → descartado y reportado; (d) ejecución idempotente (segunda corrida no reescribe).
- [x] #7 Documentación en `scripts/README.md`: comando completo + ejemplo de YAML + ejemplo de ejecución encadenada `limpiar_corpus_markdown` → `indexar_corpus_qdrant --markdown-dir data/processed/markdown_limpio/valledellili-org --collection corpus_fvl_v2`.
- [x] #8 Compatibilidad: el corpus de salida **debe** pasar la ingesta actual de [`scripts/indexar_corpus_qdrant.py`](scripts/indexar_corpus_qdrant.py) sin modificaciones (front matter parseable; `titulo`, `source_url`, `seccion` presentes).
- [x] #9 Smoke real documentado en `Final Summary` con conteos: `uv run python -m scripts.limpiar_corpus_markdown --limpiar-salida` sobre los 987 archivos reales; verificar que ≥ 80 % de archivos sobreviven (resto: 93 `buscador-integral-q-*` + descartados por umbral).

<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->

1. **Inventario** de bloques repetidos en el corpus:
   - `rg -n "^####\s+Otros especialistas" data/markdown/valledellili-org | wc -l`
   - Listar 5–10 marcadores recurrentes (menú lateral, redes, "Encuentra…", consentimiento de cookies, pie legal). Registrar regex exacta en un apartado del PR.
2. **Diseñar YAML** `config/limpieza_corpus_valledellili.yaml` con:
   - `version: 1`
   - `excluir_archivos: ["buscador-integral-q-*.md"]`
   - `remover_bloques: [{nombre, regex_inicio, regex_fin_opcional_o_hasta_proximo_h2}]`
   - `remover_lineas: [{nombre, regex}]`
   - `minimo_caracteres_utiles: 200`
3. **Implementar** `scripts/limpiar_corpus_markdown.py` reutilizando helpers de [`scripts/agrupar_corpus_markdown.py`](scripts/agrupar_corpus_markdown.py): `encontrar_raiz_repo`, `parsear_front_matter_yaml`, `_asegurar_limpiar_salida_segura` (cambiando el guard a `markdown_limpio`).
4. **Pipeline por archivo**: leer → parsear front matter → aplicar `excluir_archivos` → aplicar `remover_bloques` (regex multilínea) → aplicar `remover_lineas` (regex por línea) → comprobar `minimo_caracteres_utiles` → escribir si pasa los filtros.
5. **Tests** unitarios + de integración con fixtures mínimos (`tmp_path`) en `tests/scripts/test_limpiar_corpus_markdown.py`.
6. **Smoke** sobre corpus real con `EMBEDDING_PROVIDER=huggingface`, `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`, `EMBEDDING_DIMS=384`, `QDRANT_URL=:memory:` para validar end-to-end con `--collection corpus_fvl_limpio_smoke`.
7. **Documentar** en `scripts/README.md` y nota corta en `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md` (sección "Limpieza del corpus" antes de "Ingesta Qdrant").

<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

### Bloques de plantilla candidatos detectados (preliminar; confirmar antes de codificar)

- `#### Otros especialistas` → bloque tipo footer en fichas de médico. Regex: `^####\s+Otros especialistas\s*$` → consumir hasta `^##\s` o EOF.
- Lista de redes en cabecera (íconos enlazados a Facebook, Instagram, YouTube). Regex de línea: `^\[.*\]\(https://(www\.)?(facebook|instagram|youtube|twitter|x)\.com/.*\)\s*$`.
- Bloque "Encuentra…" en sedes (menú lateral). Regex: `^##\s+Encuentra\b` → consumir hasta próximo `^##`.
- Pie legal / consentimiento de cookies en muchas páginas. Regex de línea con marcadores específicos.

### Heurísticas

- **No** usar parser AST de Markdown completo (overkill). Trabajar línea a línea con `re.MULTILINE`, manteniendo bloques delimitados por niveles de heading.
- `re.compile(..., re.MULTILINE | re.IGNORECASE)` por regla; almacenar la compilada en memoria.

### Compatibilidad con la ingesta actual

- La ingesta ([`scripts/indexar_corpus_qdrant.py`](scripts/indexar_corpus_qdrant.py)) requiere front matter `---` con `titulo`, `source_url`, `seccion`. La limpieza preserva el front matter literal → cero cambios en `indexar_corpus_qdrant.py` para esta task.
- Recomendación: para el A/B, usar `--collection corpus_fvl_v2` para no contaminar la colección actual.

### Idempotencia

- Calcular `content_hash = sha256(front_matter_yaml + "\n---\n" + cuerpo_limpio)` y compararlo con el contenido existente en disco antes de escribir. Reusar patrón de `_recuperar_hashes_existentes` del indexador en espíritu.

### Riesgos

- Reglas regex demasiado agresivas podrían eliminar contenido útil (p. ej. una sección "Otros especialistas" que sí sea contenido único). Mitigación: empezar conservador, validar con golden set de TASK-72 antes/después.
- Front matter con caracteres especiales (tildes) preservado con `read_text(encoding="utf-8")` y `write_text(..., encoding="utf-8")`.

<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->

- [x] #1 Acceptance Criteria verificados en código, tests y documentación.
- [x] #2 `uv run pytest tests/scripts/test_limpiar_corpus_markdown.py` pasa en local.
- [x] #3 Smoke real reportado en `Final Summary` con conteos antes/después y al menos 5 ejemplos concretos de bloques removidos.
- [x] #4 `scripts/README.md` actualizado con el comando encadenado limpieza → ingesta → eval.
- [x] #5 `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md` actualizado con sección "Limpieza del corpus".
- [x] #6 Sin secretos en YAML ni en la tarea.
- [x] #7 Al cerrar, ajustar `status` a `Done` (no archivar; ver regla `backlog-workflow.mdc`).

<!-- DOD:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->

### Entregables

- Script: [`scripts/limpiar_corpus_markdown.py`](scripts/limpiar_corpus_markdown.py) (`uv run python -m scripts.limpiar_corpus_markdown`).
- Configuración: [`config/limpieza_corpus_valledellili.yaml`](config/limpieza_corpus_valledellili.yaml).
- Pruebas: [`tests/scripts/test_limpiar_corpus_markdown.py`](tests/scripts/test_limpiar_corpus_markdown.py) (7 tests).
- Documentación: [`scripts/README.md`](scripts/README.md) (sección **scripts.limpiar_corpus_markdown**), [`backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md`](backlog/docs/doc-003%20-%20Arquitectura-Agente-Modulo-2.md) (apartado **4.3 Limpieza del corpus**).

### Smoke sobre corpus real (`data/markdown/valledellili-org`)

Comando: `uv run python -m scripts.limpiar_corpus_markdown --limpiar-salida`.

| Métrica | Valor |
| --- | ---: |
| `archivos_leidos` | 987 |
| `archivos_excluidos` (`buscador-integral-q-*.md`) | 93 |
| `archivos_descartados_por_minimo` (umbral 200) | 20 |
| `archivos_escritos` | 874 |
| Sobreviven respecto al total (874 / 987) | **88,6 %** (≥ 80 % exigido) |
| Candidatos no excluidos (987 − 93) | 894; escritos + descartados = 874 + 20 |

Manifiesto: `data/processed/markdown_limpio/valledellili-org/_manifest_limpieza.json` (gitignored con `data/processed/**`).

### Cinco reglas con mayor impacto (bytes UTF-8 aproximados removidos del cuerpo)

1. **`navegacion_encuentra_hasta_titulo_principal`**: bloque `### Encuentra lo que necesitas…` + menú lateral hasta la línea del título principal `# …` (p. ej. en [`directorio-medico-fabian-sandoval-pereira.md`](../../data/markdown/valledellili-org/directorio-medico-fabian-sandoval-pereira.md) líneas 17–39 antes del `# Fabian Sandoval Pereira` en la línea 40).
2. **`otros_especialistas_hasta_siguiente_h2`**: encabezado `## Otros especialistas que te pueden interesar` (en el corpus real es `##`, no `####`; la regex usa `^#{1,6}\s+Otros especialistas`) hasta el siguiente `^##\s` o EOF — mismo archivo, a partir de la línea 67 aprox.
3. **`autorizacion_datos_hasta_eof`**: desde `### Autorización datos personales` hasta el final del archivo (texto legal repetido).
4. **`linea_tag_buscador_integral`**: líneas con enlaces `buscador-integral/?by_tag=…` (p. ej. líneas 56–59 del ejemplo de ficha).
5. **`redes_sociales_enlace_unico`** / **`linkedin_enlace_unico`** / **`spotify_open_enlace`**: líneas de enlaces a redes en cabecera (p. ej. líneas 10–15 del ejemplo).

### Ingesta sin cambios en el indexador

`QDRANT_URL=:memory: EMBEDDING_PROVIDER=huggingface EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2 EMBEDDING_DIMS=384 uv run python -m scripts.indexar_corpus_qdrant --markdown-dir data/processed/markdown_limpio/valledellili-org --glob "**/*.md" --collection corpus_fvl_limpio_smoke --limit 5` → 5 archivos, 8 chunks, 0 omitidos por YAML.

<!-- SECTION:FINAL_SUMMARY:END -->
