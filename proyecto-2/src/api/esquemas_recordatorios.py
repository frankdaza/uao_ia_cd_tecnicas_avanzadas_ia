"""Esquemas Pydantic para recordatorios (UC-MVP-04)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class DisparoRecordatorioRespuesta(BaseModel):
    """Resultado de ``POST .../disparar-recordatorio-prueba``."""

    recordatorio_id: uuid.UUID | None = None
    enviado: bool
    mensaje: str | None = None
    motivo_omitido: str | None = Field(
        default=None,
        description=(
            "sin_vinculo_telegram, chat_demo_ficticio, sin_recordatorios_pendientes, "
            "caso_inexistente, error_telegram, etc."
        ),
    )
