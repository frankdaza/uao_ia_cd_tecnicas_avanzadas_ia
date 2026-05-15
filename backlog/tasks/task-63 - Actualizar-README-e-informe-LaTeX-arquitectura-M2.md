---
id: TASK-63
title: Actualizar README.md e informe/Informe_Latex.tex con arquitectura Módulo 2
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-15 01:01'
labels:
  - docs
  - informe
  - modulo-2
dependencies:
  - TASK-62
references:
  - README.md
  - informe/Informe_Latex.tex
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
documentation:
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
priority: medium
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El README y el informe LaTeX aún describen el stack del Módulo 1 (BM25 archivo completo, endpoints `/api/qa`, posible dual Ollama/OpenAI). Deben reflejar el **agente M2**, Docker con Postgres+Qdrant, y el flujo de indexación.

## Objetivo — README

- Nueva sección **"Stack del Módulo 2"** (LangGraph, LangChain postgres, LlamaIndex, Qdrant).
- **Variables `.env` nuevas** (tabla o lista agrupada).
- **Arquitectura agéntica** con enlace a `doc-003` y `decision-3`.
- **Cómo correr con Docker** (postgres + qdrant + api + jobs init).
- **Indexar el corpus en Qdrant** (`uv run python scripts/indexar_corpus_qdrant.py ...`).
- **Eliminar o acotar** secciones que describen BM25 en runtime y modo dual Ollama+OpenAI; si se desea trazabilidad histórica, mover a subsección **"Historial de versiones"** breve.

## Objetivo — Informe LaTeX

- Añadir capítulo **"Módulo 2 — Agente conversacional"** con:
  - Arquitectura y diagrama (figure o texto).
  - Diseño de tools y memoria.
  - Justificación de **Qdrant denso puro** vs BM25/híbrido (referencia a decision-3).
  - Resultados de pruebas con referencia a **task-61** (tabla resumen o narrativa).
  - Capturas o transcripciones breves de eventos `pensamiento` / `herramienta` del SSE (sin datos personales).

## Idioma

Prosa en **español latinoamericano** en ambos artefactos.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 README describe el arranque actual sin mencionar `/api/qa` como ruta principal
- [x] #2 README enlaza a `doc-003` y menciona requisitos Docker nuevos
- [x] #3 Informe LaTeX compila con `latexmk` o comando usado en el repo sin errores nuevos
- [x] #4 Capítulo M2 incluye referencias bibliográficas internas (ADR, doc-003, tests e2e)
- [x] #5 Se eliminan afirmaciones incorrectas sobre BM25 en runtime; lo histórico queda acotado
- [x] #6 Figuras/tablas numeradas y referenciadas correctamente en LaTeX
- [x] #7 Sin rutas absolutas personales ni secretos
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Auditar README actual y marcar párrafos obsoletos.
2. Redactar secciones nuevas alineadas a doc-003.
3. Editar `Informe_Latex.tex`: `\chapter` o `\section` según estilo del documento.
4. Añadir figuras (PDF/PNG) si existen diagramas exportados; si no, usar listing de eventos SSE anonimizados.
5. Compilar informe localmente y corregir warnings mayores.
6. PR único o coordinado con cambios de código final M2.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Mantener compatibilidad con instrucciones docente del curso (portada, integrantes) intacta salvo que se pida lo contrario.
- Si el informe tiene dependencias LaTeX no disponibles en CI, documentar solo build local.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
README.md reescrito centrado en el agente M2: stack LangGraph/LangChain/LlamaIndex, Postgres, Qdrant, variables de entorno agrupadas, ingesta con `uv run python -m scripts.indexar_corpus_qdrant`, Docker Compose y API principal `/api/agente/stream`; enlaces a doc-003 y decision-3; BM25 y `/api/qa` acotados en seccion de historial M1. informe/Informe_Latex.tex: nueva seccion M2 con figura TikZ, herramientas/memoria, justificacion densa vs BM25 con cita al ADR, tabla resumen E2E (TASK-61), listing SSE anonimizado, referencias bibliograficas internas; intro/discusion/conclusiones alineadas. Compilacion verificada con `latexmk -g -pdf` en informe/.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 README revisado por checklist AC
- [ ] #2 Informe PDF generado y adjunto en entrega académica según flujo del curso (fuera de alcance git opcional)
- [x] #3 `uv run pytest` + `pnpm --dir frontend test` verdes en rama de cierre M2
<!-- DOD:END -->
