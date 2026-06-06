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


class TelegramPhotoSize(BaseModel):
    file_id: str
    file_unique_id: str | None = None
    width: int | None = None
    height: int | None = None
    file_size: int | None = None


class TelegramVideo(BaseModel):
    file_id: str
    file_unique_id: str | None = None
    width: int | None = None
    height: int | None = None
    duration: int | None = None
    mime_type: str | None = None
    file_size: int | None = None


class TelegramVoice(BaseModel):
    file_id: str
    file_unique_id: str | None = None
    duration: int | None = None
    mime_type: str | None = None
    file_size: int | None = None


class TelegramAudio(BaseModel):
    file_id: str
    file_unique_id: str | None = None
    duration: int | None = None
    mime_type: str | None = None
    file_name: str | None = None
    file_size: int | None = None


class TelegramDocument(BaseModel):
    file_id: str
    file_unique_id: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    file_size: int | None = None


class TelegramMensaje(BaseModel):
    message_id: int
    date: int | None = None
    chat: TelegramChat
    text: str | None = None
    caption: str | None = None
    photo: list[TelegramPhotoSize] | None = None
    video: TelegramVideo | None = None
    voice: TelegramVoice | None = None
    audio: TelegramAudio | None = None
    document: TelegramDocument | None = None
    from_: TelegramUsuario | None = Field(default=None, alias="from")


class TelegramUpdate(BaseModel):
    update_id: int = Field(..., ge=1)
    message: TelegramMensaje | None = None
