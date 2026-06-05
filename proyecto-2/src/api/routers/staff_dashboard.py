"""Rutas de dashboard de inicio (KPIs operativos y sistema)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencias import obtener_staff_actual, requerir_acceso_admin
from src.api.esquemas_dashboard import ResumenDashboardAdmin, ResumenDashboardStaff
from src.api.servicios.dashboard import (
    construir_resumen_dashboard_admin,
    construir_resumen_dashboard_staff,
)
from src.persistencia.modelos import UsuarioStaff
from src.persistencia.motor import obtener_sesion_db

router_staff = APIRouter(
    prefix="/staff",
    tags=["staff-dashboard"],
    dependencies=[Depends(obtener_staff_actual)],
)

router_admin = APIRouter(
    prefix="/admin",
    tags=["admin-dashboard"],
    dependencies=[Depends(requerir_acceso_admin)],
)


@router_staff.get("/dashboard/resumen", response_model=ResumenDashboardStaff)
async def obtener_resumen_dashboard_staff(
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
    staff: Annotated[UsuarioStaff, Depends(obtener_staff_actual)],
) -> ResumenDashboardStaff:
    """KPIs operativos en tiempo real para el panel de inicio."""
    return await construir_resumen_dashboard_staff(sesion, staff=staff)


@router_admin.get("/dashboard/resumen", response_model=ResumenDashboardAdmin)
async def obtener_resumen_dashboard_admin(
    sesion: Annotated[AsyncSession, Depends(obtener_sesion_db)],
) -> ResumenDashboardAdmin:
    """Metricas de sistema para administradores."""
    return await construir_resumen_dashboard_admin(sesion)
