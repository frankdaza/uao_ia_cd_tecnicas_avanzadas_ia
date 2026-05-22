"""Repositorio de idempotencia para updates Telegram."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import TelegramUpdateProcesado


class RepositorioTelegramUpdates:
    """Registra ``update_id`` procesados para evitar respuestas duplicadas."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def ya_procesado(self, update_id: int) -> bool:
        stmt = select(TelegramUpdateProcesado.update_id).where(
            TelegramUpdateProcesado.update_id == update_id
        )
        resultado = await self._sesion.execute(stmt)
        return resultado.scalar_one_or_none() is not None

    async def intentar_registrar(self, update_id: int) -> bool:
        """
        Inserta el update_id si es nuevo.

        Returns:
            True si este hilo debe procesar el update; False si ya existia.
        """
        if await self.ya_procesado(update_id):
            return False
        self._sesion.add(TelegramUpdateProcesado(update_id=update_id))
        try:
            await self._sesion.flush()
        except IntegrityError:
            await self._sesion.rollback()
            return False
        return True
