---
id: TASK-108
title: >-
  API staff: historial conversaciones, alertas triage y marcar revisado
  (UC-MVP-05)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
updated_date: '2026-05-23 05:35'
labels:
  - modulo-3
  - taam
  - fastapi
  - staff
milestone: m-0
dependencies:
  - TASK-104
  - TASK-105
  - TASK-102
priority: high
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC-MVP-05** (personal clínico revisa interacciones y valida triage). Tras **TASK-104** el agente persiste hilos en **PostgresSaver** (`thread_id` = `telegram:{chat_id}`). Tras **TASK-105** las rutas staff exigen JWT. Esta tarea expone la **vista API** que consumirá el panel **TASK-113** (`features/seguimiento/`).

**Dependencias:** TASK-102 (casos/vínculo), TASK-105 (auth JWT), TASK-104 (checkpointer + alertas vía `escalar_a_equipo`).

**Referencias:** `backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md` (UC-MVP-05), `proyecto-2/src/persistencia/repositorios/alertas_triage.py`, `proyecto-2/src/agentes/servicio.py`.

## Objetivo

Endpoints **solo lectura/actualización acotada** bajo `/api/staff/` para bandeja de alertas, historial conversacional por caso y resumen operativo.

## Endpoints (contrato)

| Método | Ruta | Auth | Comportamiento |
|--------|------|------|----------------|
| `GET` | `/api/staff/alertas` | Bearer staff | Query: `revisado` (bool, default `false`), `severidad`, `caso_id`, `limit` (1–100), `offset`. Orden: **urgente → seguimiento → info**, luego `created_at` desc. |
| `PATCH` | `/api/staff/alertas/{id}` | Bearer staff | Body: `{ "revisado": true }`. Idempotente: si ya revisada, `200` sin cambiar `revisado_at` ni auditoría. Registra `revisado_at` y `revisado_staff_id` (FK `usuarios_staff`). |
| `GET` | `/api/staff/casos/{id}/conversacion` | Bearer staff | Mensajes **human/assistant** del hilo `telegram:{chat_id}` vía `aget_state` del agente (no tablas M2). `404` si el caso no tiene vínculo Telegram activo. |
| `GET` | `/api/staff/casos/{id}/resumen` | Bearer staff | Última alerta de triage, conteo de mensajes del hilo, próximo recordatorio pendiente (`recordatorios_enviados`). |

## Privacidad (RBAC TASK-105)

- Rol **`asistente`:** enmascarar `telegram_chat_id` y `paciente_doc_id` en respuestas (últimos 4 caracteres visibles).
- Roles **`clinico`** y **`admin`:** valores completos en API (demo institucional).
- **Auditoría:** `revisado_staff_id` + `revisado_at` en PATCH.

## Rendimiento y límites

- Índice compuesto `(revisado, created_at DESC)` en `alertas_triage` (migración `0003`).
- **No** consultar `chat_history` ni tablas del Módulo 2 en `proyecto-1/`.
- Paginación obligatoria en listado de alertas.

## Fuera de alcance (MVP)

- Responder en Telegram desde el panel.
- Editar o borrar mensajes del hilo.
- Reanudar HITL desde estos endpoints (sigue en servicio agente / demo API).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 GET /api/staff/casos/{id}/conversacion devuelve mensajes human/assistant ordenados por aparición en el hilo cuando existe vínculo Telegram; 404 sin vínculo
- [x] #2 #2 GET /api/staff/alertas con revisado=false devuelve solo pendientes; filtros severidad y caso_id; orden urgente primero
- [x] #3 #3 PATCH /api/staff/alertas/{id} con revisado=true es idempotente y persiste revisado_at y revisado_staff_id
- [x] #4 #4 Tests API: fixture de alerta en BD + hilo sembrado con aupdate_state/MemorySaver (sin OpenAI)
- [x] #5 #5 OpenAPI: router tag staff-seguimiento y rutas documentadas en README proyecto-2
- [x] #6 #6 Migración Alembic 0003: columna revisado_staff_id e índice (revisado, created_at) en alertas_triage
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Migración `0003_alertas_triage_auditoria.py`: `revisado_staff_id` (FK `usuarios_staff`, nullable) + índice `ix_alertas_triage_revisado_created_at`.
2. Modelo `AlertaTriage` + `RepositorioAlertasTriage` (filtro `caso_id`, `marcar_revisado`, orden severidad).
3. `src/api/esquemas_seguimiento.py` (vistas alerta, mensaje, listados, PATCH, resumen).
4. `src/api/servicios/historial_conversacion.py` (lectura `aget_state`, filtro roles human/ai).
5. `src/api/servicios/seguimiento_caso.py` (resumen: alertas + recordatorios + conteo).
6. `src/api/routers/staff_seguimiento.py` + registro en `main.py`.
7. `tests/api/test_staff_seguimiento.py` + README.
8. Cerrar tarea: status Done, AC marcados, notas de verificación.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
- Historial: `construir_agente_taam(checkpointer).aget_state({"configurable": {"thread_id": f"telegram:{chat_id}"}})`; en tests sembrar con `aupdate_state` sin invocar LLM.
- Tag OpenAPI: `staff-seguimiento` (distinto de `staff-casos`).
- PATCH rechaza `revisado: false` con 422 en MVP.

**Verificación (2026-05-22):** `uv run pytest tests/api/test_staff_seguimiento.py` — 6 passed. Migración `0003_alertas_auditoria`. Router `staff_seguimiento.py` registrado en `main.py`. README actualizado.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
API UC-MVP-05: cuatro endpoints staff bajo tag `staff-seguimiento` (alertas list/PATCH, conversación y resumen por caso). Historial desde checkpointer LangGraph; auditoría `revisado_staff_id` + migración 0003 con índice de bandeja. Tests API sin OpenAI (hilo sembrado con `aupdate_state`).
<!-- SECTION:FINAL_SUMMARY:END -->
