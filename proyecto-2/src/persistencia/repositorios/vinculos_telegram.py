"""Repositorio de ``vinculos_telegram``."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
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

    async def obtener_pendiente_por_caso(self, caso_id: uuid.UUID) -> VinculoTelegram | None:
        stmt = (
            select(VinculoTelegram)
            .where(
                VinculoTelegram.caso_id == caso_id,
                VinculoTelegram.vinculado_at.is_(None),
                VinculoTelegram.desvinculado_at.is_(None),
            )
            .limit(1)
        )
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def obtener_vinculado_por_caso(self, caso_id: uuid.UUID) -> VinculoTelegram | None:
        stmt = (
            select(VinculoTelegram)
            .where(
                VinculoTelegram.caso_id == caso_id,
                VinculoTelegram.vinculado_at.is_not(None),
                VinculoTelegram.desvinculado_at.is_(None),
            )
            .limit(1)
        )
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def obtener_ultimo_hilo_telegram_por_caso(
        self,
        caso_id: uuid.UUID,
    ) -> VinculoTelegram | None:
        """Ultimo vinculo con chat real (activo o desvinculado) para historial staff."""
        stmt = (
            select(VinculoTelegram)
            .where(
                VinculoTelegram.caso_id == caso_id,
                VinculoTelegram.vinculado_at.is_not(None),
            )
            .order_by(VinculoTelegram.vinculado_at.desc())
            .limit(1)
        )
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def obtener_pendiente_por_codigo(self, codigo: str) -> VinculoTelegram | None:
        stmt = (
            select(VinculoTelegram)
            .where(
                VinculoTelegram.codigo_emparejamiento == codigo,
                VinculoTelegram.vinculado_at.is_(None),
                VinculoTelegram.desvinculado_at.is_(None),
            )
            .limit(1)
        )
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def obtener_vinculado_por_chat_id(
        self,
        telegram_chat_id: int,
    ) -> VinculoTelegram | None:
        stmt = (
            select(VinculoTelegram)
            .where(
                VinculoTelegram.telegram_chat_id == telegram_chat_id,
                VinculoTelegram.vinculado_at.is_not(None),
                VinculoTelegram.desvinculado_at.is_(None),
            )
            .limit(1)
        )
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def actualizar(
        self,
        fila: VinculoTelegram,
        *,
        telegram_chat_id: int | None = None,
        codigo_emparejamiento: str | None = None,
        codigo_expira_at: datetime | None = None,
        vinculado_at: datetime | None = None,
        desvinculado_at: datetime | None = None,
        limpiar_codigo: bool = False,
    ) -> VinculoTelegram:
        if telegram_chat_id is not None:
            fila.telegram_chat_id = telegram_chat_id
        if limpiar_codigo:
            fila.codigo_emparejamiento = None
            fila.codigo_expira_at = None
        else:
            if codigo_emparejamiento is not None:
                fila.codigo_emparejamiento = codigo_emparejamiento
            if codigo_expira_at is not None:
                fila.codigo_expira_at = codigo_expira_at
        if vinculado_at is not None:
            fila.vinculado_at = vinculado_at
        if desvinculado_at is not None:
            fila.desvinculado_at = desvinculado_at
        await self._sesion.flush()
        return fila

    async def contar_activos(self) -> int:
        stmt = (
            select(func.count())
            .select_from(VinculoTelegram)
            .where(
                VinculoTelegram.vinculado_at.is_not(None),
                VinculoTelegram.desvinculado_at.is_(None),
            )
        )
        res = await self._sesion.execute(stmt)
        return int(res.scalar_one())
