# Agente TAAM (LangChain Ruta A)

Modulo M3: `create_agent`, tools con Pydantic, `AsyncPostgresSaver`, `@dynamic_prompt` y `HumanInTheLoopMiddleware`.

## Session ID

Formato canonico: `telegram:{chat_id}`. El checkpointer usa `thread_id` = `session_id`.

## Human-in-the-loop (UC-MVP-03)

La tool `escalar_a_equipo` esta configurada en `HumanInTheLoopMiddleware` con `interrupt_on`:

- Antes de persistir la alerta, el grafo queda en estado `__interrupt__`.
- El endpoint `POST /chat` expone `requiere_revision_humana: true` cuando hay `__interrupt__`.
- **Nuevo mensaje del paciente (Telegram):** `invocar_agente` llama a `reanudar_hitl_si_pendiente(..., decision="reject")` si el hilo tiene `state.next` pendiente. Así se evita el error OpenAI 400 por `tool_call_id` sin respuesta cuando el paciente escribe de nuevo sin que staff haya aprobado el escalamiento.
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

### Flujo esperado con severidad urgente

1. El modelo llama `clasificar_triage` → `urgente`.
2. El modelo intenta `escalar_a_equipo` → **interrupcion HITL**.
3. Staff o script de demo llama `continuar_despues_hitl(..., decision="approve")`.
4. La alerta queda visible en API staff (TASK-108).

### Si el paciente ve timeout tras un escalamiento

Suele deberse a un hilo bloqueado en HITL (historial con `tool_calls` sin `ToolMessage`). Tras el fix anterior, el **siguiente** mensaje del paciente reanuda con `reject` y el bot vuelve a responder.

Desbloqueo manual sin esperar otro mensaje:

- API staff: `POST /api/staff/casos/{uuid}/reanudar-hitl` con `{"decision": "approve"}` o `"reject"`.
- Script: `continuar_despues_hitl(session_id="telegram:{chat_id}", decision=...)`.
- Ultimo recurso: borrar el checkpoint del `thread_id` en Postgres o usar otro chat Telegram (`/start CODIGO`).

## Guardrails de alcance (postoperatorio)

Con `AGENTE_GUARDRAILS_HABILITADO=true` (defecto), cada mensaje del paciente pasa por `evaluar_alcance_consulta` en `guardrails_alcance.py` **antes** del LLM del agente:

1. Heurísticas rápidas (p. ej. programación → rechazo; fiebre/herida → permitir).
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
