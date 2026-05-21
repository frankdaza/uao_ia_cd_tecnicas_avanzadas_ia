"""Repositorio de ``vinculos_telegram``."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import VinculoTelegram


class RepositorioVinculosTelegram:
    """CRUD minimo de emparejamiento Telegram."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def crear(
        self,
        *,
        caso_id: uuid.UUID,
        telegram_chat_id: int,
        codigo_emparejamiento: str | None = None,
        codigo_expira_at: datetime | None = None,
        vinculado_at: datetime | None = None,
    ) -> VinculoTelegram:
        fila = VinculoTelegram(
            caso_id=caso_id,
            telegram_chat_id=telegram_chat_id,
            codigo_emparejamiento=codigo_emparejamiento,
            codigo_expira_at=codigo_expira_at,
            vinculado_at=vinculado_at,
        )
        self._sesion.add(fila)
        await self._sesion.flush()
        return fila

    async def obtener_por_chat_id(self, telegram_chat_id: int) -> VinculoTelegram | None:
        stmt = select(VinculoTelegram).where(
            VinculoTelegram.telegram_chat_id == telegram_chat_id
        )
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def listar_por_caso(self, caso_id: uuid.UUID) -> list[VinculoTelegram]:
        stmt = (
            select(VinculoTelegram)
            .where(VinculoTelegram.caso_id == caso_id)
            .order_by(VinculoTelegram.vinculado_at.desc().nullslast())
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())
