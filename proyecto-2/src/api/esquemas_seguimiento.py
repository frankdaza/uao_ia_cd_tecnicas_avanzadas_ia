"""Esquemas Pydantic para panel de seguimiento staff (UC-MVP-05)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MarcarAlertaRevisadaCuerpo(BaseModel):
    """Solo admite marcar como revisada en MVP."""

    revisado: Literal[True] = True


class ReanudarHitlCuerpo(BaseModel):
    """Decision staff sobre escalamiento pendiente (HITL ``escalar_a_equipo``)."""

    decision: Literal["approve", "reject"] = Field(
        default="approve",
        description="approve ejecuta la tool y crea alerta; reject la descarta.",
    )


class ReanudarHitlRespuesta(BaseModel):
    caso_id: uuid.UUID
    session_id: str
    decision: Literal["approve", "reject"]
    requiere_revision_humana: bool = False
    reanudado: bool = Field(
        description="False si no habia interrupcion pendiente en el hilo.",
    )


class MensajeConversacionVista(BaseModel):
    """Mensaje humano o del asistente en el hilo Telegram."""

    rol: Literal["human", "assistant"]
    contenido: str
    indice: int = Field(ge=0, description="Orden de aparicion en el hilo")


class ConversacionCasoRespuesta(BaseModel):
    caso_id: uuid.UUID
    session_id: str
    telegram_chat_id_enmascarado: str | None = None
    mensajes: list[MensajeConversacionVista]


class AlertaTriageVista(BaseModel):
    id: uuid.UUID
    caso_id: uuid.UUID
    paciente_doc_id: str
    paciente_nombre: str
    severidad: str
    resumen: str
    mensaje_paciente_ref: str | None
    revisado: bool
    revisado_at: datetime | None
    revisado_staff_id: uuid.UUID | None
    created_at: datetime


class ListadoAlertasRespuesta(BaseModel):
    items: list[AlertaTriageVista]
    limit: int
    offset: int


class CasoResumenSeguimientoRespuesta(BaseModel):
    caso_id: uuid.UUID
    ultima_severidad: str | None = None
    ultima_alerta_resumen: str | None = None
    ultima_alerta_created_at: datetime | None = None
    conteo_mensajes: int = 0
    proximo_recordatorio_at: datetime | None = None
    proximo_recordatorio_estado: str | None = None
    telegram_chat_id_enmascarado: str | None = None
    vinculado_telegram: bool = False
