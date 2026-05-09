"""Proveedores de dependencias inyectables (FastAPI Depends)."""

from __future__ import annotations

from fastapi import Request

from src.qa.pipeline import PipelineQa


async def obtener_pipeline(request: Request) -> PipelineQa:
    """Retorna el PipelineQa singleton inicializado en el lifespan de la app."""
    return request.app.state.pipeline  # type: ignore[no-any-return]
