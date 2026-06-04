"""Repositorio de la fila singleton ``config_operativa_taam``."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.configuracion import Configuracion
from src.persistencia.modelos import ConfigOperativaTaam

_INTERVALO_MIN = 5
_INTERVALO_MAX = 3600


def _acotar_intervalo_seg(valor: int) -> int:
    return max(_INTERVALO_MIN, min(_INTERVALO_MAX, valor))


class RepositorioConfigOperativaTaam:
    """Lectura/escritura de configuracion operativa TAAM (singleton id=1)."""

    def __init__(self, sesion: AsyncSession) -> None:
        self._sesion = sesion

    async def obtener(self) -> ConfigOperativaTaam | None:
        return await self._sesion.get(ConfigOperativaTaam, 1)

    async def obtener_para_actualizar(self) -> ConfigOperativaTaam | None:
        stmt = select(ConfigOperativaTaam).where(ConfigOperativaTaam.id == 1).with_for_update()
        res = await self._sesion.execute(stmt)
        return res.scalars().first()

    async def obtener_o_crear_desde_env(self, cfg: Configuracion) -> ConfigOperativaTaam:
        """Crea la fila singleton con valores de entorno si aun no existe."""
        fila = await self.obtener()
        if fila is not None:
            return fila
        fila = ConfigOperativaTaam(
            id=1,
            recordatorios_job_habilitado=cfg.recordatorios_job_habilitado,
            recordatorios_job_interval_seg=_acotar_intervalo_seg(
                cfg.recordatorios_job_interval_seg
            ),
            updated_at=datetime.now(UTC),
        )
        self._sesion.add(fila)
        await self._sesion.flush()
        return fila

    async def actualizar_recordatorios_job(
        self,
        *,
        habilitado: bool | None = None,
        interval_seg: int | None = None,
    ) -> ConfigOperativaTaam:
        fila = await self.obtener_para_actualizar()
        if fila is None:
            raise ValueError("config_operativa_taam no inicializada")
        if habilitado is not None:
            fila.recordatorios_job_habilitado = habilitado
        if interval_seg is not None:
            fila.recordatorios_job_interval_seg = _acotar_intervalo_seg(interval_seg)
        fila.updated_at = datetime.now(UTC)
        await self._sesion.flush()
        return fila
