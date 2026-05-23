"""Modelos Pydantic v2 para requests y responses del API TAAM."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RespuestaSalud(BaseModel):
    """Estado de salud del servidor TAAM."""

    model_config = ConfigDict(frozen=True)

    estado: str = "ok"
    version: str = "0.1.0"
    proyecto: str = Field(
        default="taam",
        description="Identificador del ejecutable (proyecto-2).",
    )
