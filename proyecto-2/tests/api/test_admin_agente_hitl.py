"""Pruebas de configuracion admin del HITL de escalamiento."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.api.conftest import (
    EMAIL_ADMIN_DEMO,
    PASSWORD_STAFF_ADMIN_TEST,
)


@pytest.fixture
async def token_staff_admin(
    cliente_api: AsyncClient,
    usuarios_staff_sembrados: None,  # noqa: ARG001
) -> str:
    resp = await cliente_api.post(
        "/api/auth/staff/login",
        json={"email": EMAIL_ADMIN_DEMO, "password": PASSWORD_STAFF_ADMIN_TEST},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def cabecera_staff_admin(token_staff_admin: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_staff_admin}"}


@pytest.mark.asyncio
async def test_get_agente_hitl_admin_jwt(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
) -> None:
    resp = await cliente_api.get(
        "/api/admin/agente-hitl",
        headers=cabecera_staff_admin,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["habilitado"] is False
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_patch_agente_hitl_admin_jwt(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
    app_api,
) -> None:
    resp = await cliente_api.patch(
        "/api/admin/agente-hitl",
        headers=cabecera_staff_admin,
        json={"habilitado": True},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["habilitado"] is True
    assert data["updated_at"] is not None

    snapshot = await app_api.state.agente_hitl.leer()
    assert snapshot.habilitado is True


@pytest.mark.asyncio
async def test_get_agente_hitl_staff_no_admin_403(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
) -> None:
    resp = await cliente_api.get(
        "/api/admin/agente-hitl",
        headers=cabecera_staff,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_agente_hitl_admin_api_key(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    resp = await cliente_api.get(
        "/api/admin/agente-hitl",
        headers=cabecera_admin,
    )
    assert resp.status_code == 200, resp.text
