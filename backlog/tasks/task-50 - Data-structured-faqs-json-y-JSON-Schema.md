---
id: TASK-50
title: data/structured/faqs.json (5–10 FAQs) y JSON Schema de validación
status: To Do
assignee: []
created_date: '2026-05-11 00:00'
updated_date: '2026-05-11 00:00'
labels:
  - datos
  - faq
  - modulo-2
dependencies: []
references:
  - data/structured/faqs.json
  - data/structured/faqs.schema.json
documentation:
  - backlog/docs/actividades/Técnicas Avanzadas de IA en Modelos de Lenguaje - Actividad del Módulo 2.pdf
priority: high
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

La herramienta estructurada de FAQs debe leer un **JSON fijo** versionado en el repo, con contenido realista de la **Fundación Valle del Lili** (contacto, horarios, sedes, etc.), sin consultar Qdrant ni el corpus markdown en runtime.

## Objetivo

1. Crear **`data/structured/faqs.json`** con **mínimo 5** e idealmente **8** entradas, por ejemplo (ajustar a datos públicos verificables):
   - Teléfono / línea de atención / call center
   - Horarios generales de atención
   - NIT / razón social (si aplica y es público)
   - Sedes en Cali / dirección principal
   - Correo de citas / contacto
   - Sitio web oficial
   - Urgencias 24h (si aplica)
   - Portal del paciente / política de seguros (según disponibilidad pública)

2. Cada ítem debe incluir campos:
   - `id` (string estable)
   - `intent` (slug ASCII)
   - `keywords` (lista de strings en español; ASCII tras normalización en consumidor)
   - `pregunta_canonica`
   - `respuesta` (texto breve y factual)
   - `source_url` (opcional, URL pública)
   - `actualizado_el` (ISO date)

3. Crear **`data/structured/faqs.schema.json`** (JSON Schema draft 2020-12 o compatible) para validar el archivo en CI o tests.

## Dependencias entre tareas

Puede ejecutarse en paralelo con fases de infraestructura; **task-51** depende de este artefacto.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria

<!-- AC:BEGIN -->
- [ ] #1 Archivo `faqs.json` versionado con ≥5 FAQs coherentes con dominio FVL
- [ ] #2 Cada FAQ incluye los campos obligatorios listados; `keywords` no vacío
- [ ] #3 `faqs.schema.json` valida el JSON (test o script `check-jsonschema`)
- [ ] #4 Contenido revisado para evitar datos personales o clínicos; solo información institucional pública
- [ ] #5 README o doc-003 referenciará cómo actualizar FAQs (nota breve puede ir en Implementation Notes aquí)
- [ ] #6 Sin secretos ni tokens en URLs
- [ ] #7 Ejemplos de intents cubren al menos contacto, horario y ubicación
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Recopilar datos públicos desde sitio oficial (sin scraping agresivo si ya hay corpus; reutilizar fuentes ya citadas en markdown del repo cuando sea posible).
2. Redactar respuestas concisas y neutrales.
3. Escribir schema JSON y test de validación en pytest o npm (preferir pytest para una sola fuente).
4. Revisión ortográfica español LATAM.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Si algún dato no está verificado, usar formulación genérica ("consulte el canal oficial X") y enlazar `source_url`.
- Mantener `id` estables para no romper analytics futuros.
<!-- SECTION:NOTES:END -->

## Definition of Done

<!-- DOD:BEGIN -->
- [ ] #1 Test o script de validación schema pasa en CI local (`uv run pytest` o comando documentado)
- [ ] #2 Archivos UTF-8
- [ ] #3 `docker compose` monta `data/structured` ro en API según task-45
<!-- DOD:END -->
