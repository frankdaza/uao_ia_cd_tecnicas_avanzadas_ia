"""Repositorio de ``alertas_triage``."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import AlertaTriage


class RepositorioAlertasTriage:
    """CRUD minimo de alertas para el panel staff."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def crear(
        self,
        *,
        caso_id: uuid.UUID,
        severidad: str,
        resumen: str,
        mensaje_paciente_ref: str | None = None,
        tool_trace_json: dict[str, Any] | None = None,
    ) -> AlertaTriage:
        fila = AlertaTriage(
            caso_id=caso_id,
            severidad=severidad,
            resumen=resumen,
            mensaje_paciente_ref=mensaje_paciente_ref,
            tool_trace_json=tool_trace_json,
        )
        self._sesion.add(fila)
        await self._sesion.flush()
        return fila

    async def obtener_por_id(self, alerta_id: uuid.UUID) -> AlertaTriage | None:
        return await self._sesion.get(AlertaTriage, alerta_id)

    async def listar(
        self,
        *,
        revisado: bool | None = None,
        severidad: str | None = None,
        limite: int = 50,
        offset: int = 0,
    ) -> list[AlertaTriage]:
        stmt = select(AlertaTriage)
        if revisado is not None:
            stmt = stmt.where(AlertaTriage.revisado == revisado)
        if severidad is not None:
            stmt = stmt.where(AlertaTriage.severidad == severidad)
        stmt = (
            stmt.order_by(AlertaTriage.created_at.desc(), AlertaTriage.id.asc())
            .offset(offset)
            .limit(limite)
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())
