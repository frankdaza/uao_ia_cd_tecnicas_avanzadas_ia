"""Fixtures compartidas para pruebas del API TAAM."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.configuracion import obtener_configuracion

# PDF minimo valido (magic %PDF) para pruebas de upload.
PDF_FIXTURE_MINIMO = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 3 3]/Parent 2 0 R>>endobj\n"
    b"trailer<</Root 1 0 R/Size 4>>\n"
    b"%%EOF\n"
)

CLAVE_ADMIN_TEST = "clave-admin-taam-test"
CLAVE_STAFF_TEST = "clave-staff-taam-test"
SECRETO_TELEGRAM_TEST = "secreto-telegram-taam-test"


@pytest.fixture
def clave_admin(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("ADMIN_API_KEY", CLAVE_ADMIN_TEST)
    obtener_configuracion.cache_clear()
    return CLAVE_ADMIN_TEST


@pytest.fixture
def cabecera_admin(clave_admin: str) -> dict[str, str]:
    return {"X-Admin-Key": clave_admin}


@pytest.fixture
def clave_staff(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("STAFF_API_KEY", CLAVE_STAFF_TEST)
    obtener_configuracion.cache_clear()
    return CLAVE_STAFF_TEST


@pytest.fixture
def cabecera_staff(clave_staff: str) -> dict[str, str]:
    return {"X-Staff-Key": clave_staff}


@pytest.fixture
def secreto_telegram(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", SECRETO_TELEGRAM_TEST)
    obtener_configuracion.cache_clear()
    return SECRETO_TELEGRAM_TEST


@pytest.fixture
def cabecera_telegram(secreto_telegram: str) -> dict[str, str]:
    return {"X-Telegram-Bot-Api-Secret-Token": secreto_telegram}


@pytest.fixture
async def app_api(workspace_tmp: None):
    """App FastAPI con BD SQLite en memoria (lifespan activo durante el test)."""
    from src.api.main import crear_app

    app = crear_app(url_bd="sqlite+aiosqlite:///:memory:")
    async with app.router.lifespan_context(app):
        yield app


@pytest.fixture
async def cliente_api(
    app_api,
    clave_admin: str,
    clave_staff: str,
    secreto_telegram: str,
):
    """AsyncClient contra ``app_api``."""
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(
        transport=ASGITransport(app=app_api),
        base_url="http://test",
    ) as client:
        yield client
