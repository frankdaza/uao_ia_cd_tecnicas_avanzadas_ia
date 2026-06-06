"""Esquemas Pydantic del contrato ``POST /chat`` (canal externo, sin SSE)."""

from __future__ import annotations

import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.agentes.contexto import parsear_session_telegram
from src.agentes.tools.esquemas import SeveridadTriage

SeveridadTriageRespuesta = SeveridadTriage | None


class ChatMetadata(BaseModel):
    """Metadatos opcionales del integrador (Telegram, logs)."""

    canal: str | None = Field(
        default=None,
        description="Canal de origen, p. ej. telegram.",
        examples=["telegram"],
    )
    caso_id: uuid.UUID | None = Field(
        default=None,
        description="UUID del caso si el integrador ya lo conoce.",
    )
    update_id: int | None = Field(
        default=None,
        description="Identificador del update Telegram para correlacion en logs.",
        ge=1,
    )
    telegram_message_id: int | None = Field(
        default=None,
        description="message_id del mensaje Telegram (multimedia).",
        ge=1,
    )
    adjunto_ids: list[uuid.UUID] | None = Field(
        default=None,
        description="Adjuntos persistidos en el turno actual.",
    )


class ChatPeticion(BaseModel):
    """Cuerpo de ``POST /chat``."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "session_id": "telegram:123456789",
                    "mensaje": "¿Cuándo puedo retomar caminatas leves?",
                    "metadata": {
                        "canal": "telegram",
                        "update_id": 42,
                    },
                }
            ]
        }
    )

    session_id: str = Field(
        ...,
        min_length=8,
        description="Identificador de hilo; formato ``telegram:{chat_id}``.",
        examples=["telegram:123456789"],
    )
    mensaje: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="Texto del paciente.",
    )
    metadata: ChatMetadata | None = None

    @field_validator("session_id")
    @classmethod
    def validar_formato_session(cls, valor: str) -> str:
        if parsear_session_telegram(valor) is None:
            raise ValueError(
                "session_id debe tener el formato telegram:{chat_id} con chat_id numerico."
            )
        return valor.strip()

    @field_validator("mensaje")
    @classmethod
    def normalizar_mensaje(cls, valor: str) -> str:
        texto = valor.strip()
        if not texto:
            raise ValueError("mensaje no puede estar vacio.")
        return texto


class FuenteChat(BaseModel):
    """Fragmento de protocolo recuperado por RAG en el turno."""

    model_config = ConfigDict(frozen=True)

    titulo: str = Field(..., description="Titulo o etiqueta del fragmento.")
    fragmento: str = Field(..., description="Texto del chunk.")


class ChatRespuesta(BaseModel):
    """Respuesta JSON de un turno del agente TAAM."""

    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "examples": [
                {
                    "respuesta": (
                        "Segun su protocolo, puede retomar caminatas leves cuando "
                        "el equipo lo indique. Consulte ante dolor o sangrado."
                    ),
                    "severidad_triage": "info",
                    "requiere_revision_humana": False,
                    "fuentes": [
                        {
                            "titulo": "Protocolo [1]",
                            "fragmento": "Evitar esfuerzo intenso durante la primera semana.",
                        }
                    ],
                    "error": None,
                }
            ]
        },
    )

    respuesta: str
    severidad_triage: SeveridadTriageRespuesta = None
    requiere_revision_humana: bool = False
    fuentes: list[FuenteChat] = Field(default_factory=list)
    error: str | None = None
