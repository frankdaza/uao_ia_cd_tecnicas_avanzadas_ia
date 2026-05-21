"""
Entrypoint del backend FastAPI para TAAM (proyecto-2).

Desarrollo local:
    uv run uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8001
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers import salud
from src.configuracion import obtener_configuracion

app = FastAPI(
    title="TAAM API",
    description="Bot posoperatorio — Modulo 3 (scaffold)",
    version="0.1.0",
)

cfg = obtener_configuracion()
app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(salud.router, prefix="/api")
