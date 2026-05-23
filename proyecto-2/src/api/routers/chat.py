"""Endpoint REST ``POST /chat`` para integradores externos (Telegram, etc.)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from langgraph.checkpoint.base import BaseCheckpointSaver
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.api.dependencias import obtener_checkpointer_app, obtener_session_factory_app
from src.api.esquemas_chat import ChatPeticion, ChatRespuesta
from src.api.servicios.chat import procesar_turno_chat

router = APIRouter(tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatRespuesta,
    summary="Turno conversacional del agente TAAM",
    description=(
        "Procesa un mensaje del paciente para la sesion ``telegram:{chat_id}`` "
        "vinculada a un caso activo. Respuesta JSON sin SSE."
    ),
    responses={
        403: {
            "description": "Sesion sin vinculo Telegram activo",
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "Su cuenta de Telegram no esta vinculada a un caso activo. "
                            "Use el codigo de emparejamiento que le entrego el equipo clinico."
                        )
                    }
                }
            },
        },
        503: {
            "description": "Timeout o fallo temporal del agente",
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "El asistente no respondio a tiempo. Por favor intente de nuevo "
                            "en unos minutos."
                        )
                    }
                }
            },
        },
    },
)
async def chat_turno(
    cuerpo: ChatPeticion,
    session_factory: Annotated[
        async_sessionmaker[AsyncSession],
        Depends(obtener_session_factory_app),
    ],
    checkpointer: Annotated[BaseCheckpointSaver, Depends(obtener_checkpointer_app)],
) -> ChatRespuesta:
    """Un turno del bot posoperatorio (contrato rubrica M3)."""
    return await procesar_turno_chat(
        peticion=cuerpo,
        session_factory=session_factory,
        checkpointer=checkpointer,
    )
