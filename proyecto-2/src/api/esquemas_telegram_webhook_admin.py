"""Esquemas admin para registrar y consultar el webhook de Telegram."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TelegramWebhookEstadoVista(BaseModel):
    """Estado del webhook segun getWebhookInfo."""

    url: str = ""
    configurado: bool = False
    pending_update_count: int = Field(ge=0, default=0)
    last_error_message: str | None = None
    last_error_date: int | None = Field(
        default=None,
        description="Unix timestamp del ultimo error de entrega (Bot API).",
    )


class TelegramWebhookRegistrarCuerpo(BaseModel):
    """Cuerpo para setWebhook desde el panel admin."""

    url: str = Field(
        min_length=1,
        description="URL publica HTTPS que termina en /api/integracion/telegram/webhook",
    )
    drop_pending_updates: bool = False


class TelegramWebhookRegistrarRespuesta(BaseModel):
    """Confirmacion tras registrar el webhook."""

    ok: bool = True
    url: str
