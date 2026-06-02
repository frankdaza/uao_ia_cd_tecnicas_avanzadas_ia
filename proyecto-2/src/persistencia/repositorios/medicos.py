"""Repositorio del catalogo ``medicos``."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import CasoPostoperatorio, Medico


class RepositorioMedicos:
    """CRUD minimo sobre medicos/cirujanos."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def crear(
        self,
        *,
        codigo_registro: str,
        nombre_completo: str,
        especialidad: str | None = None,
        activo: bool = True,
    ) -> Medico:
        ahora = datetime.now(UTC)
        fila = Medico(
            codigo_registro=codigo_registro,
            nombre_completo=nombre_completo,
            especialidad=especialidad,
            activo=activo,
            created_at=ahora,
            updated_at=ahora,
        )
        self._sesion.add(fila)
        await self._sesion.flush()
        return fila

    async def obtener_por_id(self, medico_id: uuid.UUID) -> Medico | None:
        return await self._sesion.get(Medico, medico_id)

    async def obtener_por_codigo(self, codigo_registro: str) -> Medico | None:
        stmt = select(Medico).where(Medico.codigo_registro == codigo_registro)
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def listar(
        self,
        *,
        limite: int = 50,
        offset: int = 0,
        activo: bool | None = None,
    ) -> list[Medico]:
        stmt = select(Medico)
        if activo is not None:
            stmt = stmt.where(Medico.activo == activo)
        stmt = (
            stmt.order_by(Medico.created_at.desc(), Medico.id.asc())
            .offset(offset)
            .limit(limite)
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())

    async def contar(self, *, activo: bool | None = None) -> int:
        stmt = select(func.count()).select_from(Medico)
        if activo is not None:
            stmt = stmt.where(Medico.activo == activo)
        res = await self._sesion.execute(stmt)
        return int(res.scalar_one())

    async def actualizar(
        self,
        fila: Medico,
        *,
        codigo_registro: str | None = None,
        nombre_completo: str | None = None,
        especialidad: str | None = None,
        activo: bool | None = None,
    ) -> Medico:
        if codigo_registro is not None:
            fila.codigo_registro = codigo_registro
        if nombre_completo is not None:
            fila.nombre_completo = nombre_completo
        if especialidad is not None:
            fila.especialidad = especialidad
        if activo is not None:
            fila.activo = activo
        fila.updated_at = datetime.now(UTC)
        await self._sesion.flush()
        return fila

    async def existe_caso_activo_con_cirujano_id(self, codigo_registro: str) -> bool:
        stmt = (
            select(func.count())
            .select_from(CasoPostoperatorio)
            .where(
                CasoPostoperatorio.estado == "activo",
                CasoPostoperatorio.cirujano_id == codigo_registro,
            )
        )
        res = await self._sesion.execute(stmt)
        return int(res.scalar_one()) > 0
