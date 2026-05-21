"""Repositorio del catalogo ``tipos_procedimiento``."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import TipoProcedimiento


class RepositorioTiposProcedimiento:
    """CRUD minimo sobre procedimientos quirurgicos."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def crear(
        self,
        *,
        codigo: str,
        nombre: str,
        ruta_pdf: str | None = None,
        hash_pdf: str | None = None,
        indexacion_estado: str = "pendiente",
        qdrant_collection_version: int | None = None,
    ) -> TipoProcedimiento:
        fila = TipoProcedimiento(
            codigo=codigo,
            nombre=nombre,
            ruta_pdf=ruta_pdf,
            hash_pdf=hash_pdf,
            indexacion_estado=indexacion_estado,
            qdrant_collection_version=qdrant_collection_version,
        )
        self._sesion.add(fila)
        await self._sesion.flush()
        return fila

    async def obtener_por_id(self, tipo_id: uuid.UUID) -> TipoProcedimiento | None:
        return await self._sesion.get(TipoProcedimiento, tipo_id)

    async def obtener_por_codigo(self, codigo: str) -> TipoProcedimiento | None:
        stmt = select(TipoProcedimiento).where(TipoProcedimiento.codigo == codigo)
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def listar(
        self,
        *,
        limite: int = 50,
        offset: int = 0,
    ) -> list[TipoProcedimiento]:
        stmt = (
            select(TipoProcedimiento)
            .order_by(TipoProcedimiento.created_at.desc(), TipoProcedimiento.id.asc())
            .offset(offset)
            .limit(limite)
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())

    async def actualizar(
        self,
        fila: TipoProcedimiento,
        *,
        codigo: str | None = None,
        nombre: str | None = None,
        ruta_pdf: str | None = None,
        hash_pdf: str | None = None,
        indexacion_estado: str | None = None,
        qdrant_collection_version: int | None = None,
    ) -> TipoProcedimiento:
        if codigo is not None:
            fila.codigo = codigo
        if nombre is not None:
            fila.nombre = nombre
        if ruta_pdf is not None:
            fila.ruta_pdf = ruta_pdf
        if hash_pdf is not None:
            fila.hash_pdf = hash_pdf
        if indexacion_estado is not None:
            fila.indexacion_estado = indexacion_estado
        if qdrant_collection_version is not None:
            fila.qdrant_collection_version = qdrant_collection_version
        await self._sesion.flush()
        return fila
