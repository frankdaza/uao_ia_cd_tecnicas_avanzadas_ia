---
id: TASK-99
title: >-
  Esquema Postgres TAAM y migraciones Alembic (procedimientos, casos, alertas,
  Telegram)
status: To Do
assignee:
  - Frank Daza
created_date: '2026-05-21 22:15'
labels:
  - modulo-3
  - taam
  - postgres
  - alembic
milestone: m-0
dependencies:
  - TASK-98
references:
  - proyecto-1/src/persistencia/modelos.py
  - proyecto-1/alembic/
priority: high
ordinal: 2030
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

TAAM requiere entidades que **no existen** en M2 (`Usuario` solo tiene doc_id/nombre). Sin modelo de datos acordado, Telegram, RAG y panel staff divergen.

## Objetivo

Definir tablas OLTP en `proyecto-2` + migración Alembic inicial y repositorios async.

## Tablas propuestas (ajustar en implementación si ADR dice otro nombre)

| Tabla | Campos clave |
|-------|-------------|
| `tipos_procedimiento` | id, codigo, nombre, ruta_pdf, hash_pdf, qdrant_collection_version, created_at |
| `casos_postoperatorio` | id, paciente_doc_id, paciente_nombre, tipo_procedimiento_id, cirujano_id, cirujano_nombre, fecha_cirugia, notas_especificas, estado, created_at |
| `vinculos_telegram` | id, caso_id, telegram_chat_id (unique), codigo_emparejamiento, vinculado_at |
| `alertas_triage` | id, caso_id, severidad, resumen, mensaje_paciente_ref, tool_trace_json, revisado, revisado_at, created_at |
| `plantillas_recordatorio` | id, tipo_procedimiento_id, tipo (medicacion/terapia/control), offset_horas_desde_cirugia, texto_plantilla |
| `recordatorios_enviados` | id, caso_id, plantilla_id, programado_at, enviado_at, estado |
| `usuarios_staff` | id, email, nombre, rol (asistente/clinico/admin), hash_credencial o api_key_ref |

## Reglas

- Índices: `telegram_chat_id` unique; `casos_postoperatorio.paciente_doc_id` + estado.
- **PII:** documentar en comentarios migración qué campos enmascarar en API staff.
- **Separación:** base de datos TAAM distinta a M2 (otro `DATABASE_URL` en compose proyecto-2).
- Identificadores Python ASCII español (`caso_postoperatorio`, no tildes).

## Entregables

- `proyecto-2/alembic/versions/0001_inicial_taam.py`
- `proyecto-2/src/persistencia/modelos.py`, `repositorios/`
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Migración Alembic aplica en Postgres limpio de proyecto-2 sin errores
- [ ] #2 Modelos SQLAlchemy 2 async con type hints y tablas listadas en descripción
- [ ] #3 Repositorios CRUD mínimos: crear/listar tipo_procedimiento, caso, vinculo_telegram, alerta
- [ ] #4 Tests pytest con SQLite/Postgres de prueba validan unicidad telegram_chat_id y FK caso→tipo_procedimiento
- [ ] #5 README o docstring explica separación de BD respecto a proyecto-1
<!-- AC:END -->
