"""Pruebas HTTP del router de sesiones (Modulo 2)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.dependencias import obtener_usuario_actual
from src.api.esquemas import MensajeHistorialItem
from src.persistencia.modelos import Usuario
from src.persistencia.repositorios.sesiones import sesion_id_memoria_langchain


@pytest_asyncio.fixture
async def cliente_api_sesiones(fastapi_app_sesion_mock) -> AsyncClient:
    """Cliente ASGI con factoria de sesion DB sobrescrita (sin Postgres)."""
    app = fastapi_app_sesion_mock
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as cliente:
        cliente._app_ref = app  # type: ignore[attr-defined]
        yield cliente


@pytest.mark.asyncio
async def test_post_sesiones_crea_usuario_y_cookie(
    cliente_api_sesiones: AsyncClient,
) -> None:
    uid = uuid.uuid4()
    usuario = Usuario(id=uid, documento_identidad="999", nombre="Usuario Demo")
    with patch("src.api.routers.sesiones.RepositorioUsuarios") as cls_mock:
        instancia = cls_mock.return_value
        instancia.obtener_o_crear = AsyncMock(return_value=(usuario, False))
        instancia.actualizar_last_login = AsyncMock()
        with patch(
            "src.api.routers.sesiones.asyncio.to_thread",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await cliente_api_sesiones.post(
                "/api/sesiones",
                json={"documento_identidad": "999", "nombre": "Usuario Demo"},
            )
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["ya_existia"] is False
    assert cuerpo["usuario_id"] == str(uid)
    assert cuerpo["session_id"] == sesion_id_memoria_langchain(uid)
    assert cuerpo["nombre"] == "Usuario Demo"
    assert "fvl_session_id" in resp.headers.get("set-cookie", "").lower()


@pytest.mark.asyncio
async def test_post_sesiones_usuario_existente_mismo_id(
    cliente_api_sesiones: AsyncClient,
) -> None:
    uid = uuid.uuid4()
    usuario = Usuario(id=uid, documento_identidad="888", nombre="Ya Registrado")
    with patch("src.api.routers.sesiones.RepositorioUsuarios") as cls_mock:
        instancia = cls_mock.return_value
        instancia.obtener_o_crear = AsyncMock(return_value=(usuario, True))
        instancia.actualizar_last_login = AsyncMock()
        with patch(
            "src.api.routers.sesiones.asyncio.to_thread",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await cliente_api_sesiones.post(
                "/api/sesiones",
                json={"documento_identidad": "888", "nombre": "Otro nombre"},
            )
    assert resp.status_code == 200
    assert resp.json()["ya_existia"] is True
    assert resp.json()["usuario_id"] == str(uid)


@pytest.mark.asyncio
async def test_get_historial_sin_credencial_401(
    cliente_api_sesiones: AsyncClient,
) -> None:
    resp = await cliente_api_sesiones.get("/api/sesiones/actual/historial")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_historial_session_id_invalido_401(
    cliente_api_sesiones: AsyncClient,
) -> None:
    resp = await cliente_api_sesiones.get(
        "/api/sesiones/actual/historial",
        headers={"X-Session-Id": "no-es-un-uuid"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_historial_usuario_desconocido_401(
    cliente_api_sesiones: AsyncClient,
) -> None:
    uid = uuid.uuid4()
    sid = sesion_id_memoria_langchain(uid)
    with patch("src.api.dependencias.RepositorioUsuarios") as cls_mock:
        instancia = cls_mock.return_value
        instancia.obtener_por_id = AsyncMock(return_value=None)
        resp = await cliente_api_sesiones.get(
            "/api/sesiones/actual/historial",
            headers={"X-Session-Id": sid},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_historial_ok_mock_memoria(cliente_api_sesiones: AsyncClient) -> None:
    app = cliente_api_sesiones._app_ref  # type: ignore[attr-defined]
    uid = uuid.uuid4()
    usuario = Usuario(id=uid, documento_identidad="1", nombre="N")

    async def _usuario_fijo() -> Usuario:
        return usuario

    app.dependency_overrides[obtener_usuario_actual] = _usuario_fijo
    try:
        items = [
            MensajeHistorialItem(rol="human", contenido="hola", creado_en=None),
            MensajeHistorialItem(rol="ai", contenido="hola usuario", creado_en=None),
        ]
        with patch(
            "src.api.routers.sesiones._cargar_mensajes_desde_memoria",
            new_callable=AsyncMock,
            return_value=items,
        ):
            resp = await cliente_api_sesiones.get("/api/sesiones/actual/historial")
    finally:
        del app.dependency_overrides[obtener_usuario_actual]

    assert resp.status_code == 200
    data = resp.json()["mensajes"]
    assert len(data) == 2
    assert data[0]["rol"] == "human" and data[0]["contenido"] == "hola"
    assert data[1]["rol"] == "ai"


@pytest.mark.asyncio
async def test_post_cerrar_sesion_set_cookie_delete(
    cliente_api_sesiones: AsyncClient,
) -> None:
    resp = await cliente_api_sesiones.post("/api/sesiones/cerrar")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    set_cookie = resp.headers.get("set-cookie", "")
    assert "fvl_session_id" in set_cookie.lower()


@pytest.mark.asyncio
async def test_openapi_incluye_rutas_sesiones(
    cliente_api_sesiones: AsyncClient,
) -> None:
    r = await cliente_api_sesiones.get("/openapi.json")
    assert r.status_code == 200
    rutas = r.json().get("paths", {})
    assert "/api/sesiones" in rutas
    assert "/api/sesiones/actual/historial" in rutas
    assert "/api/sesiones/cerrar" in rutas
