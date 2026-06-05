"""Estado en memoria del HITL de escalamiento (hot-reload desde panel admin)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.configuracion import Configuracion
from src.persistencia.modelos import ConfigOperativaTaam
from src.persistencia.repositorios.config_operativa_taam import RepositorioConfigOperativaTaam

_estado_runtime: AgenteHitlEstado | None = None


@dataclass(frozen=True)
class AgenteHitlSnapshot:
    """Valor efectivo de ``escalar_a_equipo`` sujeto a HITL."""

    habilitado: bool
    updated_at: datetime | None = None


class AgenteHitlEstado:
    """Cache thread-safe sincronizada con ``config_operativa_taam``."""

    def __init__(
        self,
        *,
        habilitado: bool,
        updated_at: datetime | None = None,
    ) -> None:
        self._lock = asyncio.Lock()
        self._habilitado = habilitado
        self._updated_at = updated_at

    @classmethod
    def desde_fila(cls, fila: ConfigOperativaTaam) -> AgenteHitlEstado:
        return cls(
            habilitado=fila.agente_hitl_escalar_habilitado,
            updated_at=fila.updated_at,
        )

    async def leer(self) -> AgenteHitlSnapshot:
        async with self._lock:
            return AgenteHitlSnapshot(
                habilitado=self._habilitado,
                updated_at=self._updated_at,
            )

    def _aplicar_memoria(self, fila: ConfigOperativaTaam) -> AgenteHitlSnapshot:
        self._habilitado = fila.agente_hitl_escalar_habilitado
        self._updated_at = fila.updated_at
        return AgenteHitlSnapshot(
            habilitado=self._habilitado,
            updated_at=self._updated_at,
        )

    async def aplicar(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        habilitado: bool,
    ) -> AgenteHitlSnapshot:
        """Persiste en BD y actualiza la cache en memoria."""
        async with self._lock:
            async with session_factory() as sesion:
                repo = RepositorioConfigOperativaTaam(sesion)
                fila = await repo.actualizar_agente_hitl(habilitado=habilitado)
                await sesion.commit()
                return self._aplicar_memoria(fila)


async def inicializar_agente_hitl_estado(
    session_factory: async_sessionmaker[AsyncSession],
    cfg: Configuracion,
) -> AgenteHitlEstado:
    """Carga o crea la fila singleton y devuelve el estado runtime."""
    async with session_factory() as sesion:
        repo = RepositorioConfigOperativaTaam(sesion)
        fila = await repo.obtener_o_crear_desde_env(cfg)
        await sesion.commit()
        return AgenteHitlEstado.desde_fila(fila)


def registrar_agente_hitl_runtime(estado: AgenteHitlEstado | None) -> None:
    global _estado_runtime
    _estado_runtime = estado


def obtener_agente_hitl_runtime() -> AgenteHitlEstado | None:
    return _estado_runtime


async def hitl_escalar_habilitado_efectivo() -> bool:
    """Lee el flag en caliente; fallback a .env si el runtime no esta registrado."""
    if _estado_runtime is None:
        from src.configuracion import obtener_configuracion

        return obtener_configuracion().agente_hitl_escalar_habilitado
    snapshot = await _estado_runtime.leer()
    return snapshot.habilitado
