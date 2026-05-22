"""Repositorio de ``casos_postoperatorio``."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import CasoPostoperatorio


class RepositorioCasosPostoperatorio:
    """CRUD minimo sobre casos quirurgicos."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def crear(
        self,
        *,
        paciente_doc_id: str,
        paciente_nombre: str,
        tipo_procedimiento_id: uuid.UUID,
        cirujano_id: str,
        cirujano_nombre: str,
        fecha_cirugia: date,
        notas_especificas: str | None = None,
        estado: str = "activo",
    ) -> CasoPostoperatorio:
        fila = CasoPostoperatorio(
            paciente_doc_id=paciente_doc_id,
            paciente_nombre=paciente_nombre,
            tipo_procedimiento_id=tipo_procedimiento_id,
            cirujano_id=cirujano_id,
            cirujano_nombre=cirujano_nombre,
            fecha_cirugia=fecha_cirugia,
            notas_especificas=notas_especificas,
            estado=estado,
        )
        self._sesion.add(fila)
        await self._sesion.flush()
        return fila

    async def obtener_por_id(self, caso_id: uuid.UUID) -> CasoPostoperatorio | None:
        return await self._sesion.get(CasoPostoperatorio, caso_id)

    async def obtener_activo_por_doc_id(
        self,
        paciente_doc_id: str,
    ) -> CasoPostoperatorio | None:
        stmt = (
            select(CasoPostoperatorio)
            .where(
                CasoPostoperatorio.paciente_doc_id == paciente_doc_id,
                CasoPostoperatorio.estado == "activo",
            )
            .order_by(CasoPostoperatorio.created_at.desc(), CasoPostoperatorio.id.asc())
            .limit(1)
        )
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def listar(
        self,
        *,
        estado: str | None = None,
        limite: int = 50,
        offset: int = 0,
    ) -> list[CasoPostoperatorio]:
        stmt = select(CasoPostoperatorio)
        if estado is not None:
            stmt = stmt.where(CasoPostoperatorio.estado == estado)
        stmt = (
            stmt.order_by(
                CasoPostoperatorio.created_at.desc(),
                CasoPostoperatorio.id.asc(),
            )
            .offset(offset)
            .limit(limite)
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())
