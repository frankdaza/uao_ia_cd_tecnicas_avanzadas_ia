"""Repositorio de usuarios (acceso async a tabla ``usuarios``)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import Usuario


class RepositorioUsuarios:
    """Operaciones de lectura/escritura sobre ``Usuario`` sin SQL en routers."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def obtener_por_documento(self, documento: str) -> Usuario | None:
        """Busca por ``documento_identidad`` unico."""
        stmt = select(Usuario).where(Usuario.documento_identidad == documento)
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def obtener_por_id(self, usuario_id: uuid.UUID) -> Usuario | None:
        """Busca por clave primaria ``id``."""
        return await self._sesion.get(Usuario, usuario_id)

    async def obtener_o_crear(
        self, documento: str, nombre: str
    ) -> tuple[Usuario, bool]:
        """
        Inserta si no existe; si ya existia, devuelve la fila actual sin
        modificar el nombre.

        Retorna ``(usuario, ya_existia)`` donde ``ya_existia`` es ``True`` si
        hubo conflicto por unicidad de documento (equivalente atomico a
        upsert de solo-insert).
        """
        stmt = (
            pg_insert(Usuario)
            .values(documento_identidad=documento, nombre=nombre)
            .on_conflict_do_nothing(constraint="uq_usuarios_documento_identidad")
            .returning(Usuario.id)
        )
        res = await self._sesion.execute(stmt)
        nuevo_id = res.scalar_one_or_none()
        if nuevo_id is not None:
            creado = await self._sesion.get(Usuario, nuevo_id)
            if creado is None:
                raise RuntimeError(
                    "Inconsistencia interna: insert en usuarios sin fila legible."
                )
            return creado, False

        existente = await self.obtener_por_documento(documento)
        if existente is None:
            raise RuntimeError(
                "Inconsistencia interna: conflicto de unicidad sin fila existente."
            )
        return existente, True

    async def actualizar_last_login(self, usuario_id: uuid.UUID) -> None:
        """Persiste ``last_login_at`` en UTC (timezone-aware)."""
        ahora_utc = datetime.now(UTC)
        stmt = (
            update(Usuario)
            .where(Usuario.id == usuario_id)
            .values(last_login_at=ahora_utc)
        )
        await self._sesion.execute(stmt)

    async def contar_total(self) -> int:
        """Cuenta filas en ``usuarios`` (barato con indice secundario minimo en PK)."""
        stmt = select(func.count()).select_from(Usuario)
        res = await self._sesion.execute(stmt)
        n = res.scalar_one()
        return int(n)

    async def contar_activos_ultimos_dias(self, dias: int) -> int:
        """
        Usuarios con ``last_login_at`` no nulo dentro de la ventana de ``dias`` (UTC).

        La comparacion usa el reloj del servidor de aplicacion (UTC) alineado a
        ``DateTime(timezone=True)`` en PostgreSQL.
        """
        limite = datetime.now(UTC) - timedelta(days=int(dias))
        stmt = (
            select(func.count())
            .select_from(Usuario)
            .where(Usuario.last_login_at.is_not(None))
            .where(Usuario.last_login_at >= limite)
        )
        res = await self._sesion.execute(stmt)
        return int(res.scalar_one())

    async def listar_paginado(
        self,
        *,
        limite: int,
        offset: int,
    ) -> list[Usuario]:
        """Lista estable por ``created_at`` ascendente y ``id`` como desempate."""
        stmt = (
            select(Usuario)
            .order_by(Usuario.created_at.asc(), Usuario.id.asc())
            .offset(offset)
            .limit(limite)
        )
        res = await self._sesion.execute(stmt)
        return list(res.scalars().all())
