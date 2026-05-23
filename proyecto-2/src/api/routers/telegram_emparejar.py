"""Emparejamiento paciente Telegram (UC-MVP-02, invocado por webhook)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencias import requerir_secreto_telegram
from src.api.esquemas_casos import (
    EmparejarTelegramCuerpo,
    EmparejarTelegramRespuesta,
    ErrorEmparejamientoRespuesta,
)
from src.api.servicios.emparejamiento import EmparejamientoError, emparejar_codigo
from src.persistencia.motor import obtener_sesion_db

router = APIRouter(
    prefix="/telegram",
    tags=["telegram-emparejamiento"],
    dependencies=[Depends(requerir_secreto_telegram)],
)


@router.post(
    "/emparejar",
    response_model=EmparejarTelegramRespuesta,
    responses={
        400: {"model": ErrorEmparejamientoRespuesta},
        409: {"model": ErrorEmparejamientoRespuesta},
    },
)
async def emparejar_telegram(
    cuerpo: EmparejarTelegramCuerpo,
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
) -> EmparejarTelegramRespuesta | JSONResponse:
    try:
        resultado = await emparejar_codigo(
            sesion,
            codigo=cuerpo.codigo,
            telegram_chat_id=cuerpo.telegram_chat_id,
        )
    except EmparejamientoError as exc:
        cuerpo_error = ErrorEmparejamientoRespuesta(
            error=exc.codigo_error,
            mensaje_telegram=exc.mensaje_telegram,
        )
        return JSONResponse(
            status_code=exc.status_http,
            content=cuerpo_error.model_dump(),
        )

    return EmparejarTelegramRespuesta(
        caso_id=resultado.caso_id,
        vinculado_at=resultado.vinculado_at,
        mensaje_confirmacion=resultado.mensaje_confirmacion,
    )
