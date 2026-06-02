"""Servicios de casos postoperatorio para panel staff (UC-MVP-02)."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistencia.repositorios.medicos import RepositorioMedicos


async def validar_cirujano_en_catalogo(
    sesion: AsyncSession,
    cirujano_id: str,
    cirujano_nombre: str,
) -> None:
    """Exige cirujano activo en catalogo y nombre alineado con ``nombre_completo``."""
    repo = RepositorioMedicos(sesion)
    medico = await repo.obtener_por_codigo(cirujano_id)
    if medico is None or not medico.activo:
        raise HTTPException(
            status_code=422,
            detail="El cirujano seleccionado no existe o esta inactivo.",
        )
    if medico.nombre_completo != cirujano_nombre:
        raise HTTPException(
            status_code=422,
            detail="El nombre del cirujano no coincide con el catalogo.",
        )
