---
id: TASK-17
title: Documentar fase 1 MVP scraping markdown bm25
status: Done
assignee: []
created_date: '2026-04-28 02:33'
updated_date: '2026-04-28 04:00'
labels:
  - documentacion
  - fase-1
  - mvp
dependencies: []
references:
  - README.md
  - backlog/decisions/decision-1 - MVP-BM25-Archivo-Completo.md
  - src/scraping/robots.py
  - src/scraping/descarga.py
  - src/markdown_export/conversion.py
  - src/retrieval/recuperador.py
  - scripts/scrape.py
  - scripts/export_markdown.py
  - .env.example
  - backlog/docs/doc-001 - MVP-Fase-1-Proyecto-Final-QA-BM25.md
  - .cursor/rules/backlog-docs-format.mdc
ordinal: 24
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Redactar `backlog/docs/doc-001 - MVP-Fase-1-Proyecto-Final-QA-BM25.md` (formato backlog docs según upstream Backlog.md: `doc-<N>` y YAML `id`/`title`/`type`/`created_date`), una guia detallada de la fase 1 del proyecto final del Modulo 1 (Tecnicas avanzadas de IA). El documento debe servir como onboarding para alguien sin contexto previo: explica el problema, el alcance del MVP, el pipeline completo (`scraping -> data/raw/ -> data/markdown/ -> BM25 -> Ollama -> Gradio`), y por que esta fase NO incluye chunking, embeddings ni base de datos vectorial.

Debe basarse en la documentacion y codigo existentes:
- `README.md` (descripcion, comandos, limitaciones, roadmap).
- `backlog/decisions/decision-1 - MVP-BM25-Archivo-Completo.md` (ADR de la decision arquitectonica).
- `src/scraping/robots.py` y `src/scraping/descarga.py` (crawler BFS, robots.txt, idempotencia por hash, slug ASCII, reintentos, filtros).
- `src/markdown_export/conversion.py` (limpieza HTML, `markdownify` ATX, front matter YAML).
- `src/retrieval/recuperador.py` (BM25 a nivel archivo con `rank-bm25`, tokenizador con stopwords ES, seleccion top-1).
- Skills `web-scraping`, `markdown-knowledge-base`, `qa-prompt-engineering`, `llm-backend` y reglas `.cursor/rules/*.mdc`; para naming en `backlog/docs/`: skill `backlog-docs` y regla `backlog-docs-format.mdc`.

## Plan

1. Releer `README.md`, ADR-0001 y los modulos `src/scraping/`, `src/markdown_export/`, `src/retrieval/`.
2. Crear el documento bajo `backlog/docs/` con prefijo `doc-001 - ...`, front matter canonico y secciones: resumen ejecutivo, decisiones de diseno, arquitectura (diagrama Mermaid), scraping en detalle, que se descarga / que no, conversion a Markdown, recuperacion BM25 sin vectores, inyeccion en el prompt, comandos y `.env`, limitaciones y roadmap Modulo 2.
3. Verificar cada criterio de aceptacion contra el documento.
4. Marcar criterios y dejar la tarea con `status: Done` (sin archivar; regla `backlog-workflow.mdc`).

## Fuera de alcance

- No se modifica codigo en `src/` ni `scripts/`.
- No se cubre Modulo 2 mas alla de un breve roadmap.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 El documento `backlog/docs/doc-001 - MVP-Fase-1-Proyecto-Final-QA-BM25.md` existe (id `doc-001` en front matter), esta en espanol latinoamericano y describe el problema, el alcance del MVP y por que esta fase no incluye chunking ni base vectorial, citando ADR-0001.
- [x] #2 Incluye un diagrama Mermaid del pipeline completo `valledellili.org -> data/raw/ -> data/markdown/ -> RecuperadorBm25 -> src/qa -> Ollama -> Gradio`.
- [x] #3 Detalla el scraping citando `src/scraping/robots.py` y `src/scraping/descarga.py`: `GestorRobots` con modo conservador, BFS con `requests`+`BeautifulSoup`, normalizacion de URL, slug kebab ASCII, idempotencia por hash SHA-256, reintentos 1/2/4 s ante 5xx/429, respeto de `Crawl-delay`.
- [x] #4 Explica que se descarga (HTML del dominio `valledellili.org` con sidecar `.json` en `data/raw/valledellili-org/` y registro en `data/raw/_log.jsonl`) y que se descarta (PDF, imagenes, ZIP, fragmentos `#`, `mailto:`/`tel:`/`javascript:`, dominios externos).
- [x] #5 Detalla la conversion a Markdown citando `src/markdown_export/conversion.py`: limpieza de `script`/`style`/`nav`/`header`/`footer`/banners de cookies, `markdownify` con `heading_style=ATX`, ejemplo de front matter YAML con campos `source_url`, `titulo`, `seccion`, `fecha_extraccion`, `idioma`, `hash`, y rutas en kebab ASCII bajo `data/markdown/valledellili-org/`.
- [x] #6 Explica como funciona la recuperacion sin chunking ni vectores citando `src/retrieval/recuperador.py`: indice BM25 (`rank-bm25`) por archivo `.md` completo, tokenizador (minusculas, sin tildes, longitud >= 2, stopwords ES), seleccion del top-1 por `argmax`, manejo de `RecuperacionVaciaError`, e inyeccion del `.md` integro en el prompt del LLM.
- [x] #7 Incluye los comandos canonicos `uv run python -m scripts.scrape` y `uv run python -m scripts.export_markdown`, y menciona variables relevantes de `.env.example` (`URL_BASE_SITIO`, `USER_AGENT`, `OLLAMA_BASE_URL`, `MODELO_LLM_DEFECTO`).
- [x] #8 Cierra con limitaciones conocidas (`num_ctx`, ambiguedad de BM25 con vocabulario repetido, disponibilidad de `gemma4:e2b`) y un roadmap breve hacia el Modulo 2 (chunking, embeddings, base vectorial, re-ranking).
- [x] #9 El documento usa identificadores y rutas ASCII puras conforme a `.cursor/rules/language-conventions.mdc`.
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-04-27: backlog/docs/fase-1-mvp.md se renombró al patrón doc-001 (...).md con id/title/type/created_date. Ver regla backlog-docs-format.mdc y skill backlog-docs para futuros documentos.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se redacto el documento guia con 10 secciones bajo backlog/docs/doc-001 - MVP-Fase-1-Proyecto-Final-QA-BM25.md (front matter id doc-001, tipo guide, created_date), alineado al formato Backlog.md upstream. Contenido: resumen ejecutivo, decisiones de diseno (ADR-0001), arquitectura con diagrama Mermaid, scraping, que se descarga / que no, conversion a Markdown, recuperacion BM25 sin vectores, inyeccion en el prompt, comandos uv y variables .env, limitaciones y roadmap Modulo 2. Posteriormente se anadio la convención doc-<N>: regla backlog-docs-format.mdc y skill backlog-docs.
<!-- SECTION:FINAL_SUMMARY:END -->
