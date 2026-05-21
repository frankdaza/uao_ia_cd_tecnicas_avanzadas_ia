---
id: TASK-104
title: 'Endpoint REST POST /chat para canal externo (contrato JSON, sin SSE)'
status: Done
assignee:
  - Frank Daza
created_date: '2026-05-21 22:16'
updated_date: '2026-05-21 23:47'
labels:
  - modulo-3
  - taam
  - fastapi
  - api
milestone: m-0
dependencies:
  - TASK-103
modified_files:
  - proyecto-2/src/api/routers/chat.py
  - proyecto-2/src/api/esquemas_chat.py
  - proyecto-2/src/api/servicios/chat.py
  - proyecto-2/src/api/dependencias.py
  - proyecto-2/src/api/main.py
  - proyecto-2/src/configuracion.py
  - proyecto-2/src/agentes/servicio.py
  - proyecto-2/tests/api/test_chat.py
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
## Contexto

UC-MVP-03 y [decision-7](backlog/decisions/decision-7%20-%20Arquitectura-M3-TAAM-Proyecto-2-Telegram-Ruta-A.md) definen el canal **Telegram vía 2**: el webhook (TASK-106) no llama al LLM directamente; delega en **`POST /chat`** con contrato JSON **sin SSE** (el streaming de M2 en `proyecto-1/` no aplica).

**Prerrequisito cerrado:** módulo agente TASK-103 (`servicio.invocar_agente`, HITL, `extraer_texto_respuesta`). Este entregable es la **capa HTTP** consumible por TASK-106 y pruebas httpx.

## Objetivo

Exponer `POST /chat` en `proyecto-2/src/api/routers/chat.py` (montaje en raíz, no bajo `/api`) que valide sesión Telegram vinculada, invoque un turno del agente y devuelva JSON estable para el integrador.

## Contrato request (`ChatPeticion`)

| Campo | Tipo | Reglas |
| --- | --- | --- |
| `session_id` | string | Formato canónico `telegram:{chat_id}` (entero Telegram) |
| `mensaje` | string | Texto del paciente; `min_length=1`, recorte de espacios |
| `metadata` | object opcional | `canal` (p. ej. `telegram`), `caso_id` (UUID opcional), `update_id` (correlación logs) |

## Contrato response (`ChatRespuesta`)

| Campo | Tipo | Reglas |
| --- | --- | --- |
| `respuesta` | string | Texto para el paciente (incluye mensaje fijo si HITL) |
| `severidad_triage` | `info` \| `seguimiento` \| `urgente` \| null | Última salida de `clasificar_triage` en el turno, si existe |
| `requiere_revision_humana` | bool | `true` si el estado del grafo tiene `__interrupt__` |
| `fuentes` | lista | Fragmentos RAG `{titulo, fragmento}` derivados de `consultar_protocolo_rag` en el turno |
| `error` | string \| null | Solo uso interno/diagnóstico acotado; en errores HTTP usar `detail` de FastAPI |

## Comportamiento HTTP

| Caso | Código | `detail` (español) |
| --- | --- | --- |
| `session_id` con formato inválido | 422 | Validación Pydantic |
| Sin vínculo Telegram activo (`vinculado_at` nulo) | 403 | Instrucción de emparejamiento (UC-MVP-02) |
| Timeout LLM/agente (`CHAT_TIMEOUT_SEG`) | 503 | Mensaje genérico; **sin** stack trace ni secretos |
| Turno OK | 200 | Cuerpo `ChatRespuesta` |

- **Auth:** no exige header en MVP; la barrera es el vínculo OLTP. TASK-106 llamará en el mismo proceso o red de confianza.
- **Idempotencia:** no requerida; documentar reenvío de updates Telegram.
- **Logging:** `session_id` + `metadata.update_id` cuando exista.

## OpenAPI

- Tag `chat`.
- Ejemplos request/response en español latinoamericano.
- Schemas en `src/api/esquemas_chat.py`.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 POST /chat con sesión vinculada devuelve 200, `respuesta` no vacía y `requiere_revision_humana` coherente con el estado mock del agente
- [x] #2 `session_id` telegram sin `vinculado_at` devuelve 403 con `detail` en español (sin datos clínicos inventados)
- [x] #3 Timeout del turno (config `CHAT_TIMEOUT_SEG` o mock) devuelve 503 con mensaje genérico; la respuesta no incluye API keys ni stack traces
- [x] #4 Tests en `tests/api/test_chat.py` con httpx `AsyncClient`: happy path, sin vínculo y timeout
- [x] #5 OpenAPI (`/openapi.json`) documenta `ChatPeticion` y `ChatRespuesta` bajo tag `chat` con ejemplos
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
## Fase 1 — Esquemas y servicio
1. Crear `esquemas_chat.py` (`ChatPeticion`, `ChatMetadata`, `FuenteChat`, `ChatRespuesta`) con validación de `session_id`.
2. Crear `servicios/chat.py`: validar vínculo vía `parsear_session_telegram` + `RepositorioVinculosTelegram.obtener_vinculado_por_chat_id`.
3. Ampliar `servicio.py` con `extraer_severidad_triage` y `extraer_fuentes_respuesta` escaneando mensajes del turno.

## Fase 2 — Router y lifespan
4. `routers/chat.py`: `POST /chat`, `asyncio.wait_for` con `CHAT_TIMEOUT_SEG`.
5. Guardar `checkpointer` en `app.state` en lifespan; Depends para factory + checkpointer.
6. Registrar router en `main.py` **sin** prefijo `/api`.

## Fase 3 — Config y pruebas
7. Variable `CHAT_TIMEOUT_SEG` en `configuracion.py` y `.env.example` si aplica.
8. `tests/api/test_chat.py`: happy path con mock de `invocar_agente`, 403 sin vínculo, 503 timeout simulado.
9. Verificar schemas en OpenAPI (`/openapi.json`).
<!-- SECTION:PLAN:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
## Referencias
- Agente: `src/agentes/servicio.py` (`invocar_agente`, `extraer_texto_respuesta`, `requiere_revision_humana`).
- Vínculo: `src/persistencia/repositorios/vinculos_telegram.py`, `src/agentes/contexto.parsear_session_telegram`.
- Patrón tests API: `tests/api/conftest.py` + `test_staff_casos.py`.
- UC: `backlog/docs/usecases/Caso de Uso TAAM - Bot Posoperatorio.md` (UC-MVP-03).

## Extracción de metadatos del turno
- `severidad_triage`: último `ToolMessage` de `clasificar_triage` (JSON / modelo Pydantic serializado).
- `fuentes`: parsear salida de `consultar_protocolo_rag` (`[n] fragmento`) en hasta `AGENTE_RAG_K` entradas.

## Tests sin OpenAI
- Mock de `invocar_agente` devolviendo estado mínimo con `AIMessage`.
- Timeout: `CHAT_TIMEOUT_SEG` bajo + mock que duerme o `asyncio.TimeoutError`.

## TASK-106
El webhook construirá `session_id=telegram:{chat_id}` y hará POST interno a `/chat`; mapear 403 a mensaje instructivo de emparejamiento.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implementado POST /chat (JSON, sin SSE): esquemas ChatPeticion/ChatRespuesta, servicio con validacion de vinculo Telegram, timeout CHAT_TIMEOUT_SEG, mapeo de severidad_triage/fuentes/HITL desde estado del agente, checkpointer en app.state y tests httpx (200 mock, 403 sin vinculo, 503 timeout, OpenAPI). Listo para TASK-106 webhook.
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Router `POST /chat` registrado en `crear_app()` y visible en OpenAPI
- [x] #2 `uv run pytest tests/api/test_chat.py` pasa sin regresión de `tests/api/`
- [x] #3 Variable `CHAT_TIMEOUT_SEG` documentada en configuración; sin secretos en backlog
- [x] #4 TASK-106 puede consumir el contrato JSON sin SSE (nota en implementation notes)
<!-- DOD:END -->
