# Agente TAAM (LangChain Ruta A)

Modulo M3: `create_agent`, tools con Pydantic, `AsyncPostgresSaver`, `@dynamic_prompt` y `HumanInTheLoopMiddleware` opcional.

## Session ID

Formato canonico: `telegram:{chat_id}`. El checkpointer usa `thread_id` = `session_id`.

## Escalamiento y bandeja de alertas (UC-MVP-05)

Por defecto (HITL desactivado; valor inicial en `.env`, luego panel **Administracion → Escalamiento clinico (HITL)**):

1. El modelo puede llamar `clasificar_triage` y `escalar_a_equipo`.
2. `escalar_a_equipo` persiste de inmediato en `alertas_triage` (sin interrupcion HITL).
3. Tras cada turno de `POST /chat`, `asegurar_alerta_desde_turno` garantiza una alerta si la severidad es `urgente` o `seguimiento` y la tool no la creo ya (heuristica de respaldo sobre el mensaje del paciente).

La bandeja staff (`GET /api/staff/alertas?revisado=false`) muestra esas filas sin paso manual.

## Human-in-the-loop (opcional, UC-MVP-03)

Con HITL activado (panel admin o `AGENTE_HITL_ESCALAR_HABILITADO=true` solo al sembrar la fila), la tool `escalar_a_equipo` queda en `HumanInTheLoopMiddleware` con `interrupt_on`:

- API admin: `GET/PATCH /api/admin/agente-hitl` (solo rol `admin` o `X-Admin-Key`).

- Antes de persistir la alerta, el grafo queda en estado `__interrupt__`.
- El endpoint `POST /chat` expone `requiere_revision_humana: true` cuando hay `__interrupt__`.
- **No** se crea alerta automatica mientras HITL este pendiente (`asegurar_alerta_desde_turno` no actua).
- **Nuevo mensaje del paciente (Telegram):** `invocar_agente` llama a `reanudar_hitl_si_pendiente(..., decision="reject")` solo si HITL esta activo. Asi se evita el error OpenAI 400 por `tool_call_id` sin respuesta.
- **Staff:** `POST /api/staff/casos/{caso_id}/reanudar-hitl` con body `{"decision": "approve"|"reject"}` o `continuar_despues_hitl` desde Python.

### Reanudar tras aprobacion (demo / staff)

```python
from src.agentes.servicio import continuar_despues_hitl

estado = await continuar_despues_hitl(
    session_factory=factory,
    checkpointer=checkpointer,
    session_id="telegram:123",
    decision="approve",  # o "reject"
)
```

- **approve**: ejecuta `escalar_a_equipo` y crea la fila en `alertas_triage`.
- **reject**: no crea alerta; el agente puede responder al paciente sin escalamiento.

### Flujo con HITL activo y severidad urgente

1. El modelo llama `clasificar_triage` → `urgente`.
2. El modelo intenta `escalar_a_equipo` → **interrupcion HITL**.
3. Staff llama `continuar_despues_hitl(..., decision="approve")` o `POST .../reanudar-hitl`.
4. La alerta queda visible en API staff.

### Si el paciente ve timeout tras un escalamiento

Suele deberse a un hilo bloqueado en HITL (historial con `tool_calls` sin `ToolMessage`). Con HITL activo, el **siguiente** mensaje del paciente reanuda con `reject` y el bot vuelve a responder.

Desbloqueo manual:

- API staff: `POST /api/staff/casos/{uuid}/reanudar-hitl` con `{"decision": "approve"}` o `"reject"`.
- Script: `continuar_despues_hitl(session_id="telegram:{chat_id}", decision=...)`.
- Ultimo recurso: borrar el checkpoint del `thread_id` en Postgres o usar otro chat Telegram (`/start CODIGO`).

## Guardrails de alcance (postoperatorio)

Con `AGENTE_GUARDRAILS_HABILITADO=true` (defecto), cada mensaje del paciente pasa por `evaluar_alcance_consulta` en `guardrails_alcance.py` **antes** del LLM del agente:

1. Heuristicas rapidas (p. ej. programacion → rechazo; fiebre/herida → permitir).
2. Si el mensaje es dudoso y hay `OPENAI_API_KEY`, un clasificador LLM estructurado decide.
3. Fuera de alcance: se persiste en el checkpointer el mensaje fijo `MENSAJE_FUERA_DE_ALCANCE` sin ejecutar tools ni `ainvoke` completo.

Desactivar en tests locales: `AGENTE_GUARDRAILS_HABILITADO=false`.

## Invocacion desde servicios

En **Postgres** (produccion / Docker), use ``AsyncPostgresSaver`` (``ainvoke``, ``aupdate_state``, ``aget_state``):

```python
from src.agentes.checkpointer import gestionar_checkpointer_postgres_async
from src.agentes.servicio import invocar_agente, extraer_texto_respuesta

async with gestionar_checkpointer_postgres_async(cfg.url_base_datos_sync()) as cp:
    estado = await invocar_agente(
        session_factory=factory,
        checkpointer=cp,
        session_id="telegram:123",
        mensaje="Tengo fiebre alta",
    )
texto = extraer_texto_respuesta(estado)
```

El lifespan de FastAPI ya abre el checkpointer async en arranque.

En **tests SQLite**, use `crear_checkpointer_para_url("sqlite+aiosqlite:///:memory:")` (devuelve `MemorySaver`).

## Verificacion rubrica

```bash
./scripts/verificar_stack_m3.sh
uv run pytest tests/agentes/test_stack_ruta_a.py -q
```
