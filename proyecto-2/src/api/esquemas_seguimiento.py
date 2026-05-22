"""Esquemas Pydantic para panel de seguimiento staff (UC-MVP-05)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MarcarAlertaRevisadaCuerpo(BaseModel):
    """Solo admite marcar como revisada en MVP."""

    revisado: Literal[True] = True


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
