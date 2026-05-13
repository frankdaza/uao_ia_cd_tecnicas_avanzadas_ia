"""Pruebas basicas del router administrativo M2 (auth y lectura con sesion simulada)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.api.configuracion import obtener_configuracion
from src.api.dependencias import obtener_sesion_db
from src.api.main import crear_app
from src.persistencia.modelos import ConfigAdminM2


@pytest.fixture(autouse=True)
def limpiar_cache_config() -> None:
    """Evita que ``lru_cache`` de configuracion contamine pruebas entre casos."""
    obtener_configuracion.cache_clear()
    yield
    obtener_configuracion.cache_clear()


@pytest.mark.asyncio
async def test_admin_config_503_cuando_no_hay_clave(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "")
    obtener_configuracion.cache_clear()
    app = crear_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/admin/config", headers={"X-Admin-Key": "cualquiera"})
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_admin_config_401_clave_incorrecta(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "abcd")
    app = crear_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/admin/config", headers={"X-Admin-Key": "eeee"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_config_200_con_sesion_simulada(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "clave-admin-test-123")
    app = crear_app()

    async def _sesion_falsa() -> AsyncIterator[AsyncMock]:
        s = AsyncMock()
        s.get = AsyncMock(return_value=None)
        s.commit = AsyncMock()
        s.rollback = AsyncMock()
        yield s

    app.dependency_overrides[obtener_sesion_db] = _sesion_falsa
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/admin/config",
                headers={"X-Admin-Key": "clave-admin-test-123"},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["version"] == 0
    assert "meta_prompt" in cuerpo
    assert "modelo_llm_router" in cuerpo


@pytest.mark.asyncio
async def test_admin_config_401_sin_cabecera_x_admin_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "abc")
    app = crear_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/admin/config")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_usuarios_200_lista_vacia(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "clave-admin-test-123")
    app = crear_app()

    async def _sesion_falsa() -> AsyncIterator[AsyncMock]:
        s = AsyncMock()
        s.commit = AsyncMock()
        s.rollback = AsyncMock()
        yield s

    app.dependency_overrides[obtener_sesion_db] = _sesion_falsa
    try:
        with patch("src.api.routers.admin.RepositorioUsuarios") as cls_mock:
            inst = cls_mock.return_value
            inst.contar_total = AsyncMock(return_value=0)
            inst.listar_paginado = AsyncMock(return_value=[])
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get(
                    "/api/admin/usuarios",
                    headers={"X-Admin-Key": "clave-admin-test-123"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["total"] == 0
    assert cuerpo["items"] == []


class _SesionAdminEnMemoria:
    """Sesion minima para PATCH/GET config sin PostgreSQL real."""

    def __init__(self) -> None:
        self.fila: ConfigAdminM2 | None = None

    async def get(self, model: type, ident: object) -> object | None:
        if model is ConfigAdminM2 and ident == 1:
            return self.fila
        return None

    async def execute(self, _stmt: object) -> MagicMock:
        res = MagicMock()
        res.scalars.return_value.first.return_value = self.fila
        return res

    def add(self, obj: object) -> None:
        if isinstance(obj, ConfigAdminM2):
            self.fila = obj

    async def flush(self) -> None:
        if self.fila is not None:
            self.fila.updated_at = datetime.now(UTC)

    async def commit(self) -> None:
        return

    async def rollback(self) -> None:
        return


@pytest.mark.asyncio
async def test_admin_patch_luego_get_misma_sesion_hot_reload(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tras PATCH, un segundo GET en el mismo proceso observa la temperatura persistida (simulacion en memoria)."""
    monkeypatch.setenv("ADMIN_API_KEY", "clave-admin-test-123")
    app = crear_app()
    mem = _SesionAdminEnMemoria()

    async def _sesion_falsa() -> AsyncIterator[_SesionAdminEnMemoria]:
        yield mem

    app.dependency_overrides[obtener_sesion_db] = _sesion_falsa
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            headers = {"X-Admin-Key": "clave-admin-test-123", "Content-Type": "application/json"}
            r1 = await client.patch(
                "/api/admin/config",
                headers=headers,
                json={"version": 0, "temperatura_router": 0.37},
            )
            assert r1.status_code == 200
            assert r1.json()["temperatura_router"] == 0.37
            r2 = await client.get("/api/admin/config", headers={"X-Admin-Key": "clave-admin-test-123"})
            assert r2.status_code == 200
            assert r2.json()["temperatura_router"] == 0.37
            assert r2.json()["version"] >= 1
    finally:
        app.dependency_overrides.clear()
