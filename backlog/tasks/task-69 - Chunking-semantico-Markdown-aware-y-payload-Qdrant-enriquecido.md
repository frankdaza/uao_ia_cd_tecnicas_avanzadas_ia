---
id: TASK-69
title: >-
  Chunking semántico Markdown-aware (LlamaIndex MarkdownNodeParser) y
  enriquecimiento del payload Qdrant con metadata estructurada
  (`tipo_pagina`, `especialidad`, `sedes`, `nombre_medico`, `headings_path`)
status: "To Do"
assignee:
  - Frank Daza
created_date: '2026-05-14 16:30'
labels:
  - rag
  - qdrant
  - chunking
  - llama-index
  - scripts
  - modulo-2
dependencies:
  - TASK-68
references:
  - scripts/indexar_corpus_qdrant.py
  - src/rag/qdrant_store.py
  - src/rag/embeddings.py
  - src/rag/recuperador_denso.py
  - src/api/configuracion.py
  - data/processed/markdown_limpio/valledellili-org/
documentation:
  - .claude/skills/text-chunking/SKILL.md
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
priority: high
ordinal: 220
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->

### Problema

`scripts/indexar_corpus_qdrant.py` usa hoy `SentenceSplitter(chunk_size=1024, chunk_overlap=128)`. Esto tiene dos defectos para nuestro corpus de Markdown estructurado:

1. **Corta sin respetar la estructura**. Las páginas de servicios y de educación tienen jerarquía clara (`# ... ## Enfermedades que trata ## Procedimientos`); SentenceSplitter mezcla en un mismo chunk encabezados distintos y baja la coherencia semántica.
2. **Payload mínimo** (`archivo`, `titulo`, `source_url`, `seccion`, `chunk_index`, `content_hash`, `texto`). Imposible filtrar por especialidad, sede o tipo de página. La consulta "lista de pediatras" no puede acotarse a fichas de médico ni a la especialidad Pediatría, lo que **TASK-70** requiere obligatoriamente.

Adicionalmente, [`src/api/configuracion.py`](src/api/configuracion.py) ya tiene un campo **reservado** `chunk_strategy` (literal `"sentence"`) que no afecta nada hoy. Esta task activa esa palanca.

### Objetivo

Migrar el chunking del corpus a `MarkdownNodeParser` de LlamaIndex (con post-split por tamaño máximo para evitar chunks gigantes en secciones largas) y enriquecer el payload Qdrant con metadata estructurada, manteniendo retro-compatibilidad detrás del flag `chunk_strategy`.

#### Nuevo payload propuesto

```jsonc
{
  // existentes
  "archivo": "data/processed/markdown_limpio/valledellili-org/directorio-medico-ana-maria-gomez-bedoya.md",
  "titulo": "Ana Maria Gomez Bedoya - Fundación Valle del Lili",
  "source_url": "https://valledellili.org/directorio-medico/ana-maria-gomez-bedoya/",
  "seccion": "directorio-medico",
  "chunk_index": 0,
  "content_hash": "...",
  "id_chunk": "...",
  "texto": "...",

  // nuevos (TASK-69)
  "tipo_pagina": "ficha_medico",          // {ficha_medico|servicio|sede|programa|institucional|educacion|evento|investigacion|revista|otro}
  "subtipo": null,                         // p. ej. "mision", "vision", "valores" cuando aplique
  "especialidad": ["Pediatria"],          // lista normalizada
  "sedes": ["Sede Alfaguara"],            // lista normalizada
  "nombre_medico": "Ana Maria Gomez Bedoya", // solo para ficha_medico
  "headings_path": "Pediatria > Formación", // ruta de encabezados del chunk
  "h1": "Ana Maria Gomez Bedoya",
  "h2": "Pediatria",
  "h3": "Formación",
  "tags": ["pediatria", "bienestar-infant"]  // del front matter o extraídos del cuerpo
}
```

### Alcance

- Modificar [`scripts/indexar_corpus_qdrant.py`](scripts/indexar_corpus_qdrant.py): nueva ruta de chunking cuando `cfg.chunk_strategy == "markdown"`.
- Nuevo módulo `src/rag/extractor_metadata.py` con funciones puras y testeables:
  - `inferir_tipo_pagina(seccion, nombre_archivo) -> str`
  - `extraer_nombre_medico(titulo, fm) -> str | None`
  - `extraer_especialidades(cuerpo, fm) -> list[str]`
  - `extraer_sedes(cuerpo, fm) -> list[str]`
  - `extraer_tags(fm, cuerpo) -> list[str]`
  - `construir_headings_path(nodo) -> str`
- Activar `chunk_strategy` en [`src/api/configuracion.py`](src/api/configuracion.py) con `Literal["sentence", "markdown"]` y describir en docstring.
- Crear índices de payload en Qdrant (`client.create_payload_index`) para los campos filtrables (`tipo_pagina`, `especialidad`, `sedes`, `seccion`) en `asegurar_coleccion` (compatible con servidor; en `:memory:` puede ser no-op).
- ADR corto (`decision-4` o nota en `decision-3`) si el payload nuevo se considera **breaking** para colecciones existentes.

### Ejemplos concretos de metadata esperada por tipo de página

| Archivo (tras limpieza, TASK-68) | `tipo_pagina` | `especialidad` | `sedes` | `nombre_medico` | `headings_path` (ej.) |
|---|---|---|---|---|---|
| `directorio-medico-ana-maria-gomez-bedoya.md` | `ficha_medico` | `["Pediatria"]` | `["Sede Alfaguara", "Sede Valle del Lili"]` | `"Ana Maria Gomez Bedoya"` | `Pediatria > Formación` |
| `servicios-gastroenterologia-pediatrica.md` | `servicio` | `["Gastroenterologia Pediatrica"]` | `[]` | `null` | `Enfermedades que trata > Tracto gastrointestinal` |
| `sedes-sede-alfaguara.md` | `sede` | `[]` | `["Sede Alfaguara"]` | `null` | `Servicios destacados > Alergología` |
| `la-fundacion-mision.md` (si existe) | `institucional` (`subtipo="mision"`) | `[]` | `[]` | `null` | `Misión` |
| `educacion-lactancia-materna.md` | `educacion` | `["Pediatria"]` (inferida) | `[]` | `null` | `¿Qué es la lactancia materna?` |

### Por qué importa para la calidad del RAG

- **Misión institucional**: el chunk con la misión, marcado `tipo_pagina="institucional"` y con `headings_path` significativo, puede recuperarse aun con baja similitud porque (a) tiene metadata propia y (b) **TASK-70** podrá filtrarlo blandamente cuando la consulta toque "misión", "visión", "valores".
- **Listado de pediatras**: con `tipo_pagina="ficha_medico"` y `especialidad=["Pediatria"]`, **TASK-70** podrá enumerar las 102 fichas mediante `scroll + filter`.
- **Headings preservados**: cada chunk lleva su contexto (`h1/h2/h3`), reduciendo ambigüedad y mejorando similitud frente a preguntas concretas ("¿qué procedimientos hace gastro pediátrica?").

<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->

- [ ] #1 `Configuracion.chunk_strategy: Literal["sentence", "markdown"]` activo en [`src/api/configuracion.py`](src/api/configuracion.py); cuando es `"markdown"`, el script usa `MarkdownNodeParser`. Cuando es `"sentence"`, comportamiento idéntico al actual (retro-compatible).
- [ ] #2 Implementado `MarkdownNodeParser` con post-split por tamaño máximo (p. ej. 1200 caracteres efectivos) para evitar chunks gigantes; tamaño objetivo y mínimo configurables vía `cfg.chunk_size`, `cfg.chunk_overlap`.
- [ ] #3 Nuevo módulo `src/rag/extractor_metadata.py` con las funciones listadas en *Description*, cada una con docstring y type hints; tests unitarios en `tests/rag/test_extractor_metadata.py` con ≥ 10 casos cubriendo: ficha de médico con varias sedes, servicio con `headings_path`, sede pura, archivo institucional (misión), archivo sin metadata extraíble (fallback a defaults).
- [ ] #4 Payload Qdrant extendido con todos los campos nuevos de la tabla en *Description*. Campos opcionales (`nombre_medico`, `subtipo`) admiten `null`.
- [ ] #5 Índices de payload creados en `asegurar_coleccion` para `tipo_pagina` (keyword), `especialidad` (keyword[]), `sedes` (keyword[]), `seccion` (keyword). Mensaje claro si el servidor no soporta `create_payload_index` (modo `:memory:`).
- [ ] #6 Tests de integración en `tests/scripts/test_indexar_corpus_qdrant_markdown.py` con Qdrant `:memory:` y fixtures: (a) ingesta de 3 archivos de tipos distintos, (b) verifica payload completo de un punto, (c) verifica idempotencia (segunda corrida no embedde de nuevo), (d) `chunk_strategy="sentence"` mantiene comportamiento anterior con los mismos fixtures.
- [ ] #7 Smoke real documentado: `EMBEDDING_PROVIDER=huggingface`, `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`, `EMBEDDING_DIMS=384`, `CHUNK_STRATEGY=markdown`, `uv run python -m scripts.indexar_corpus_qdrant --markdown-dir data/processed/markdown_limpio/valledellili-org --collection corpus_fvl_v2 --limit 50` produce conteos: archivos in, chunks producidos, distribución por `tipo_pagina` (impresa en el resumen final del script).
- [ ] #8 [`scripts/indexar_corpus_qdrant.py`](scripts/indexar_corpus_qdrant.py) imprime al final un **resumen por `tipo_pagina`** (cuántos chunks por categoría) además de los conteos existentes.
- [ ] #9 Documentación en [`scripts/README.md`](scripts/README.md) y `backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md` con: nuevo payload, comando `CHUNK_STRATEGY=markdown`, recomendación de **colección nueva** (`corpus_fvl_v2`) durante la migración para A/B sin downtime.
- [ ] #10 ADR `backlog/decisions/decision-4 - Payload-Qdrant-enriquecido-y-chunking-Markdown.md` corto que justifique el cambio y declare el impacto sobre colecciones existentes (recomienda recrear colección).

<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->

1. **Dependencias**: verificar que `llama-index-core` ya provee `MarkdownNodeParser`. Si hace falta paquete adicional, declarar con `uv add` y dejar nota en el PR.
2. **Configuración**: en [`src/api/configuracion.py`](src/api/configuracion.py), cambiar `chunk_strategy: str` a `chunk_strategy: Literal["sentence", "markdown"]` con validación; actualizar el docstring para indicar que `"markdown"` ya tiene efecto.
3. **Extractor de metadata** en `src/rag/extractor_metadata.py`:
   - Diccionario `_PREFIJO_A_TIPO_PAGINA` (mapea prefijos de nombre de archivo a `tipo_pagina`).
   - Regex compiladas para detectar `Pediatria`, `Sede X`, etc. en el cuerpo.
   - Helpers `_normalizar_especialidad`, `_normalizar_sede` que produzcan strings comparables.
4. **Integración** en [`scripts/indexar_corpus_qdrant.py`](scripts/indexar_corpus_qdrant.py):
   - Ramificar `construir_trabajos` según `cfg.chunk_strategy`.
   - Para `"markdown"`: usar `MarkdownNodeParser().get_nodes_from_documents([doc])`; para nodos cuyo `len(texto) > tope_max`, aplicar `SentenceSplitter` post-hoc.
   - Construir payload extendido a partir de fm + extractor + nodo (`headings_path`, `h1`, `h2`, `h3`).
5. **Índices de payload**: en `src/rag/qdrant_store.py::asegurar_coleccion`, tras crear/validar la colección, llamar a `client.create_payload_index(collection_name, field_name, field_schema=models.KeywordIndexParams())` para los campos requeridos; tolerar `UnexpectedResponse` del modo `:memory:` con warning.
6. **Tests** en `tests/rag/test_extractor_metadata.py` + `tests/scripts/test_indexar_corpus_qdrant_markdown.py`.
7. **Smoke + reporte por tipo_pagina** integrado en `_imprimir_resumen`.
8. **ADR** en `backlog/decisions/decision-4 - Payload-Qdrant-enriquecido-y-chunking-Markdown.md`.
9. **Doc-003** actualizado con sección "Chunking semántico y payload enriquecido".

<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->

### `headings_path` con LlamaIndex

`MarkdownNodeParser` rellena `node.metadata["Header_1"]`, `Header_2`, `Header_3` con el último encabezado de cada nivel visto. La función `construir_headings_path(nodo)` debe concatenar de mayor a menor nivel presente, ignorando los `None`:

```python
def construir_headings_path(nodo) -> str:
    niveles = []
    for k in ("Header_1", "Header_2", "Header_3"):
        v = nodo.metadata.get(k)
        if v:
            niveles.append(str(v).strip())
    return " > ".join(niveles)
```

### Tope de tamaño de chunk

Algunas páginas de servicios tienen secciones largas. Si `len(nodo.get_content()) > tope_max` (sugerido 4× `cfg.chunk_size` en caracteres como aprox.), aplicar `SentenceSplitter` sobre ese nodo y propagar la metadata original a los sub-nodos.

### Heurísticas de extracción (esperar iteración con golden set de TASK-72)

- **Especialidad** en `ficha_medico`: primer heading `H2` no vacío del cuerpo o primera línea no vacía de cuerpo si no hay H2; fallback a heurística por palabra clave en título.
- **Sedes** en `ficha_medico`: bullets bajo un H3 "Sedes" si existe; fallback: buscar substrings de un set conocido (`Sede Alfaguara`, `Sede Valle del Lili`, etc.).
- **Nombre médico**: del título antes de " - Fundación Valle del Lili" o del H1 del cuerpo.
- **Tags**: del front matter si el TASK-68 los preserva; fallback a links `?by_tag=` del cuerpo limpio.

### Compatibilidad con colección existente

- Qdrant **no permite cambiar el schema implícito** del payload, pero **sí** permite añadir campos nuevos (son keys del payload, no parte de `VectorParams`). Una colección antigua sin estos campos seguirá funcionando, pero **no podrá filtrar** por ellos hasta reindexar.
- **Recomendación**: usar `--collection corpus_fvl_v2` y mover el endpoint a la nueva colección sólo cuando TASK-72 valide mejora.

### Conexión con TASK-70 y TASK-71

- **TASK-70** depende de esta task: sin `tipo_pagina`, `especialidad`, `sedes` indexados, no hay filtros.
- **TASK-71** se beneficia de esta task: chunks con `headings_path` claros mejoran la calidad de reranking.

<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->

- [ ] #1 Acceptance Criteria verificados en código, tests y documentación.
- [ ] #2 `uv run pytest tests/rag/test_extractor_metadata.py tests/scripts/test_indexar_corpus_qdrant_markdown.py` pasa en local.
- [ ] #3 Smoke real reportado en `Final Summary` con: archivos in, chunks producidos, distribución por `tipo_pagina`, dimensión del vector y tiempo total.
- [ ] #4 ADR `decision-4` mergeado (o nota incorporada a `decision-3` si el equipo prefiere).
- [ ] #5 [`scripts/README.md`](scripts/README.md) actualizado con el flujo encadenado completo (TASK-68 → TASK-69 → ingesta).
- [ ] #6 Sin secretos en código, configuraciones ni en la tarea.
- [ ] #7 Al cerrar, ajustar `status` a `Done` (no archivar; ver regla `backlog-workflow.mdc`).

<!-- DOD:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->

<!-- SECTION:FINAL_SUMMARY:END -->
