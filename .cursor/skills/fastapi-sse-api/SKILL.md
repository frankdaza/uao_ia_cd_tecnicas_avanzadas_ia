---
name: fastapi-sse-api
description: Implementa el backend HTTP con FastAPI + sse-starlette (M1 PipelineQa y M2 agente SSE). Usar al crear o modificar src/api/ o cuando se necesite agregar endpoints al backend.
---

# Backend HTTP: FastAPI + SSE

> Mantener el mismo contenido en `.cursor/skills/fastapi-sse-api/` y `.claude/skills/fastapi-sse-api/`.

## Instalacion de dependencias

```bash
uv add fastapi uvicorn[standard] sse-starlette pydantic-settings
uv lock
```

## Estructura de modulos

```
src/api/
  __init__.py
  main.py           # FastAPI app, lifespan, CORS, routers
  configuracion.py  # pydantic-settings Settings
  dependencias.py   # Depends(obtener_pipeline)
  esquemas.py       # modelos Pydantic v2
  routers/
    __init__.py
    salud.py        # GET /api/salud
    qa.py           # M1: POST /api/qa, /api/qa/stream (legacy si se retira)
    sesiones.py     # M2: sesion e historial
    agente.py       # M2: POST /api/agente/stream
    corpus.py       # GET /api/modelos, POST /api/recargar-corpus, GET /api/prompt-defecto
```

## main.py: app con lifespan y CORS

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.configuracion import obtener_configuracion
from src.api.routers import salud, qa, corpus
from src.qa.pipeline import construir_pipeline_por_defecto

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Inicializa PipelineQa una sola vez al arrancar."""
    cfg = obtener_configuracion()
    app.state.pipeline = construir_pipeline_por_defecto()
    yield

def crear_app() -> FastAPI:
    cfg = obtener_configuracion()
    app = FastAPI(title="Q&A Valle del Lili API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(salud.router, prefix="/api")
    app.include_router(qa.router, prefix="/api")
    app.include_router(corpus.router, prefix="/api")
    return app

app = crear_app()
```

## configuracion.py: pydantic-settings

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    api_port: int = 8000
    ollama_base_url: str = "http://localhost:11434"
    openai_api_key: str | None = None

@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
```

## dependencias.py: inyeccion del pipeline

```python
from fastapi import Request
from src.qa.pipeline import PipelineQa

async def obtener_pipeline(request: Request) -> PipelineQa:
    """Retorna el PipelineQa singleton inicializado en el lifespan."""
    return request.app.state.pipeline
```

## Endpoints SSE con sse-starlette

```python
import asyncio
import json
from sse_starlette.sse import EventSourceResponse
from fastapi import APIRouter, Depends

router = APIRouter()

async def _generar_stream_ollama(pipeline: PipelineQa, peticion: PeticionQa):
    """Envuelve el generador sincrono en un generador asincrono."""
    def _iter():
        for parcial, final in pipeline.responder_stream(
            pregunta=peticion.pregunta,
            modelo=peticion.modelo_ollama,
            prompt_sistema=peticion.prompt_sistema or PROMPT_SISTEMA_DEFECTO,
        ):
            if final is None:
                yield {"event": "token", "data": json.dumps({"tipo": "token", "motor": "ollama", "texto": parcial})}
            else:
                yield {"event": "final", "data": json.dumps({"tipo": "final", "motor": "ollama", "texto": final.texto, "latencia_ms": final.latencia_ms})}
                yield {"event": "fuentes", "data": json.dumps({"tipo": "fuentes", "fuentes": [_serializar_fuente(f) for f in final.fuentes_bm25]})}

    for evento in await asyncio.to_thread(lambda: list(_iter())):
        yield evento

@router.post("/qa/stream")
async def qa_stream(peticion: PeticionQa, pipeline: PipelineQa = Depends(obtener_pipeline)):
    """Streaming SSE: Ollama o OpenAI segun peticion."""
    return EventSourceResponse(_generar_stream_ollama(pipeline, peticion))
```

## Manejo de errores en endpoints normales

```python
from fastapi import HTTPException
from src.qa.cliente_ollama import OllamaNoAccesibleError, ModeloNoDisponibleError

@router.post("/qa")
async def qa_sincrono(peticion: PeticionQa, pipeline: PipelineQa = Depends(obtener_pipeline)):
    try:
        resultado = pipeline.responder(
            pregunta=peticion.pregunta,
            modelo=peticion.modelo_ollama,
            prompt_sistema=peticion.prompt_sistema,
        )
        return RespuestaQa(texto=resultado.texto, fuentes=_serializar_fuentes(resultado.fuentes_bm25))
    except OllamaNoAccesibleError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ModeloNoDisponibleError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
```

## Manejo de errores en endpoints SSE

En SSE la conexion ya esta abierta; emitir evento `error` en lugar de lanzar excepcion HTTP:

```python
async def _generar_con_manejo_errores(pipeline, peticion):
    try:
        async for evento in _generar_stream_ollama(pipeline, peticion):
            yield evento
    except OllamaNoAccesibleError as exc:
        yield {"event": "error", "data": json.dumps({"tipo": "error", "mensaje": str(exc)})}
```

## Tests con httpx AsyncClient

```python
# tests/api/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock
from src.api.main import crear_app

@pytest.fixture
async def async_client():
    app = crear_app()
    app.state.pipeline = MagicMock()  # mock del pipeline
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

# tests/api/test_salud.py
async def test_salud(async_client):
    response = await async_client.get("/api/salud")
    assert response.status_code == 200
    assert response.json()["estado"] == "ok"
```

## Comando de ejecucion

```bash
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Variables de entorno relevantes

Ver `.env.example`; las nuevas variables del backend son:
- `ALLOWED_ORIGINS`: lista JSON de origenes CORS, ej. `["http://localhost:5173"]`
- `API_PORT`: puerto del servidor (defecto `8000`)

## SSE del agente (Modulo 2)

- Endpoint tipico: **`POST /api/agente/stream`** con cuerpo JSON (p. ej. `session_id`, `pregunta`, `primer_turno` opcional).
- **Eventos** (nombres de campo `event` en SSE, alineados con `esquemas.py`): incluir entre otros `pensamiento`, `herramienta`, `token` (p. ej. `motor: "agente"`), `fuentes` (metadata Qdrant), `final`, `error`, y opcionalmente `keepalive`.
- **Serializacion**: cada `data` debe ser JSON valido; preferir modelos Pydantic v2 + `model_dump(mode="json")` para tipos no JSON nativos.
- **Pruebas**: `httpx.AsyncClient` leyendo el cuerpo como texto, acumulando buffer y parseando lineas `event:` / `data:`; mockear el grafo LangChain/LangGraph en `app.state` para no llamar APIs reales.
- **Cancelacion**: al cancelar el cliente, propagar cancelacion al async generator del grafo (no dejar tareas huerfanas).
- **CORS y cookies**: si la sesion usa cookie HTTP-only, configurar `allow_credentials` y origenes explicitos (coordinar con `react-vite-qa-ui`).
- Detalle de arquitectura agente: skill **`agente-modulo-2`**.

## Referencia de reglas

- Convencion FastAPI: `.cursor/rules/api-fastapi.mdc`
- Agente M2 (globs acotados): `.cursor/rules/agente-modulo-2.mdc`
- Idioma: `.cursor/rules/language-conventions.mdc`
