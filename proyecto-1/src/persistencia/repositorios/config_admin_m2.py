"""Repositorio de la fila singleton ``config_admin_m2``."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.modelos import ConfigAdminM2


class RepositorioConfigAdminM2:
    """Lectura/escritura de overrides de configuracion admin (singleton id=1)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def obtener(self) -> ConfigAdminM2 | None:
        """Devuelve la fila singleton o ``None`` si aun no existe."""
        return await self._sesion.get(ConfigAdminM2, 1)

    async def obtener_para_actualizar(self) -> ConfigAdminM2 | None:
        """Carga la fila con bloqueo pesimista para actualizacion concurrente segura."""
        stmt = select(ConfigAdminM2).where(ConfigAdminM2.id == 1).with_for_update()
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    def agregar_inicial(self, fila: ConfigAdminM2) -> None:
        """Inserta la fila id=1 (sin commit; lo hace la sesion HTTP)."""
        self._sesion.add(fila)
