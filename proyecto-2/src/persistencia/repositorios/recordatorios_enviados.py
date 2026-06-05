"""Repositorio de ``recordatorios_enviados``."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import RecordatorioEnviado


class RepositorioRecordatoriosEnviados:
    """Programacion y trazabilidad de recordatorios."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def crear(
        self,
        *,
        caso_id: uuid.UUID,
        plantilla_id: uuid.UUID,
        programado_at: datetime,
        estado: str = "pendiente",
    ) -> RecordatorioEnviado:
        fila = RecordatorioEnviado(
            caso_id=caso_id,
            plantilla_id=plantilla_id,
            programado_at=programado_at,
            estado=estado,
        )
        self._sesion.add(fila)
        await self._sesion.flush()
        return fila

    async def obtener_por_id(
        self,
        recordatorio_id: uuid.UUID,
    ) -> RecordatorioEnviado | None:
        return await self._sesion.get(RecordatorioEnviado, recordatorio_id)

    async def listar_pendientes_vencidos(
        self,
        *,
        ahora: datetime,
        limite: int = 50,
    ) -> list[RecordatorioEnviado]:
        stmt = (
            select(RecordatorioEnviado)
            .where(
                RecordatorioEnviado.estado == "pendiente",
                RecordatorioEnviado.enviado_at.is_(None),
                RecordatorioEnviado.programado_at <= ahora,
            )
            .order_by(RecordatorioEnviado.programado_at.asc())
            .limit(limite)
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())

    async def obtener_siguiente_pendiente_caso(
        self,
        caso_id: uuid.UUID,
    ) -> RecordatorioEnviado | None:
        stmt = (
            select(RecordatorioEnviado)
            .where(
                RecordatorioEnviado.caso_id == caso_id,
                RecordatorioEnviado.estado == "pendiente",
                RecordatorioEnviado.enviado_at.is_(None),
            )
            .order_by(RecordatorioEnviado.programado_at.asc())
            .limit(1)
        )
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def listar_pendientes_sin_enviar(
        self,
        *,
        limite: int = 500,
    ) -> list[RecordatorioEnviado]:
        stmt = (
            select(RecordatorioEnviado)
            .where(
                RecordatorioEnviado.estado == "pendiente",
                RecordatorioEnviado.enviado_at.is_(None),
            )
            .order_by(RecordatorioEnviado.caso_id.asc(), RecordatorioEnviado.programado_at.asc())
            .limit(limite)
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())

    async def actualizar_programado_at(
        self,
        fila: RecordatorioEnviado,
        *,
        programado_at: datetime,
    ) -> RecordatorioEnviado:
        fila.programado_at = programado_at
        await self._sesion.flush()
        return fila

    async def marcar_enviado(
        self,
        fila: RecordatorioEnviado,
        *,
        enviado_at: datetime,
    ) -> RecordatorioEnviado:
        fila.estado = "enviado"
        fila.enviado_at = enviado_at
        await self._sesion.flush()
        return fila

    async def marcar_error(self, fila: RecordatorioEnviado) -> RecordatorioEnviado:
        fila.estado = "error"
        await self._sesion.flush()
        return fila

    async def contar_por_estado(self) -> dict[str, int]:
        stmt = select(RecordatorioEnviado.estado, func.count()).group_by(
            RecordatorioEnviado.estado
        )
        res = await self._sesion.execute(stmt)
        return {str(estado): int(cnt) for estado, cnt in res.all()}

    async def contar_pendientes_vencidos(self, *, ahora: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(RecordatorioEnviado)
            .where(
                RecordatorioEnviado.estado == "pendiente",
                RecordatorioEnviado.enviado_at.is_(None),
                RecordatorioEnviado.programado_at <= ahora,
            )
        )
        res = await self._sesion.execute(stmt)
        return int(res.scalar_one())

    async def contar_enviados_desde(self, desde: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(RecordatorioEnviado)
            .where(
                RecordatorioEnviado.estado == "enviado",
                RecordatorioEnviado.enviado_at.is_not(None),
                RecordatorioEnviado.enviado_at >= desde,
            )
        )
        res = await self._sesion.execute(stmt)
        return int(res.scalar_one())
