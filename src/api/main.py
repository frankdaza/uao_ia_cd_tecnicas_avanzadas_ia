"""
Entrypoint del backend FastAPI para el sistema Q&A Valle del Lili.

Inicialización:
    uv run uvicorn src.api.main:app --reload --port 8000
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.api.configuracion import obtener_configuracion
from src.api.middleware_request_id import registrar_request_response
from src.api.routers import corpus, qa, salud
from src.qa.pipeline import construir_pipeline_por_defecto

_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Inicializa el PipelineQa una sola vez al arrancar el servidor."""
    app.state.pipeline = construir_pipeline_por_defecto()
    yield
    # Limpieza al apagar (espacio para cerrar recursos si se agregan en el futuro)


def crear_app() -> FastAPI:
    """Fabrica la aplicación FastAPI con CORS y routers montados."""
    cfg = obtener_configuracion()

    app = FastAPI(
        title="Q&A Fundación Valle del Lili — API",
        description=(
            "Backend HTTP con FastAPI + SSE que expone el PipelineQa "
            "(BM25 + Ollama + OpenAI) al frontend React."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
    app.middleware("http")(registrar_request_response)

    app.include_router(salud.router, prefix="/api")
    app.include_router(corpus.router, prefix="/api")
    app.include_router(qa.router, prefix="/api")

    # Servir el frontend React como estáticos en producción
    if _FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")

    return app


app = crear_app()
