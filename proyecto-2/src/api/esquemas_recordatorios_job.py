"""Esquemas del job de recordatorios configurable desde panel admin."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RecordatoriosJobConfigVista(BaseModel):
    """Estado efectivo del job periodico de recordatorios Telegram."""

    habilitado: bool
    interval_seg: int = Field(ge=5, le=3600)
    updated_at: datetime | None = None


class RecordatoriosJobConfigParche(BaseModel):
    """Actualizacion parcial del job (hot-reload sin reiniciar el servidor)."""

    habilitado: bool | None = None
    interval_seg: int | None = Field(default=None, ge=5, le=3600)
