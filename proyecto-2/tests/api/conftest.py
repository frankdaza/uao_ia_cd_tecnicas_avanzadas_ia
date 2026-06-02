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

MD_FIXTURE_MINIMO = (
    b"""---
titulo: Protocolo demo colecistectomia
idioma: es
---
## Cuidados postoperatorios
Repita las indicaciones de su equipo tratante.
"""
    + b"Texto util del protocolo. " * 20
)

MD_FIXTURE_FM_INVALIDO = b"""---
titulo: [no-es-yaml-valido
---
Cuerpo.
"""

MD_FIXTURE_CUERPO_VACIO = b"""---
titulo: Vacio
---
"""

CLAVE_ADMIN_TEST = "clave-admin-taam-test"
SECRETO_TELEGRAM_TEST = "secreto-telegram-taam-test"
JWT_SECRETO_STAFF_TEST = "jwt-secreto-staff-taam-test-32bytes-min"
PASSWORD_STAFF_ASISTENTE_TEST = "demo-pass-asistente-taam-test"
PASSWORD_STAFF_ADMIN_TEST = "demo-pass-admin-taam-test"
EMAIL_ASISTENTE_DEMO = "asistente@demo.taam"
EMAIL_ADMIN_DEMO = "admin@demo.taam"


@pytest.fixture
def clave_admin(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("ADMIN_API_KEY", CLAVE_ADMIN_TEST)
    obtener_configuracion.cache_clear()
    return CLAVE_ADMIN_TEST


@pytest.fixture
def cabecera_admin(clave_admin: str) -> dict[str, str]:
    return {"X-Admin-Key": clave_admin}


@pytest.fixture
def jwt_staff(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("STAFF_JWT_SECRET", JWT_SECRETO_STAFF_TEST)
    monkeypatch.setenv("STAFF_DEMO_ASISTENTE_PASSWORD", PASSWORD_STAFF_ASISTENTE_TEST)
    monkeypatch.setenv("STAFF_DEMO_CLINICO_PASSWORD", "demo-pass-clinico-taam-test")
    monkeypatch.setenv("STAFF_DEMO_ADMIN_PASSWORD", PASSWORD_STAFF_ADMIN_TEST)
    obtener_configuracion.cache_clear()
    return JWT_SECRETO_STAFF_TEST


@pytest.fixture
async def usuarios_staff_sembrados(app_api, jwt_staff: str) -> None:
    from src.persistencia.semilla_staff_demo import sembrar_usuarios_staff_demo

    cfg = obtener_configuracion()
    factory = app_api.state.session_factory
    async with factory() as sesion:
        await sembrar_usuarios_staff_demo(sesion, cfg)
        await sesion.commit()


@pytest.fixture
async def token_staff_asistente(
    cliente_api,
    usuarios_staff_sembrados: None,  # noqa: ARG001
) -> str:
    from httpx import AsyncClient

    assert isinstance(cliente_api, AsyncClient)
    resp = await cliente_api.post(
        "/api/auth/staff/login",
        json={
            "email": "asistente@demo.taam",
            "password": PASSWORD_STAFF_ASISTENTE_TEST,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def cabecera_staff(token_staff_asistente: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_staff_asistente}"}


@pytest.fixture
def secreto_telegram(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", SECRETO_TELEGRAM_TEST)
    obtener_configuracion.cache_clear()
    return SECRETO_TELEGRAM_TEST


@pytest.fixture
def cabecera_telegram(secreto_telegram: str) -> dict[str, str]:
    return {"X-Telegram-Bot-Api-Secret-Token": secreto_telegram}


@pytest.fixture(autouse=True)
def recordatorios_job_off_en_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Evita tarea asyncio de recordatorios en la mayoria de pruebas API."""
    monkeypatch.setenv("RECORDATORIOS_JOB_HABILITADO", "false")
    obtener_configuracion.cache_clear()


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
    jwt_staff: str,
    secreto_telegram: str,
):
    """AsyncClient contra ``app_api``."""
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(
        transport=ASGITransport(app=app_api),
        base_url="http://test",
    ) as client:
        yield client
