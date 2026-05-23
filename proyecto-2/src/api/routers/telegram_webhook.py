"""Webhook Telegram (via 2 M3): POST /api/integracion/telegram/webhook."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from langgraph.checkpoint.base import BaseCheckpointSaver
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.api.dependencias import (
    obtener_checkpointer_app,
    obtener_session_factory_app,
    requerir_secreto_telegram,
)
from src.integracion.telegram.esquemas import TelegramUpdate
from src.integracion.telegram.manejador import procesar_update_telegram

router = APIRouter(
    prefix="/integracion/telegram",
    tags=["telegram-webhook"],
    dependencies=[Depends(requerir_secreto_telegram)],
)


class WebhookTelegramRespuesta(BaseModel):
    """Respuesta minima esperada por Telegram tras recibir un update."""

    ok: bool = True


@router.post(
    "/webhook",
    response_model=WebhookTelegramRespuesta,
    summary="Webhook de updates Telegram",
    description=(
        "Recibe updates del Bot API, valida el secret, procesa mensajes de texto "
        "y responde al paciente via sendMessage. Ruta canónica M3 (decision-7)."
    ),
)
async def webhook_telegram(
    update: TelegramUpdate,
    session_factory: Annotated[
        async_sessionmaker[AsyncSession],
        Depends(obtener_session_factory_app),
    ],
    checkpointer: Annotated[BaseCheckpointSaver, Depends(obtener_checkpointer_app)],
) -> WebhookTelegramRespuesta:
    await procesar_update_telegram(
        update,
        session_factory=session_factory,
        checkpointer=checkpointer,
    )
    return WebhookTelegramRespuesta()
