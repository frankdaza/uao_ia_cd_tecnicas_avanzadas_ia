---
id: TASK-97
title: 'Documento casos de uso TAAM MVP (5 UC, matriz trazabilidad, guion demo)'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:15'
updated_date: '2026-05-21 22:38'
labels:
  - modulo-3
  - taam
  - documentacion
  - usecases
milestone: m-0
dependencies:
  - TASK-96
references:
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
  - >-
    backlog/decisions/decision-7 -
    Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md
  - backlog/milestones/m-0 - agentic-final-project.md
  - >-
    backlog/tasks/task-96 -
    ADR-decision-4-arquitectura-M3-TAAM-en-proyecto-2-Ruta-A-Telegram-vía-2.md
documentation:
  - .cursor/rules/backlog-docs-format.mdc
  - .claude/skills/backlog-docs/SKILL.md
modified_files:
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
  - >-
    backlog/tasks/task-97 -
    Documento-casos-de-uso-TAAM-MVP-5-UC-matriz-trazabilidad-guion-demo.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El archivo [Caso de Uso TAAM — Bot Posoperatorio](../docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md) mezcla **8 capacidades** en una tabla sin priorización, duplica roles de staff (cirujano vs asistente) y no traza endpoints, tools LangChain ni pantallas de `proyecto-2/frontend/`. Es la **fuente de verdad funcional** para sustentación M3, pruebas de aceptación y tareas TASK-98+.

**Dependencia:** [TASK-96](task-96) cerró el ADR como [decision-7](../../decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md) (`decision-4` en el repo queda reservado a payload Qdrant M2).

## Objetivo

Reescribir el documento con **5 UC-MVP** (plantilla completa por UC), sección **Fuera de MVP** explícita, **matriz de trazabilidad** UC → API → tool → pantalla, **guion de demo 15 min** y **datos de prueba** alineados a decision-7 sin contradecir el producto M2 en `proyecto-1/`.

## Alcance del entregable

| Sección | Contenido mínimo |
| --- | --- |
| Resumen ejecutivo | Problema FVL, canal Telegram, Ruta A vía 2, frontera proyecto-1 vs proyecto-2 |
| Glosario | triage, protocolo general vs caso, `session_id`, emparejamiento |
| Actores | Paciente, Asistente, Personal clínico (unificado), Admin catálogo; Bot Lili como subsistema |
| UC-MVP-01..05 | ID, actor, objetivo, pre/post, flujos numerados, alternativas, reglas, datos persistidos, criterios demo |
| Fuera de MVP | ≥5 ítems del documento original + ítems de decision-7 |
| Fase 2 | Tabla de capacidades diferidas |
| Matriz | 5 filas con endpoints, tools (`name` inglés) y rutas frontend previstas |
| Guion demo | 15 min, pasos con teléfono + panel staff |
| Datos de prueba | 2 pacientes, 1 procedimiento+PDF, tokens Telegram ficticios |

## Archivos

- **Principal:** `backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md` (reemplazo del cuerpo; conservar enlace a decision-7).
- **Opcional:** `backlog/docs/doc-006 - Bot-Posoperatorio-Casos-Uso-MVP.md` solo si el equipo quiere front matter `doc-*`; no obligatorio si el use case queda autocontenido.

## Restricciones

- No describir endpoints M2 (`POST /api/agente/stream`, sesiones DocId) como parte del MVP TAAM.
- Tools: nombres en **inglés** (contrato LangChain); textos y reglas en español latinoamericano.
- Triage MVP: severidades cerradas `info`, `seguimiento`, `urgente` con acciones documentadas.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Los cinco UC-MVP (01–05) incluyen plantilla completa: actor, objetivo, precondiciones, flujo principal numerado (≥5 pasos donde aplique), alternativas/excepciones, postcondiciones, reglas de negocio (incl. disclaimer médico), datos persistidos y criterios de aceptación para demo
- [x] #2 Sección «Fuera de MVP» lista al menos cinco capacidades del documento original (tabla de 8 filas) más ítems explícitos de decision-7 (email, evidencias multimedia, RBAC completo, intervención en vivo, WhatsApp/N8N)
- [x] #3 Matriz de trazabilidad con una fila por UC-MVP: columnas UC, endpoints FastAPI previstos, tools LangChain (`name`), pantalla/ruta en `proyecto-2/frontend/` y tarea Backlog de implementación
- [x] #4 Guion de sustentación 15 min con tiempos aproximados, roles (presentador/asistente/paciente), pasos: alta procedimiento → caso+código → Telegram → pregunta clínica → alerta en panel → marcar revisado
- [x] #5 Modelo de triage documentado: severidades `info`, `seguimiento`, `urgente`; acción del bot, HITL (`HumanInTheLoopMiddleware`) y registro en `alertas_triage` por severidad
- [x] #6 Referencias cruzadas a decision-7 y m-0; nota de separación con M2 (`proyecto-1/`, LangGraph, SSE) sin contradicciones
- [x] #7 Sección «Datos de prueba» con identidades ficticias (sin PHI real), 1 PDF de protocolo, 2 casos paciente y variables/env Telegram de laboratorio
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Leer documento legacy y decision-7; extraer los 8 UC originales y mapearlos a 5 MVP + Fuera de MVP.
2. Redactar resumen, glosario y actores (unificar cirujano/asistente en «Personal clínico» para UC-05; Bot no es actor numerado).
3. Por cada UC-MVP-01..05: aplicar plantilla; cruzar endpoints de TASK-100, 102, 104, 106, 107, 108 y tools de TASK-103.
4. Tabla Fase 2 y matriz UC → endpoint → tool → `proyecto-2/frontend/src/features/*` → TASK-XXX.
5. Guion 15 min + datos de prueba ficticios.
6. Revisión: grep mental de que no se cite `/api/agente/stream` ni LangGraph como runtime TAAM.
7. Actualizar task-97: marcar AC/DoD, status Done, finalSummary (sin archivar).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
ADR M3 = **decision-7** (no decision-4). Webhook canónico en decision-7: `POST /api/integracion/telegram/webhook`; TASK-106 usa `POST /api/telegram/webhook` — la matriz puede listar ambos como alias documentado hasta unificar en código.
Ingesta PDF (TASK-101) es prerequisito técnico de UC-01 pero no UC separado.
UC-MVP-03 es el núcleo demo; UC-MVP-04 admite `POST /api/staff/casos/{id}/disparar-recordatorio-prueba` para no esperar el scheduler en vivo.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Reescrito backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md: resumen ejecutivo, glosario, actores unificados, modelo de triage (info/seguimiento/urgente), 5 UC-MVP con plantilla completa, Fuera de MVP (8 ítems), Fase 2, matriz UC→API→tool→frontend→TASK, guion 15 min y datos de prueba ficticios. Alineado a decision-7 y frontera proyecto-1/proyecto-2. Task metadata ampliada (AC×7, DoD×3, plan, notas).
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Documento revisado en Markdown sin enlaces rotos a decision-7, m-0 y tareas TASK-100..113
- [x] #2 TASK-98+ pueden citar IDs UC-MVP-0N en descripciones sin ambigüedad
- [x] #3 Guion demo coherente con `sembrar_demo_taam.py` (TASK-114) y webhook Telegram (TASK-106)
<!-- DOD:END -->
