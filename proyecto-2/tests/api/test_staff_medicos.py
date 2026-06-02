"""Pruebas de opciones de medicos para staff y validacion en alta de caso (TASK-138)."""

from __future__ import annotations

import uuid

import pytest

pytest_plugins = ["tests.api.test_staff_casos"]
from httpx import AsyncClient

from tests.api.test_staff_casos import _cuerpo_caso


@pytest.mark.asyncio
async def test_listar_medicos_staff_solo_activos(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    cabecera_admin: dict[str, str],
    medico_activo_catalogo: dict[str, str | None],
) -> None:
    codigo_activo = medico_activo_catalogo["codigo_registro"]
    crear_inactivo = await cliente_api.post(
        "/api/admin/medicos",
        headers=cabecera_admin,
        json={
            "codigo_registro": f"DOC-IN-{uuid.uuid4().hex[:6].upper()}",
            "nombre_completo": "Dr. Inactivo Staff",
            "especialidad": None,
        },
    )
    assert crear_inactivo.status_code == 201
    medico_id = crear_inactivo.json()["id"]
    borrar = await cliente_api.delete(
        f"/api/admin/medicos/{medico_id}",
        headers=cabecera_admin,
    )
    assert borrar.status_code == 204

    resp = await cliente_api.get(
        "/api/staff/medicos",
        headers=cabecera_staff,
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    codigos = {i["codigo_registro"] for i in items}
    assert codigo_activo in codigos
    assert crear_inactivo.json()["codigo_registro"] not in codigos
    for item in items:
        assert set(item.keys()) == {"codigo_registro", "nombre_completo", "especialidad"}
    nombres = [i["nombre_completo"] for i in items]
    assert nombres == sorted(nombres, key=str.casefold)


@pytest.mark.asyncio
async def test_listar_medicos_staff_sin_token_401(
    cliente_api: AsyncClient,
    usuarios_staff_sembrados: None,  # noqa: ARG001
) -> None:
    resp = await cliente_api.get("/api/staff/medicos")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_crear_caso_cirujano_inexistente_422(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
) -> None:
    resp = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(
            tipo_id=tipo_procedimiento_ok,
            cirujano_id="NO-EXISTE",
            cirujano_nombre="Dr. Fantasma",
        ),
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "El cirujano seleccionado no existe o esta inactivo."


@pytest.mark.asyncio
async def test_crear_caso_cirujano_inactivo_422(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    cabecera_admin: dict[str, str],
    tipo_procedimiento_ok: str,
) -> None:
    codigo = f"DOC-OFF-{uuid.uuid4().hex[:6].upper()}"
    nombre = "Dr. Desactivado"
    crear = await cliente_api.post(
        "/api/admin/medicos",
        headers=cabecera_admin,
        json={
            "codigo_registro": codigo,
            "nombre_completo": nombre,
        },
    )
    assert crear.status_code == 201
    medico_id = crear.json()["id"]
    borrar = await cliente_api.delete(
        f"/api/admin/medicos/{medico_id}",
        headers=cabecera_admin,
    )
    assert borrar.status_code == 204

    resp = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(
            tipo_id=tipo_procedimiento_ok,
            cirujano_id=codigo,
            cirujano_nombre=nombre,
        ),
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "El cirujano seleccionado no existe o esta inactivo."


@pytest.mark.asyncio
async def test_crear_caso_nombre_cirujano_no_coincide_422(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
    medico_activo_catalogo: dict[str, str | None],
) -> None:
    med = medico_activo_catalogo
    resp = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(
            tipo_id=tipo_procedimiento_ok,
            cirujano_id=med["codigo_registro"],
            cirujano_nombre="Nombre incorrecto",
        ),
    )
    assert resp.status_code == 422
    assert resp.json()["detail"] == "El nombre del cirujano no coincide con el catalogo."


@pytest.mark.asyncio
async def test_crear_caso_cirujano_catalogo_201(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    tipo_procedimiento_ok: str,
    medico_activo_catalogo: dict[str, str | None],
) -> None:
    med = medico_activo_catalogo
    resp = await cliente_api.post(
        "/api/staff/casos",
        headers=cabecera_staff,
        json=_cuerpo_caso(
            tipo_id=tipo_procedimiento_ok,
            cirujano_id=med["codigo_registro"],
            cirujano_nombre=med["nombre_completo"],
        ),
    )
    assert resp.status_code == 201
    assert resp.json()["cirujano_id"] == med["codigo_registro"]
    assert resp.json()["cirujano_nombre"] == med["nombre_completo"]
