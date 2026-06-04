"""Estado en memoria del job de recordatorios (hot-reload desde panel admin)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.configuracion import Configuracion
from src.persistencia.modelos import ConfigOperativaTaam
from src.integracion.recordatorios.servicio import reprogramar_recordatorios_pendientes
from src.persistencia.repositorios.config_operativa_taam import RepositorioConfigOperativaTaam


@dataclass(frozen=True)
class RecordatoriosJobSnapshot:
    """Valores efectivos leidos por el bucle asyncio."""

    habilitado: bool
    interval_seg: int
    updated_at: datetime | None = None


class RecordatoriosJobEstado:
    """Cache thread-safe sincronizada con ``config_operativa_taam``."""

    def __init__(
        self,
        *,
        habilitado: bool,
        interval_seg: int,
        updated_at: datetime | None = None,
    ) -> None:
        self._lock = asyncio.Lock()
        self._habilitado = habilitado
        self._interval_seg = interval_seg
        self._updated_at = updated_at

    @classmethod
    def desde_fila(cls, fila: ConfigOperativaTaam) -> RecordatoriosJobEstado:
        return cls(
            habilitado=fila.recordatorios_job_habilitado,
            interval_seg=fila.recordatorios_job_interval_seg,
            updated_at=fila.updated_at,
        )

    async def leer(self) -> RecordatoriosJobSnapshot:
        async with self._lock:
            return RecordatoriosJobSnapshot(
                habilitado=self._habilitado,
                interval_seg=self._interval_seg,
                updated_at=self._updated_at,
            )

    def _aplicar_memoria(self, fila: ConfigOperativaTaam) -> RecordatoriosJobSnapshot:
        self._habilitado = fila.recordatorios_job_habilitado
        self._interval_seg = fila.recordatorios_job_interval_seg
        self._updated_at = fila.updated_at
        return RecordatoriosJobSnapshot(
            habilitado=self._habilitado,
            interval_seg=self._interval_seg,
            updated_at=self._updated_at,
        )

    async def aplicar(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        habilitado: bool | None = None,
        interval_seg: int | None = None,
    ) -> RecordatoriosJobSnapshot:
        """Persiste en BD y actualiza la cache en memoria."""
        async with self._lock:
            async with session_factory() as sesion:
                repo = RepositorioConfigOperativaTaam(sesion)
                fila = await repo.actualizar_recordatorios_job(
                    habilitado=habilitado,
                    interval_seg=interval_seg,
                )
                await sesion.commit()
                snapshot = self._aplicar_memoria(fila)
            if interval_seg is not None:
                await reprogramar_recordatorios_pendientes(
                    session_factory,
                    interval_seg=snapshot.interval_seg,
                )
            return snapshot


async def inicializar_recordatorios_job_estado(
    session_factory: async_sessionmaker[AsyncSession],
    cfg: Configuracion,
) -> RecordatoriosJobEstado:
    """Carga o crea la fila singleton y devuelve el estado runtime."""
    async with session_factory() as sesion:
        repo = RepositorioConfigOperativaTaam(sesion)
        fila = await repo.obtener_o_crear_desde_env(cfg)
        await sesion.commit()
        return RecordatoriosJobEstado.desde_fila(fila)
