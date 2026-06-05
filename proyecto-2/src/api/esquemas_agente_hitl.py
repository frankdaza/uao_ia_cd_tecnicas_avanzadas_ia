"""Esquemas del HITL de escalamiento configurable desde panel admin."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AgenteHitlConfigVista(BaseModel):
    """Estado efectivo del HITL en ``escalar_a_equipo``."""

    habilitado: bool
    updated_at: datetime | None = None


class AgenteHitlConfigParche(BaseModel):
    """Actualizacion del HITL (hot-reload sin reiniciar el servidor)."""

    habilitado: bool
