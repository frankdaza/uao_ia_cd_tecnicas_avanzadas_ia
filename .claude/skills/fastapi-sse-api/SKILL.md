---
name: fastapi-sse-api
description: Backend HTTP con FastAPI + sse-starlette (agente M2, SSE). Usar al crear o modificar src/api/ o cuando se necesite agregar endpoints al backend.
---

# Backend HTTP: FastAPI + SSE

> Mantener el mismo contenido en `.cursor/skills/fastapi-sse-api/` y `.claude/skills/fastapi-sse-api/`.

Los endpoints legacy **`/api/qa`** y el singleton **`PipelineQa`** fueron **retirados**. El producto expone sesiones y el agente vía `src/api/main.py` y routers bajo `src/api/routers/` (`salud`, `sesiones`, `agente`, `admin` según evolución del repo).

## Instalacion de dependencias

```bash
uv add fastapi uvicorn[standard] sse-starlette pydantic-settings
uv lock
```

## Estructura de modulos (referencia)

```
src/api/
  main.py           # FastAPI app, lifespan, CORS, routers, estaticos
  configuracion.py  # pydantic-settings
  dependencias.py   # Depends (sesion DB, usuario, grafo, etc.)
  esquemas.py       # modelos Pydantic v2
  routers/
    salud.py
    sesiones.py
    agente.py
    admin.py
```

## SSE del agente (Modulo 2)

- Endpoint: **`POST /api/agente/stream`** con cuerpo JSON (`session_id`, `pregunta`, `primer_turno`, etc.).
- **Eventos**: `pensamiento`, `herramienta`, `token` (p. ej. `motor: "agente"`), `fuentes` (chunks Qdrant), `final`, `error`, y opcionalmente `keepalive`.
- **Serializacion**: cada `data` en JSON valido; Pydantic v2 con `model_dump(mode="json")` cuando aplique.
- **Cancelacion**: al cerrar el cliente, cancelar de forma cooperativa el async generator del grafo.
- **CORS y cookies**: sesion HTTP-only → `allow_credentials` y origenes explicitos (ver `react-vite-qa-ui`).
- Implementacion y pruebas: skill **`agente-modulo-2`**.

## Tests con httpx AsyncClient

```python
@pytest.fixture
async def async_client():
    app = crear_app()
    app.state.grafo_agente = MagicMock()  # o fixture dedicada del grafo
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
```

## Comando de ejecucion

```bash
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Referencia de reglas

- Convencion FastAPI: `.cursor/rules/api-fastapi.mdc`
- Agente M2: `.cursor/rules/agente-modulo-2.mdc`
