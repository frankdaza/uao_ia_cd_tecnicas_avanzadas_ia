"""Repositorio de ``alertas_triage``."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import AlertaTriage

_ORDEN_SEVERIDAD = case(
    (AlertaTriage.severidad == "urgente", 0),
    (AlertaTriage.severidad == "seguimiento", 1),
    else_=2,
)


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
        caso_id: uuid.UUID | None = None,
        limite: int = 50,
        offset: int = 0,
    ) -> list[AlertaTriage]:
        stmt = select(AlertaTriage)
        if revisado is not None:
            stmt = stmt.where(AlertaTriage.revisado == revisado)
        if severidad is not None:
            stmt = stmt.where(AlertaTriage.severidad == severidad)
        if caso_id is not None:
            stmt = stmt.where(AlertaTriage.caso_id == caso_id)
        stmt = (
            stmt.order_by(
                _ORDEN_SEVERIDAD.asc(),
                AlertaTriage.created_at.desc(),
                AlertaTriage.id.asc(),
            )
            .offset(offset)
            .limit(limite)
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())

    async def obtener_ultima_por_caso(self, caso_id: uuid.UUID) -> AlertaTriage | None:
        stmt = (
            select(AlertaTriage)
            .where(AlertaTriage.caso_id == caso_id)
            .order_by(AlertaTriage.created_at.desc(), AlertaTriage.id.asc())
            .limit(1)
        )
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def marcar_revisado(
        self,
        fila: AlertaTriage,
        *,
        staff_id: uuid.UUID,
        revisado_at: datetime,
    ) -> AlertaTriage:
        """Idempotente: no sobrescribe auditoria si ya estaba revisada."""
        if not fila.revisado:
            fila.revisado = True
            fila.revisado_at = revisado_at
            fila.revisado_staff_id = staff_id
        await self._sesion.flush()
        return fila

    async def contar_por_severidad(self, *, revisado: bool | None = None) -> dict[str, int]:
        stmt = select(AlertaTriage.severidad, func.count()).group_by(AlertaTriage.severidad)
        if revisado is not None:
            stmt = stmt.where(AlertaTriage.revisado == revisado)
        res = await self._sesion.execute(stmt)
        return {str(sev): int(cnt) for sev, cnt in res.all()}

    async def contar_revisadas_desde(self, desde: datetime) -> int:
        stmt = (
            select(func.count())
            .select_from(AlertaTriage)
            .where(
                AlertaTriage.revisado.is_(True),
                AlertaTriage.revisado_at.is_not(None),
                AlertaTriage.revisado_at >= desde,
            )
        )
        res = await self._sesion.execute(stmt)
        return int(res.scalar_one())

    async def serie_creadas_por_dia(self, *, dias: int) -> list[tuple[date, int]]:
        """Cuenta alertas creadas agrupadas por dia calendario."""
        if dias < 1:
            return []
        stmt = (
            select(func.date(AlertaTriage.created_at), func.count())
            .group_by(func.date(AlertaTriage.created_at))
            .order_by(func.date(AlertaTriage.created_at).asc())
        )
        res = await self._sesion.execute(stmt)
        filas: list[tuple[date, int]] = []
        for dia_raw, cnt in res.all():
            if isinstance(dia_raw, str):
                filas.append((date.fromisoformat(dia_raw), int(cnt)))
            else:
                filas.append((dia_raw, int(cnt)))
        return filas[-dias:] if len(filas) > dias else filas
