"""Repositorio de adjuntos multimedia de mensajes Telegram."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import AdjuntoMensaje, AlertaAdjunto


class RepositorioAdjuntosMensaje:
    """CRUD de archivos multimedia asociados a casos."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def crear(
        self,
        *,
        caso_id: uuid.UUID,
        telegram_message_id: int,
        telegram_file_id: str,
        tipo: str,
        mime_type: str,
        tamano_bytes: int,
        ruta_relativa: str,
        indice_hilo: int,
        caption: str | None = None,
        adjunto_id: uuid.UUID | None = None,
    ) -> AdjuntoMensaje:
        fila = AdjuntoMensaje(
            id=adjunto_id or uuid.uuid4(),
            caso_id=caso_id,
            telegram_message_id=telegram_message_id,
            telegram_file_id=telegram_file_id,
            tipo=tipo,
            mime_type=mime_type,
            tamano_bytes=tamano_bytes,
            ruta_relativa=ruta_relativa,
            caption=caption,
            indice_hilo=indice_hilo,
        )
        self._sesion.add(fila)
        await self._sesion.flush()
        return fila

    async def obtener_por_id(self, adjunto_id: uuid.UUID) -> AdjuntoMensaje | None:
        return await self._sesion.get(AdjuntoMensaje, adjunto_id)

    async def listar_por_caso(self, caso_id: uuid.UUID) -> list[AdjuntoMensaje]:
        stmt = (
            select(AdjuntoMensaje)
            .where(AdjuntoMensaje.caso_id == caso_id)
            .order_by(AdjuntoMensaje.indice_hilo.asc(), AdjuntoMensaje.created_at.asc())
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())

    async def listar_por_caso_e_indice(
        self,
        caso_id: uuid.UUID,
        indice_hilo: int,
    ) -> list[AdjuntoMensaje]:
        stmt = (
            select(AdjuntoMensaje)
            .where(
                AdjuntoMensaje.caso_id == caso_id,
                AdjuntoMensaje.indice_hilo == indice_hilo,
            )
            .order_by(AdjuntoMensaje.created_at.asc())
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())

    async def listar_por_alerta(self, alerta_id: uuid.UUID) -> list[AdjuntoMensaje]:
        stmt = (
            select(AdjuntoMensaje)
            .join(AlertaAdjunto, AlertaAdjunto.adjunto_id == AdjuntoMensaje.id)
            .where(AlertaAdjunto.alerta_id == alerta_id)
            .order_by(AdjuntoMensaje.created_at.asc())
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())

    async def listar_por_alertas(self, alerta_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[AdjuntoMensaje]]:
        if not alerta_ids:
            return {}
        stmt = (
            select(AlertaAdjunto.alerta_id, AdjuntoMensaje)
            .join(AdjuntoMensaje, AdjuntoMensaje.id == AlertaAdjunto.adjunto_id)
            .where(AlertaAdjunto.alerta_id.in_(alerta_ids))
            .order_by(AdjuntoMensaje.created_at.asc())
        )
        res = await self._sesion.execute(stmt)
        agrupado: dict[uuid.UUID, list[AdjuntoMensaje]] = {aid: [] for aid in alerta_ids}
        for alerta_id, adjunto in res.all():
            agrupado[alerta_id].append(adjunto)
        return agrupado

    async def vincular_a_alerta(
        self,
        alerta_id: uuid.UUID,
        adjunto_ids: list[uuid.UUID],
    ) -> None:
        for adjunto_id in adjunto_ids:
            self._sesion.add(
                AlertaAdjunto(alerta_id=alerta_id, adjunto_id=adjunto_id),
            )
        await self._sesion.flush()

    async def existe_por_file_id(
        self,
        caso_id: uuid.UUID,
        telegram_file_id: str,
    ) -> AdjuntoMensaje | None:
        stmt = (
            select(AdjuntoMensaje)
            .where(
                AdjuntoMensaje.caso_id == caso_id,
                AdjuntoMensaje.telegram_file_id == telegram_file_id,
            )
            .limit(1)
        )
        res = await self._sesion.execute(stmt)
        return res.scalars().first()
