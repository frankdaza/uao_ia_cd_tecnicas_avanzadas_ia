"""Repositorio del catalogo ``tipos_procedimiento``."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
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
        formato_protocolo: str = "pdf",
        qdrant_collection_version: int | None = None,
    ) -> TipoProcedimiento:
        fila = TipoProcedimiento(
            codigo=codigo,
            nombre=nombre,
            ruta_pdf=ruta_pdf,
            hash_pdf=hash_pdf,
            formato_protocolo=formato_protocolo,
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

    async def listar_por_indexacion(
        self,
        estado: str,
        *,
        limite: int = 50,
    ) -> list[TipoProcedimiento]:
        stmt = (
            select(TipoProcedimiento)
            .where(TipoProcedimiento.indexacion_estado == estado)
            .order_by(TipoProcedimiento.created_at.asc(), TipoProcedimiento.id.asc())
            .limit(limite)
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())

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
        formato_protocolo: str | None = None,
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
        if formato_protocolo is not None:
            fila.formato_protocolo = formato_protocolo
        if indexacion_estado is not None:
            fila.indexacion_estado = indexacion_estado
        if qdrant_collection_version is not None:
            fila.qdrant_collection_version = qdrant_collection_version
        await self._sesion.flush()
        return fila

    async def contar_por_indexacion_estado(self) -> dict[str, int]:
        stmt = select(
            TipoProcedimiento.indexacion_estado,
            func.count(),
        ).group_by(TipoProcedimiento.indexacion_estado)
        res = await self._sesion.execute(stmt)
        return {str(estado): int(cnt) for estado, cnt in res.all()}
