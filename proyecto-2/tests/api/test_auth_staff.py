"""Pruebas de autenticacion staff JWT (TASK-105)."""

from __future__ import annotations

import json
import uuid

import pytest
from httpx import AsyncClient

from tests.api.conftest import (
    EMAIL_ASISTENTE_DEMO,
    EMAIL_ADMIN_DEMO,
    PASSWORD_STAFF_ADMIN_TEST,
    PASSWORD_STAFF_ASISTENTE_TEST,
    PDF_FIXTURE_MINIMO,
)


async def _login(
    cliente: AsyncClient,
    *,
    email: str,
    password: str,
) -> dict:
    resp = await cliente.post(
        "/api/auth/staff/login",
        json={"email": email, "password": password},
    )
    return resp


@pytest.mark.asyncio
async def test_login_ok_devuelve_jwt(
    cliente_api: AsyncClient,
    usuarios_staff_sembrados: None,
) -> None:
    resp = await _login(
        cliente_api,
        email=EMAIL_ASISTENTE_DEMO,
        password=PASSWORD_STAFF_ASISTENTE_TEST,
    )
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["token_type"] == "bearer"
    assert cuerpo["rol"] == "asistente"
    assert cuerpo["nombre"] == "Asistente Demo"
    assert isinstance(cuerpo["access_token"], str) and len(cuerpo["access_token"]) > 20
    assert cuerpo["expira_en_seg"] > 0


@pytest.mark.asyncio
async def test_login_credenciales_invalidas_401(
    cliente_api: AsyncClient,
    usuarios_staff_sembrados: None,
) -> None:
    resp = await _login(
        cliente_api,
        email=EMAIL_ASISTENTE_DEMO,
        password="contrasena-incorrecta",
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Credenciales invalidas."


@pytest.mark.asyncio
async def test_staff_sin_token_401(
    cliente_api: AsyncClient,
    usuarios_staff_sembrados: None,
) -> None:
    resp = await cliente_api.get("/api/staff/casos")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_asistente_no_puede_admin_procedimientos_403(
    cliente_api: AsyncClient,
    usuarios_staff_sembrados: None,
    cabecera_admin: dict[str, str],
) -> None:
    login = await _login(
        cliente_api,
        email=EMAIL_ASISTENTE_DEMO,
        password=PASSWORD_STAFF_ASISTENTE_TEST,
    )
    token = login.json()["access_token"]
    headers_staff = {"Authorization": f"Bearer {token}"}

    resp = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=headers_staff,
        files={
            "metadata": (
                None,
                json.dumps(
                    {"codigo": f"rbac-{uuid.uuid4().hex[:6]}", "nombre": "RBAC"}
                ),
                "application/json",
            ),
            "archivo": ("protocolo.pdf", PDF_FIXTURE_MINIMO, "application/pdf"),
        },
    )
    assert resp.status_code == 403

    login_admin = await _login(
        cliente_api,
        email=EMAIL_ADMIN_DEMO,
        password=PASSWORD_STAFF_ADMIN_TEST,
    )
    token_admin = login_admin.json()["access_token"]
    resp_admin_jwt = await cliente_api.post(
        "/api/admin/procedimientos",
        headers={"Authorization": f"Bearer {token_admin}"},
        files={
            "metadata": (
                None,
                json.dumps(
                    {"codigo": f"adm-jwt-{uuid.uuid4().hex[:6]}", "nombre": "Admin JWT"}
                ),
                "application/json",
            ),
            "archivo": ("protocolo.pdf", PDF_FIXTURE_MINIMO, "application/pdf"),
        },
    )
    assert resp_admin_jwt.status_code == 201

    resp_admin_key = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files={
            "metadata": (
                None,
                json.dumps(
                    {"codigo": f"adm-key-{uuid.uuid4().hex[:6]}", "nombre": "Admin Key"}
                ),
                "application/json",
            ),
            "archivo": ("protocolo.pdf", PDF_FIXTURE_MINIMO, "application/pdf"),
        },
    )
    assert resp_admin_key.status_code == 201


@pytest.mark.asyncio
async def test_openapi_incluye_login_staff(cliente_api: AsyncClient) -> None:
    resp = await cliente_api.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert "/api/auth/staff/login" in paths
