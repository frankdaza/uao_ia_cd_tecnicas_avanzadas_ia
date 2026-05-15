---
id: TASK-62
title: >-
  Documentación doc-003: Arquitectura del agente Módulo 2 (Markdown en
  backlog/docs)
status: Done
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-15 00:07'
labels:
  - docs
  - modulo-2
dependencies:
  - TASK-43
  - TASK-61
references:
  - backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md
  - .claude/skills/backlog-docs/SKILL.md
documentation:
  - backlog/decisions/decision-3 - Arquitectura-Agente-Memoria-RAG-Qdrant-M2.md
priority: medium
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

Los ADR capturan decisiones; falta una **guía operativa** amplia para desarrollo, demo y troubleshooting del agente M2 (sin BM25 en runtime, Qdrant denso, memoria Postgres).

## Objetivo

Crear **`backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md`** siguiendo la skill **`backlog-docs`**:

- Front matter YAML con `id`, `title`, `type`, `created_date` alineado al estándar del repo.
- Contenido en español latinoamericano:
  - Diagrama Mermaid del agente (sin nodos BM25).
  - Diseño de las dos tools (FAQ determinista vs RAG denso) y justificación pedagógica.
  - Gestión de memoria: beneficios, límites (`HISTORIAL_DIAS_MAX`), consideraciones de privacidad.
  - Comandos para desarrollo local y Docker Compose (postgres, qdrant, api).
  - **Troubleshooting**: Postgres no levanta, timeout Qdrant, embeddings sin API key, colección vacía.
  - Ejemplos de los **4 escenarios** con `curl` (referencia a tests e2e task-61).
  - Sección **"Migración desde BM25 (M1) a Qdrant denso (M2)"**: pasos para indexar `data/markdown/` y verificar salud del sistema.

## Dependencias

Requiere ADR **decision-3** y suite e2e **task-61** para no documentar comportamientos no verificados.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Archivo cumple naming `doc-003 - ...` y skill backlog-docs
- [x] #2 Front matter válido y consistente con otras docs del repo
- [x] #3 Incluye diagrama Mermaid y secciones listadas en Description
- [x] #4 Troubleshooting con síntomas → causas → acciones
- [x] #5 Ejemplos `curl` copy-paste con `BASE_URL` placeholder
- [x] #6 Sin secretos; solo placeholders de variables
- [x] #7 Enlaces internos a ADR decision-3 y a scripts/README.md
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Leer `backlog-docs` skill y un `doc-002` existente como plantilla de tono/estructura.
2. Redactar secciones técnicas a partir del código final (tasks 45–61).
3. Insertar diagramas y tablas solo si aportan (preferir listas claras).
4. Revisión ortográfica y de enlaces rotos.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Mantener espejo `.cursor/skills/backlog-docs` si se actualiza la skill (no obligatorio en esta task salvo cambio de regla).
- Si `doc-003` ya existe por otro PR, evolucionar en lugar de duplicar IDs.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Se agrego backlog/docs/doc-003 - Arquitectura-Agente-Modulo-2.md con front matter alineado a backlog-docs, diagrama Mermaid sin BM25, secciones de tools FAQ vs RAG denso, memoria (HISTORIAL_DIAS_MAX / HISTORIAL_TURNOS_MAX y privacidad), comandos uv/docker-compose, tabla de troubleshooting, ejemplos curl con BASE_URL y referencia a tests/e2e/test_escenarios_modulo2.py, migracion M1 BM25 a M2 Qdrant, y enlaces a decision-3 y scripts/README.md. El ADR decision-3 ya enlazaba a doc-003 en Referencias (referencia cruzada). Revision: checklist de criterios de aceptacion aplicada sobre el archivo entregado.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Archivo mergeado en `backlog/docs/`
- [x] #2 Referencia cruzada desde README (task-63) o desde ADR
- [x] #3 Revisión por par técnico (self-review + checklist AC)
<!-- DOD:END -->
