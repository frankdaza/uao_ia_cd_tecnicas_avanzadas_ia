# Agente TAAM (LangChain Ruta A)

Modulo M3: `create_agent`, tools con Pydantic, `AsyncPostgresSaver`, `@dynamic_prompt` y `HumanInTheLoopMiddleware`.

## Session ID

Formato canonico: `telegram:{chat_id}`. El checkpointer usa `thread_id` = `session_id`.

## Human-in-the-loop (UC-MVP-03)

La tool `escalar_a_equipo` esta configurada en `HumanInTheLoopMiddleware` con `interrupt_on`:

- Antes de persistir la alerta, el grafo queda en estado `__interrupt__`.
- El endpoint `POST /chat` expone `requiere_revision_humana: true` cuando hay `__interrupt__`; staff puede reanudar con `continuar_despues_hitl`.

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
