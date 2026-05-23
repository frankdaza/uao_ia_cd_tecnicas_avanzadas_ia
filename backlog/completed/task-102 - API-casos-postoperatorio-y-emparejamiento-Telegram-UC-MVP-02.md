---
id: TASK-102
title: API casos postoperatorio y emparejamiento Telegram (UC-MVP-02)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:16'
updated_date: '2026-05-21 23:32'
labels:
  - modulo-3
  - taam
  - fastapi
milestone: m-0
dependencies:
  - TASK-99
  - TASK-100
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC-MVP-02** ([casos de uso TAAM](../docs/usecases/Caso%20de%20Uso%20TAAM%20-%20Bot%20Posoperatorio.md)): el asistente registra el **caso quirúrgico** de un paciente (sin PDF por paciente) y genera un **código de emparejamiento** para que el paciente vincule su chat de Telegram. Sin caso `activo` + fila en `vinculos_telegram` con `vinculado_at`, **UC-MVP-03** debe rechazar consejo clínico (403).

**Dependencias:** esquema y repositorios **TASK-99**; catálogo con `indexacion_estado=ok` vía **TASK-100**/**TASK-101**.

## Objetivo

Exponer en **`proyecto-2/`** la API staff de casos y el endpoint de emparejamiento invocado por el webhook Telegram (**TASK-106**).

## Contrato HTTP

| Método | Ruta | Auth | Cuerpo / query |
| --- | --- | --- | --- |
| `POST` | `/api/staff/casos` | `X-Staff-Key` | JSON: `paciente_doc_id`, `paciente_nombre`, `tipo_procedimiento_id`, `cirujano_id`, `cirujano_nombre`, `fecha_cirugia` (ISO date), `notas_especificas` opcional |
| `GET` | `/api/staff/casos` | idem | Query `estado` (`activo`\|`cerrado`), `limit` (1–100), `offset` |
| `POST` | `/api/staff/casos/{id}/codigo-emparejamiento` | idem | Sin cuerpo; regenera código (invalida pendiente anterior) |
| `POST` | `/api/telegram/emparejar` | `X-Telegram-Bot-Api-Secret-Token` (= `TELEGRAM_WEBHOOK_SECRET`) | JSON: `codigo`, `telegram_chat_id` (int) |

**Respuesta caso (listado/detalle):** `id`, `paciente_doc_id`, `paciente_nombre`, `tipo_procedimiento_id`, `cirujano_id`, `cirujano_nombre`, `fecha_cirugia`, `notas_especificas`, `estado`, `created_at`, `vinculado_telegram` (bool), `codigo_emparejamiento_activo` (solo si hay pendiente no expirado; sin PII extra).

**Respuesta generar código:** `codigo`, `expira_at` (ISO UTC), `caso_id`.

**Respuesta emparejar:** `caso_id`, `vinculado_at`, `mensaje_confirmacion` (español, para `sendMessage`).

## Persistencia del código (sin tabla extra)

- Fila en `vinculos_telegram` con `vinculado_at IS NULL`, `codigo_emparejamiento` y `codigo_expira_at` (TTL **24 h**).
- `telegram_chat_id` **placeholder negativo** derivado de `caso_id` hasta el emparejamiento; al vincular se actualiza al `chat_id` real y se fija `vinculado_at`.
- Código **un solo uso**: tras emparejar exitoso no se reutiliza el mismo valor.

## Reglas de negocio

- `tipo_procedimiento_id` debe existir y tener `indexacion_estado=ok` al crear caso (422 si no).
- Caso nuevo con `estado=activo`.
- Un `telegram_chat_id` solo puede estar vinculado a **un** caso `activo` (409 si ya existe vínculo con `vinculado_at`).
- Código expirado o inexistente → 400 con `error=codigo_invalido` o `codigo_expirado` y `mensaje_telegram` para la capa Telegram.
- Auth staff MVP: **`STAFF_API_KEY`** + cabecera `X-Staff-Key` (mismo patrón que `ADMIN_API_KEY`; **TASK-105** sustituirá por JWT).

## Fuera de alcance

- Panel React (**TASK-112**), webhook completo (**TASK-106**), recordatorios al crear caso (**TASK-107**), JWT staff (**TASK-105**).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 #1 `POST /api/staff/casos` con procedimiento `indexacion_estado=ok` persiste fila `estado=activo` y responde 201 con `id` y metadatos del caso
- [x] #2 #2 `POST /api/staff/casos` con procedimiento no indexado (`pendiente`/`error`) o inexistente responde 422
- [x] #3 #3 `GET /api/staff/casos` paginado devuelve `items` con `vinculado_telegram` y filtros `estado`/`limit`/`offset`
- [x] #4 #4 `POST .../codigo-emparejamiento` genera código 6–8 caracteres ASCII, `expira_at` ≈ now+24h y asocia pendiente en `vinculos_telegram`
- [x] #5 #5 `POST /api/telegram/emparejar` con código válido actualiza `telegram_chat_id`, fija `vinculado_at` y responde 200 con mensaje de confirmación en español
- [x] #6 #6 Código inválido/expirado en emparejar responde 400 con `error` discriminante y `mensaje_telegram` (consumible por TASK-106)
- [x] #7 #7 Doble emparejamiento del mismo `telegram_chat_id` a otro caso activo responde 409
- [x] #8 #8 Tests en `proyecto-2/tests/api/test_staff_casos.py` con SQLite, fixtures de procedimiento `ok` y auth staff/telegram
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. **Config:** `STAFF_API_KEY`, `TAAM_CODIGO_EMPAREJAMIENTO_TTL_HORAS` (default 24), `TAAM_CODIGO_LONGITUD` (6–8) en `src/configuracion.py`.
2. **Auth:** `requerir_clave_staff` y `requerir_secreto_telegram` en `src/api/dependencias.py`.
3. **Servicio:** `src/api/servicios/emparejamiento.py` — generar código, placeholder `telegram_chat_id`, emparejar, errores estructurados.
4. **Esquemas:** `src/api/esquemas_casos.py` (request/response staff y telegram).
5. **Repositorios:** extender `vinculos_telegram` (por código pendiente, pendiente por caso, actualizar) y validaciones en `casos_postoperatorio` si hace falta.
6. **Routers:** `staff_casos.py` (POST/GET/código) y `telegram_emparejar.py`; montar en `main.py`.
7. **Tests:** `tests/api/test_staff_casos.py` — flujo feliz, 422 procedimiento, 409 chat duplicado, código expirado; fixtures staff + telegram secret.
8. **Docs:** README sección UC-MVP-02; marcar AC/DoD; `task_edit` status Done (sin archivar).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Entregado en proyecto-2: servicios/emparejamiento.py (codigo TTL, placeholder chat_id negativo, errores estructurados); routers staff_casos.py y telegram_emparejar.py; esquemas_casos.py; dependencias requerir_clave_staff y requerir_secreto_telegram; repositorio vinculos_telegram extendido; configuracion STAFF_API_KEY y TAAM_CODIGO_*; tests/api/test_staff_casos.py (6 casos). Auth staff MVP con X-Staff-Key hasta TASK-105. TASK-106 debe POST /api/telegram/emparejar con X-Telegram-Bot-Api-Secret-Token.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
API UC-MVP-02: POST/GET /api/staff/casos, POST codigo-emparejamiento, POST /api/telegram/emparejar con validacion indexacion ok, codigo un solo uso TTL 24h, 409 chat duplicado y errores codigo_expirado para Telegram. Tests API 30 passed en proyecto-2; README actualizado.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Router `/api/staff/casos` y `/api/telegram/emparejar` registrados en `src/api/main.py`
- [x] #2 `STAFF_API_KEY` documentado en README y `.env.example` (placeholder, sin secretos en repo)
- [x] #3 `uv run pytest` en `proyecto-2/` pasa incluyendo tests de casos y emparejamiento
- [x] #4 Servicio `src/api/servicios/emparejamiento.py` centraliza generación TTL, placeholder chat_id y validaciones
<!-- DOD:END -->
