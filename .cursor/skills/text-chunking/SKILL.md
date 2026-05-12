---
name: text-chunking
description: Lee Markdown de data/markdown/, normaliza si hace falta y divide en chunks semanticos con metadatos. Usar despues de markdown-knowledge-base o al preparar knowledge_base.
---

# Limpieza y chunking

> Mantener el mismo contenido en `.cursor/skills/text-chunking/` y `.claude/skills/text-chunking/`.

## Fuente de entrada

- **Entrada principal**: archivos **Markdown** en **`data/markdown/`** (cada uno con front matter YAML segun skill `markdown-knowledge-base`).
- Si aun existen restos de HTML en el cuerpo del `.md`, limpiarlos antes de fragmentar (BeautifulSoup o reglas simples segun el caso).

## Limpieza (sobre Markdown)

- Colapsar lineas vacias excesivas; unificar saltos de linea.
- Conservar jerarquia de encabezados `#`, `##`, `###` como anclas semanticas.
- Propagar al chunk los metadatos del front matter (`source_url`, `titulo`, `seccion`, `fecha_extraccion`, `idioma`, `hash`) como campos por fragmento.

## Chunking

- Objetivo: fragmentos **coherentes** para el Q&A del modulo 1 (tamano por caracteres o por tokens aproximados, con **solapamiento** pequeno si mejora continuidad).
- Preferir cortes en **limites de encabezados Markdown** o bloques completos (listas, parrafos) antes que a mitad de frase.
- Evitar cortar en medio de una tabla critica si se puede partir por filas o secciones.

### Modulo 2 (Qdrant / LlamaIndex)

- El chunking **principal** para vectores puede vivir en el script de ingesta (`scripts/indexar_corpus_qdrant.py`) usando `SentenceSplitter` de LlamaIndex con `CHUNK_SIZE` / `CHUNK_OVERLAP` desde `.env`.
- Seguir propagando metadatos del front matter al **payload** de Qdrant (`titulo`, `source_url`, `archivo`, etc.) segun skill `markdown-knowledge-base` y esta skill.

## Metadatos por chunk

- Campos utiles: heredar del front matter y anadir `chunk_id`, `indice_chunk` (nombres ASCII en codigo).

## Salida

- Escribir artefactos en **`data/processed/`** (JSONL o similar) y documentar el esquema en espanol en README o `docs/`.
