"""Conflictos de version admin y reflejo de PATCH RAG en el bundle de runtime."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

from src.api.configuracion import obtener_configuracion
from src.api.dependencias import obtener_sesion_db
from src.api.main import crear_app
from src.api.servicios.agente_m2_config import ServicioAgenteM2Config
from src.persistencia.modelos import ConfigAdminM2


@pytest.fixture(autouse=True)
def limpiar_cache_config() -> None:
    obtener_configuracion.cache_clear()
    yield
    obtener_configuracion.cache_clear()


class _SesionAdminEnMemoria:
    """Sesion minima para PATCH/GET config sin PostgreSQL real."""

    def __init__(self) -> None:
        self.fila: ConfigAdminM2 | None = None

    async def get(self, model: type, ident: object) -> object | None:
        if model is ConfigAdminM2 and ident == 1:
            return self.fila
        return None

    async def execute(self, _stmt: object) -> object:
        from unittest.mock import MagicMock

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
async def test_patch_version_desactualizada_retorna_409(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ADMIN_API_KEY", "clave-admin-test-123")
    app = crear_app()
    mem = _SesionAdminEnMemoria()
    mem.fila = ConfigAdminM2(
        id=1,
        version=4,
        updated_at=datetime.now(UTC),
    )

    async def _sesion_falsa() -> AsyncIterator[_SesionAdminEnMemoria]:
        yield mem

    app.dependency_overrides[obtener_sesion_db] = _sesion_falsa
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                "/api/admin/config",
                headers={
                    "X-Admin-Key": "clave-admin-test-123",
                    "Content-Type": "application/json",
                },
                json={"version": 1, "rag_mmr_lambda": 0.2},
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 409
    detalle = resp.json()["detail"].lower()
    assert "recargue" in detalle or "reintente" in detalle


@pytest.mark.asyncio
async def test_patch_rag_mmr_lambda_servicio_bundle_siguiente_lectura(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tras PATCH de lambda, ServicioAgenteM2Config expone el mismo valor en el bundle."""
    monkeypatch.setenv("ADMIN_API_KEY", "clave-admin-test-123")
    monkeypatch.setenv("MOCK_LLM", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-falso")
    app = crear_app()
    mem = _SesionAdminEnMemoria()

    async def _sesion_falsa() -> AsyncIterator[_SesionAdminEnMemoria]:
        yield mem

    app.dependency_overrides[obtener_sesion_db] = _sesion_falsa
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            headers = {
                "X-Admin-Key": "clave-admin-test-123",
                "Content-Type": "application/json",
            }
            r1 = await client.patch(
                "/api/admin/config",
                headers=headers,
                json={"version": 0, "rag_mmr_lambda": 0.31},
            )
            assert r1.status_code == 200
            assert r1.json()["rag_mmr_lambda"] == 0.31
    finally:
        app.dependency_overrides.clear()

    sesion = AsyncMock(spec=AsyncSession)
    sesion.get = AsyncMock(return_value=mem.fila)

    svc = ServicioAgenteM2Config(sesion)
    bundle = await svc.construir_bundle_tiempo_ejecucion()
    assert abs(bundle.rag_mmr_lambda - 0.31) < 1e-9
