"""Repositorio de ``plantillas_recordatorio``."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import PlantillaRecordatorio


class RepositorioPlantillasRecordatorio:
    """Consultas sobre plantillas por tipo de procedimiento."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def crear(
        self,
        *,
        tipo_procedimiento_id: uuid.UUID,
        tipo: str,
        offset_horas_desde_cirugia: int,
        texto_plantilla: str,
    ) -> PlantillaRecordatorio:
        fila = PlantillaRecordatorio(
            tipo_procedimiento_id=tipo_procedimiento_id,
            tipo=tipo,
            offset_horas_desde_cirugia=offset_horas_desde_cirugia,
            texto_plantilla=texto_plantilla,
        )
        self._sesion.add(fila)
        await self._sesion.flush()
        return fila

    async def obtener_por_id(
        self,
        plantilla_id: uuid.UUID,
    ) -> PlantillaRecordatorio | None:
        return await self._sesion.get(PlantillaRecordatorio, plantilla_id)

    async def listar_por_tipo(
        self,
        tipo_procedimiento_id: uuid.UUID,
    ) -> list[PlantillaRecordatorio]:
        stmt = (
            select(PlantillaRecordatorio)
            .where(PlantillaRecordatorio.tipo_procedimiento_id == tipo_procedimiento_id)
            .order_by(PlantillaRecordatorio.offset_horas_desde_cirugia.asc())
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())
