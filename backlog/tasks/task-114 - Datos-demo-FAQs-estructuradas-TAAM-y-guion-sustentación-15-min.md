---
id: TASK-114
title: 'Datos demo, FAQs estructuradas TAAM y guion sustentación 15 min'
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:18'
labels:
  - modulo-3
  - taam
  - demo
  - seed
milestone: m-0
dependencies:
  - TASK-107
  - TASK-111
  - TASK-112
  - TASK-113
priority: high
ordinal: 2180
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La sustentación M3 es **100% práctica** con teléfono del profesor. Sin datos y guion reproducible, la demo falla aunque el código funcione.

## Objetivo

Paquete reproducible de semillas + documento guion alineado a TASK-97.

## Entregables

1. `data/structured/taam_faqs.json` + JSON Schema (5–10 FAQs postoperatorio ficticias pero realistas).
2. Script `proyecto-2/scripts/sembrar_demo_taam.py`: usuarios staff, 1 tipo procedimiento + PDF de ejemplo, 2 casos paciente, plantillas recordatorio.
3. PDF de ejemplo en `data/taam/demo/` (texto sintético, sin PHI real).
4. `backlog/docs/usecases/GUION-DEMO-TAAM.md` o sección en doc UC: pasos minuto a minuto, qué terminal/logs mostrar.
5. Checklist pre-demo: webhook HTTPS, token bot, Qdrant indexado, MOCK_LLM vs real.

## Guion mínimo (5 pasos)

1. Admin sube PDF (o ya sembrado).
2. Asistente crea caso → muestra código.
3. Profesor `/start CODIGO` en Telegram.
4. Pregunta clínica + pregunta red flag → alerta urgente.
5. Panel staff marca alerta revisada.

## Fallas a evitar

- PHI real de pacientes en repo.
- Depender de OpenAI en CI (documentar MOCK_LLM para tests).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 uv run sembrar_demo deja sistema listo sin pasos manuales obscuros
- [ ] #2 faqs.json valida contra schema
- [ ] #3 Guion documentado con tiempos estimados y comandos docker/uv
- [ ] #4 Dos pacientes demo distinguibles en listado staff
- [ ] #5 README proyecto-2 sección «Demo en vivo»
<!-- AC:END -->
