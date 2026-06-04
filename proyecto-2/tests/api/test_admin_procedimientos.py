"""Pruebas del catalogo admin de procedimientos (UC-MVP-01)."""

from __future__ import annotations

import json
import uuid
from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from src.api import dependencias as deps_admin
from src.api.servicios.almacenamiento_protocolo import ruta_absoluta_por_formato
from src.configuracion import obtener_configuracion
from tests.api.conftest import MD_FIXTURE_FM_INVALIDO, MD_FIXTURE_MINIMO, PDF_FIXTURE_MINIMO


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
    assert cuerpo["formato_protocolo"] == "pdf"
    assert cuerpo["qdrant_collection_version"] is None
    assert "ruta" not in json.dumps(cuerpo).lower()

    tipo_id = cuerpo["id"]
    ruta = ruta_absoluta_por_formato(tipo_id, "pdf")
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


def _multipart_crear_md(
    *,
    codigo: str = "cole-md",
    nombre: str = "Protocolo Markdown",
    contenido: bytes = MD_FIXTURE_MINIMO,
    nombre_archivo: str = "protocolo.md",
) -> dict:
    return {
        "metadata": (None, json.dumps({"codigo": codigo, "nombre": nombre}), "application/json"),
        "archivo": (nombre_archivo, contenido, "text/markdown"),
    }


@pytest.mark.asyncio
async def test_crear_procedimiento_markdown_201(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    resp = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear_md(),
    )
    assert resp.status_code == 201
    cuerpo = resp.json()
    assert cuerpo["formato_protocolo"] == "markdown"
    assert cuerpo["indexacion_estado"] == "pendiente"

    tipo_id = cuerpo["id"]
    ruta_md = ruta_absoluta_por_formato(tipo_id, "markdown")
    ruta_pdf = ruta_absoluta_por_formato(tipo_id, "pdf")
    assert ruta_md.is_file()
    assert not ruta_pdf.is_file()
    assert b"Cuidados postoperatorios" in ruta_md.read_bytes()


@pytest.mark.asyncio
async def test_422_markdown_front_matter_invalido(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    resp = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear_md(
            codigo="md-bad-fm",
            contenido=MD_FIXTURE_FM_INVALIDO,
        ),
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_patch_pdf_a_markdown_elimina_pdf_anterior(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear(codigo="swap-pdf-md"),
    )
    tipo_id = crear.json()["id"]
    ruta_pdf = ruta_absoluta_por_formato(tipo_id, "pdf")
    assert ruta_pdf.is_file()

    parche = await cliente_api.patch(
        f"/api/admin/procedimientos/{tipo_id}",
        headers=cabecera_admin,
        files={
            "archivo": ("protocolo.md", MD_FIXTURE_MINIMO, "text/markdown"),
        },
    )
    assert parche.status_code == 200
    assert parche.json()["formato_protocolo"] == "markdown"
    assert not ruta_pdf.is_file()
    assert ruta_absoluta_por_formato(tipo_id, "markdown").is_file()


@pytest.mark.asyncio
async def test_patch_markdown_a_pdf_elimina_md_anterior(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear_md(codigo="swap-md-pdf"),
    )
    tipo_id = crear.json()["id"]
    ruta_md = ruta_absoluta_por_formato(tipo_id, "markdown")
    assert ruta_md.is_file()

    parche = await cliente_api.patch(
        f"/api/admin/procedimientos/{tipo_id}",
        headers=cabecera_admin,
        files={
            "archivo": ("protocolo.pdf", PDF_FIXTURE_MINIMO, "application/pdf"),
        },
    )
    assert parche.status_code == 200
    assert parche.json()["formato_protocolo"] == "pdf"
    assert not ruta_md.is_file()
    assert ruta_absoluta_por_formato(tipo_id, "pdf").is_file()


@pytest.mark.asyncio
async def test_reindexar_sin_archivo_422(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
    app_api,
) -> None:
    from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento

    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear(codigo="sin-archivo-reidx"),
    )
    tipo_id = uuid.UUID(crear.json()["id"])
    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo = RepositorioTiposProcedimiento(sesion)
        fila = await repo.obtener_por_id(tipo_id)
        assert fila is not None
        fila.ruta_pdf = None
        await sesion.flush()
        await sesion.commit()

    reindex = await cliente_api.post(
        f"/api/admin/procedimientos/{tipo_id}/reindexar",
        headers=cabecera_admin,
    )
    assert reindex.status_code == 422
    assert "protocolo" in reindex.json()["detail"].lower()


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


@pytest.mark.asyncio
async def test_get_protocolo_pdf_200(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear(codigo="get-proto-pdf"),
    )
    assert crear.status_code == 201
    tipo_id = crear.json()["id"]

    resp = await cliente_api.get(
        f"/api/admin/procedimientos/{tipo_id}/protocolo",
        headers=cabecera_admin,
    )
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers.get("content-type", "")
    assert resp.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_get_protocolo_markdown_200(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear_md(codigo="get-proto-md"),
    )
    assert crear.status_code == 201
    tipo_id = crear.json()["id"]

    resp = await cliente_api.get(
        f"/api/admin/procedimientos/{tipo_id}/protocolo",
        headers=cabecera_admin,
    )
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers.get("content-type", "")
    assert b"Cuidados postoperatorios" in resp.content


@pytest.mark.asyncio
async def test_get_protocolo_procedimiento_inexistente_404(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
) -> None:
    resp = await cliente_api.get(
        "/api/admin/procedimientos/00000000-0000-0000-0000-000000000099/protocolo",
        headers=cabecera_admin,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_protocolo_sin_archivo_404(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
    app_api,
) -> None:
    from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento

    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear(codigo="get-proto-sin-arch"),
    )
    tipo_id = uuid.UUID(crear.json()["id"])
    factory = app_api.state.session_factory
    async with factory() as sesion:
        repo = RepositorioTiposProcedimiento(sesion)
        fila = await repo.obtener_por_id(tipo_id)
        assert fila is not None
        fila.ruta_pdf = None
        await sesion.flush()
        await sesion.commit()

    resp = await cliente_api.get(
        f"/api/admin/procedimientos/{tipo_id}/protocolo",
        headers=cabecera_admin,
    )
    assert resp.status_code == 404
    assert "protocolo" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_asistente_no_puede_get_protocolo_403(
    cliente_api: AsyncClient,
    usuarios_staff_sembrados: None,
    cabecera_admin: dict[str, str],
) -> None:
    from tests.api.conftest import (
        EMAIL_ASISTENTE_DEMO,
        PASSWORD_STAFF_ASISTENTE_TEST,
    )

    crear = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files=_multipart_crear(codigo="rbac-get-proto"),
    )
    tipo_id = crear.json()["id"]

    login = await cliente_api.post(
        "/api/auth/staff/login",
        json={"email": EMAIL_ASISTENTE_DEMO, "password": PASSWORD_STAFF_ASISTENTE_TEST},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    resp = await cliente_api.get(
        f"/api/admin/procedimientos/{tipo_id}/protocolo",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403
