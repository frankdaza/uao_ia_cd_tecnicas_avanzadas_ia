"""Pruebas del catalogo admin de procedimientos (UC-MVP-01)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from src.api import dependencias as deps_admin
from src.api.servicios.almacenamiento_pdf import ruta_absoluta_protocolo
from src.configuracion import obtener_configuracion
from tests.api.conftest import PDF_FIXTURE_MINIMO


def _multipart_crear(
    *,
    codigo: str = "cole-lap",
    nombre: str = "Colecistectomia laparoscopica",
    pdf: bytes = PDF_FIXTURE_MINIMO,
    nombre_archivo: str = "protocolo.pdf",
) -> dict:
    return {
        "metadata": (None, json.dumps({"codigo": codigo, "nombre": nombre}), "application/json"),
        "archivo": (nombre_archivo, pdf, "application/pdf"),
    }


@pytest.mark.asyncio
async def test_crear_procedimiento_201(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    resp = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear(),
    )
    assert resp.status_code == 201
    cuerpo = resp.json()
    assert cuerpo["codigo"] == "cole-lap"
    assert cuerpo["nombre"] == "Colecistectomia laparoscopica"
    assert cuerpo["indexacion_estado"] == "pendiente"
    assert cuerpo["qdrant_collection_version"] is None
    assert "ruta" not in json.dumps(cuerpo).lower()

    tipo_id = cuerpo["id"]
    ruta = ruta_absoluta_protocolo(tipo_id)
    assert ruta.is_file()
    assert ruta.read_bytes().startswith(b"%PDF")


@pytest.mark.asyncio
async def test_listar_y_obtener_procedimiento(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear(codigo="proc-a", nombre="Procedimiento A"),
    )
    tipo_id = crear.json()["id"]
    lista = await cliente_api.get(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        params={"limit": 10, "offset": 0},
    )
    uno = await cliente_api.get(
        f"/api/admin/procedimientos/{tipo_id}",
        headers=cabecera_admin,
    )

    assert lista.status_code == 200
    items = lista.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == tipo_id
    assert items[0]["codigo"] == "proc-a"
    assert "created_at" in items[0]

    assert uno.status_code == 200
    assert uno.json()["nombre"] == "Procedimiento A"


@pytest.mark.asyncio
async def test_patch_reemplazo_pdf_incrementa_version(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear(codigo="ver-test"),
    )
    tipo_id = crear.json()["id"]
    parche = await cliente_api.patch(
        f"/api/admin/procedimientos/{tipo_id}",
        headers=cabecera_admin,
        files={
            "archivo": ("nuevo.pdf", PDF_FIXTURE_MINIMO + b"\n", "application/pdf"),
        },
    )

    assert parche.status_code == 200
    cuerpo = parche.json()
    assert cuerpo["qdrant_collection_version"] == 1
    assert cuerpo["indexacion_estado"] == "pendiente"


@pytest.mark.asyncio
async def test_patch_solo_metadata_sin_version(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear(codigo="meta-only"),
    )
    tipo_id = crear.json()["id"]
    parche = await cliente_api.patch(
        f"/api/admin/procedimientos/{tipo_id}",
        headers=cabecera_admin,
        files={
            "metadata": (
                None,
                json.dumps({"nombre": "Nombre actualizado"}),
                "application/json",
            ),
        },
    )

    assert parche.status_code == 200
    assert parche.json()["nombre"] == "Nombre actualizado"
    assert parche.json()["qdrant_collection_version"] is None


@pytest.mark.asyncio
async def test_422_pdf_invalido(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    resp = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear(pdf=b"no-es-pdf", nombre_archivo="mal.pdf"),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_409_codigo_duplicado(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear(codigo="dup", nombre="Uno"),
    )
    resp = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear(codigo="dup", nombre="Dos"),
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_404_procedimiento_inexistente(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    resp = await cliente_api.get(
        "/api/admin/procedimientos/00000000-0000-0000-0000-000000000099",
        headers=cabecera_admin,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_admin_401_sin_cabecera(cliente_api: AsyncClient) -> None:
    resp = await cliente_api.get("/api/admin/procedimientos")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_503_sin_clave_configurada(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from httpx import ASGITransport, AsyncClient

    from src.api.main import crear_app

    monkeypatch.setenv("ADMIN_API_KEY", "")
    obtener_configuracion.cache_clear()
    monkeypatch.setattr(
        deps_admin,
        "obtener_configuracion",
        lambda: SimpleNamespace(admin_api_key=None),
    )
    app = crear_app(url_bd="sqlite+aiosqlite:///:memory:")
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                "/api/admin/procedimientos",
                headers={"X-Admin-Key": "cualquiera"},
            )
    assert resp.status_code == 503
