"""Pruebas del dashboard de sistema admin."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dashboard_admin_resumen_jwt(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
    medico_activo_catalogo: dict[str, str | None],
) -> None:
    resp = await cliente_api.get(
        "/api/admin/dashboard/resumen",
        headers=cabecera_staff_admin,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["medicos"]["total"] >= 1
    assert data["medicos"]["activos"] >= 1
    assert "recordatorios_job_habilitado" in data["config_operativa"]
    assert "agente_hitl_habilitado" in data["config_operativa"]
    assert "configurado" in data["telegram_webhook"]
    assert "generado_en" in data


@pytest.mark.asyncio
async def test_dashboard_admin_staff_no_admin_403(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
) -> None:
    resp = await cliente_api.get(
        "/api/admin/dashboard/resumen",
        headers=cabecera_staff,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_dashboard_admin_api_key(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    resp = await cliente_api.get(
        "/api/admin/dashboard/resumen",
        headers=cabecera_admin,
    )
    assert resp.status_code == 200, resp.text
