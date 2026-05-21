---
id: TASK-97
title: 'Documento casos de uso TAAM MVP (5 UC, matriz trazabilidad, guion demo)'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:15'
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
documentation:
  - .cursor/rules/backlog-docs-format.mdc
  - .claude/skills/backlog-docs/SKILL.md
priority: high
ordinal: 2010
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

El documento actual mezcla 8 casos sin priorización, duplica capacidades de staff y no traza endpoints/tools M3. Es la fuente de verdad funcional para sustentación y pruebas.

## Objetivo

Reescribir el documento de casos de uso con **5 UC-MVP** detallados y sección **Fuera de MVP**, alineado a decision-4 (TASK-96).

## Estructura obligatoria

1. Resumen ejecutivo (problema, Telegram, Ruta A vía 2).
2. Glosario: triage, protocolo general vs caso, `session_id`.
3. Actores (Paciente, Asistente, Personal clínico unificado, Administrador catálogo; Bot como subsistema, no actor numerado).
4. **UC-MVP-01** Registrar tipo procedimiento + PDF (admin).
5. **UC-MVP-02** Vincular paciente a seguimiento (asistente; sin PDF por paciente).
6. **UC-MVP-03** Consultar Bot Lili por Telegram (núcleo demo): flujos, red flags, HITL, escalación.
7. **UC-MVP-04** Recordatorios proactivos (plantilla + fecha cirugía; sin email).
8. **UC-MVP-05** Revisar conversaciones y alertas (solo lectura + marcar revisado).
9. Tabla Fase 2 (evidencias, citas email, RBAC, intervención en vivo).
10. Matriz UC → endpoint → tool LangChain → pantalla `proyecto-2/frontend`.
11. Guion demo 15 min (pasos para profesor con teléfono).
12. Datos de prueba: 2 pacientes, 1 procedimiento PDF, tokens Telegram de prueba.

## Plantilla por UC

Cada UC debe incluir: ID, actor, objetivo, precondiciones, flujo principal numerado, alternativos/excepciones, postcondiciones, reglas de negocio (disclaimer médico), datos persistidos, criterios aceptación demo.

## Archivos

- Actualizar `backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md`.
- Opcional: `backlog/docs/doc-00X - Bot-Posoperatorio-Casos-Uso-MVP.md` con front matter si se formaliza como doc de proyecto.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Los 5 UC-MVP tienen plantilla completa (no solo una fila de tabla)
- [ ] #2 Existe sección Fuera de MVP con al menos 5 ítems explícitos del documento original
- [ ] #3 Matriz de trazabilidad cubre los 5 UC con endpoints y tools nombrados
- [ ] #4 Guion de demo en vivo documentado paso a paso (vincular paciente, preguntar, ver alerta en panel)
- [ ] #5 Triage define severidades cerradas: info, seguimiento, urgente y acciones por severidad
- [ ] #6 Documento referencia decision-4 y proyecto-2 sin contradecir M2 en proyecto-1
<!-- AC:END -->
