"""Subset Pydantic del Bot API de Telegram para el webhook."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TelegramUsuario(BaseModel):
    id: int
    is_bot: bool | None = None
    first_name: str | None = None
    username: str | None = None


class TelegramChat(BaseModel):
    id: int
    type: str | None = None


class TelegramMensaje(BaseModel):
    message_id: int
    date: int | None = None
    chat: TelegramChat
    text: str | None = None
    from_: TelegramUsuario | None = Field(default=None, alias="from")


class TelegramUpdate(BaseModel):
    update_id: int = Field(..., ge=1)
    message: TelegramMensaje | None = None
