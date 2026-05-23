---
id: TASK-107
title: Recordatorios proactivos Telegram y plantillas por procedimiento (UC-MVP-04)
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:17'
updated_date: '2026-05-22 00:10'
labels:
  - modulo-3
  - taam
  - scheduler
  - telegram
milestone: m-0
dependencies:
  - TASK-106
  - TASK-102
references:
  - backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md
  - >-
    backlog/decisions/decision-7 -
    Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md
  - proyecto-2/src/integracion/recordatorios/
  - proyecto-2/README.md
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

**UC-MVP-04** (ver `backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md`): recordatorios proactivos de medicación, terapia y control postoperatorio. El MVP **no** incluye email, SMTP ni agenda hospitalaria; el único canal de salida es **Telegram Bot API** (misma integración que **TASK-106**).

Las tablas `plantillas_recordatorio` y `recordatorios_enviados` ya existen desde **TASK-99** (migración `0001_inicial_taam`). Esta tarea implementa la lógica de negocio, el job periódico y el endpoint de demo para sustentación.

## Objetivo

1. Sembrar plantillas por `tipo_procedimiento` cuando un tipo aún no tiene ninguna.
2. Al **crear caso** (**TASK-102**), programar filas en `recordatorios_enviados` con `programado_at = medianoche UTC(fecha_cirugia) + offset_horas`.
3. **Job** cada minuto (tarea asyncio en lifespan de FastAPI) que envía pendientes vencidos vía `ClienteTelegram`.
4. **Demo:** `POST /api/staff/casos/{id}/disparar-recordatorio-prueba` para enviar el siguiente pendiente sin esperar el scheduler.

## Contrato de plantilla

Campo `texto_plantilla` con placeholders:

- `{nombre_paciente}` — `casos_postoperatorio.paciente_nombre`
- `{tipo_procedimiento}` — `tipos_procedimiento.nombre`
- `{texto_cuidado}` — texto fijo por tipo de plantilla (`medicacion`, `terapia`, `control`) en semilla MVP

## Reglas de negocio

| Regla | Comportamiento |
| --- | --- |
| Sin vínculo Telegram | No enviar; log `recordatorio_omitido_sin_telegram`; fila sigue `pendiente` |
| Duplicados | Un solo worker asyncio en MVP; marcar `enviado` solo tras `sendMessage` exitoso; reintento no duplica si `estado != pendiente` |
| Caso cerrado | Job solo procesa filas pendientes; no cancela automáticamente en MVP |
| Email | **Fuera de alcance** — no importar ni invocar SMTP |

## Anti-patrones (evitar)

- Enviar recordatorio sin comprobar `vinculos_telegram.vinculado_at`.
- Marcar `enviado` antes de confirmar envío Telegram.
- Bloquear el event loop con HTTP sync a Bot API (usar `httpx` async de TASK-106).
- Depender de OCR del PDF para horarios de recordatorio.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Plantillas asociadas a `tipo_procedimiento` existen en BD (semilla idempotente al crear caso)
- [x] #2 Job envía al menos un recordatorio en prueba con `programado_at` en el pasado y vínculo Telegram (mock `sendMessage`)
- [x] #3 `POST /api/staff/casos/{id}/disparar-recordatorio-prueba` funciona para demo (con y sin vínculo)
- [x] #4 Verificado que el módulo no usa email/SMTP (solo Telegram)
- [x] #5 Tests unitarios de `calcular_programado_at` y render de placeholders
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Fase 1 — Dominio y persistencia
1. `integracion/recordatorios/programacion.py` — `calcular_programado_at`, `renderizar_texto_plantilla`.
2. `integracion/recordatorios/semilla_plantillas.py` — tres plantillas por defecto (24 h / 48 h / 168 h).
3. Repositorios `plantillas_recordatorio` y `recordatorios_enviados`.

## Fase 2 — Servicio y scheduler
4. `integracion/recordatorios/servicio.py` — programar al crear caso, procesar pendientes, disparo manual.
5. `integracion/recordatorios/scheduler.py` + lifespan en `api/main.py` (`RECORDATORIOS_JOB_*`).

## Fase 3 — API staff
6. Hook en `POST /api/staff/casos` → `programar_recordatorios_para_caso`.
7. `POST /api/staff/casos/{id}/disparar-recordatorio-prueba` + esquema `DisparoRecordatorioRespuesta`.

## Fase 4 — Pruebas y documentación
8. `tests/integracion/test_recordatorios_programacion.py` y `tests/api/test_recordatorios.py`.
9. README: rutas, variables, placeholders, límite sin email.
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Referencias
- UC: sección UC-MVP-04 en `backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md`.
- Telegram: `src/integracion/telegram/cliente.py` (`ClienteTelegram.enviar_mensaje`).
- Alta de caso: `src/api/routers/staff_casos.py`.
- Tests: desactivar job con `RECORDATORIOS_JOB_HABILITADO=false` (fixture autouse en `tests/api/conftest.py`).

## Configuración
- `RECORDATORIOS_JOB_HABILITADO` (default `true`).
- `RECORDATORIOS_JOB_INTERVAL_SEG` (default `60`, mínimo 5).

## Demo 15 min
1. Staff crea caso → empareja Telegram → `disparar-recordatorio-prueba` → mensaje en teléfono.
2. Alternativa: `fecha_cirugia` en el pasado + esperar un ciclo del job (menos fiable en vivo).

## SQLite vs Postgres
- Normalizar datetimes naive de SQLite con `_en_utc` antes de comparar con `datetime.now(UTC)`.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
UC-MVP-04 implementado en proyecto-2: paquete src/integracion/recordatorios (programación, semilla de plantillas, servicio de envío, job asyncio en lifespan), repositorios OLTP, hook en alta de caso, endpoint POST /api/staff/casos/{id}/disparar-recordatorio-prueba, variables RECORDATORIOS_JOB_* y README. Tests en tests/integracion/test_recordatorios_programacion.py y tests/api/test_recordatorios.py. Sin email; canal exclusivo Telegram (TASK-106).
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Job registrado en lifespan y desactivable por env en tests
- [x] #2 `uv run pytest tests/integracion/test_recordatorios_programacion.py tests/api/test_recordatorios.py` pasa
- [x] #3 README documenta ruta de demo, variables y placeholders
- [x] #4 Sin regresión en `tests/api/test_staff_casos.py`
- [x] #5 Sin secretos ni tokens en backlog ni commits
<!-- DOD:END -->
