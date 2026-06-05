"""Rutas admin para registrar y consultar el webhook de Telegram."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as estado_http

from src.api.dependencias import requerir_acceso_admin
from src.api.esquemas_telegram_webhook_admin import (
    TelegramWebhookEstadoVista,
    TelegramWebhookRegistrarCuerpo,
    TelegramWebhookRegistrarRespuesta,
)
from src.integracion.telegram.configuracion_webhook import (
    TelegramApiRespuestaError,
    TelegramWebhookConfiguracionError,
    TelegramWebhookEstado,
    TelegramWebhookValidacionError,
    obtener_estado_webhook,
    registrar_webhook,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin-telegram-webhook"],
    dependencies=[Depends(requerir_acceso_admin)],
)


def _a_vista(estado: TelegramWebhookEstado) -> TelegramWebhookEstadoVista:
    return TelegramWebhookEstadoVista(
        url=estado.url,
        configurado=estado.configurado,
        pending_update_count=estado.pending_update_count,
        last_error_message=estado.last_error_message,
        last_error_date=estado.last_error_date,
    )


def _manejar_error_configuracion(exc: TelegramWebhookConfiguracionError) -> HTTPException:
    return HTTPException(
        status_code=estado_http.HTTP_503_SERVICE_UNAVAILABLE,
        detail=str(exc),
    )


def _manejar_error_validacion(exc: TelegramWebhookValidacionError) -> HTTPException:
    return HTTPException(
        status_code=estado_http.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=str(exc),
    )


def _manejar_error_telegram(exc: TelegramApiRespuestaError) -> HTTPException:
    return HTTPException(
        status_code=estado_http.HTTP_502_BAD_GATEWAY,
        detail=exc.datos,
    )


@router.get(
    "/telegram-webhook",
    response_model=TelegramWebhookEstadoVista,
    summary="Estado del webhook registrado en Telegram",
)
async def obtener_webhook_telegram_admin() -> TelegramWebhookEstadoVista:
    try:
        estado = await obtener_estado_webhook()
    except TelegramWebhookConfiguracionError as exc:
        raise _manejar_error_configuracion(exc) from exc
    except TelegramApiRespuestaError as exc:
        raise _manejar_error_telegram(exc) from exc
    return _a_vista(estado)


@router.post(
    "/telegram-webhook",
    response_model=TelegramWebhookRegistrarRespuesta,
    summary="Registrar URL del webhook en Telegram (setWebhook)",
)
async def registrar_webhook_telegram_admin(
    cuerpo: TelegramWebhookRegistrarCuerpo,
) -> TelegramWebhookRegistrarRespuesta:
    try:
        url = await registrar_webhook(
            cuerpo.url,
            drop_pending_updates=cuerpo.drop_pending_updates,
        )
    except TelegramWebhookConfiguracionError as exc:
        raise _manejar_error_configuracion(exc) from exc
    except TelegramWebhookValidacionError as exc:
        raise _manejar_error_validacion(exc) from exc
    except TelegramApiRespuestaError as exc:
        raise _manejar_error_telegram(exc) from exc
    return TelegramWebhookRegistrarRespuesta(url=url)
