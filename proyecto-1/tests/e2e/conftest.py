"""Fixtures para pruebas E2E del Modulo 2 (API HTTP real)."""

from __future__ import annotations

import os
import uuid

import httpx
import pytest
import pytest_asyncio


@pytest.fixture
def base_url_e2e() -> str:
    """Origen HTTP de la API (docker-compose suele publicar 8000 en el host)."""
    raw = (
        os.environ.get("E2E_BASE_URL")
        or os.environ.get("BASE_URL")
        or "http://127.0.0.1:8000"
    )
    return raw.rstrip("/")


@pytest_asyncio.fixture
async def cliente_http_e2e(base_url_e2e: str) -> httpx.AsyncClient:
    timeout = httpx.Timeout(
        connect=15.0,
        read=float(os.environ.get("E2E_TIMEOUT_READ", "120")),
        write=30.0,
        pool=15.0,
    )
    async with httpx.AsyncClient(base_url=base_url_e2e, timeout=timeout) as client:
        try:
            r = await client.get("/api/salud")
        except httpx.RequestError as exc:
            pytest.skip(f"No se alcanza la API en {base_url_e2e}: {exc}")
        if r.status_code != 200:
            pytest.skip(
                f"GET /api/salud devolvio HTTP {r.status_code} en {base_url_e2e}"
            )
        yield client


@pytest_asyncio.fixture
async def sesion_m2_e2e(cliente_http_e2e: httpx.AsyncClient) -> dict[str, str]:
    """Inicia sesion y devuelve ``session_id`` canonico (cookie + cabecera)."""
    doc = f"e2e61-{uuid.uuid4().hex[:16]}"
    r = await cliente_http_e2e.post(
        "/api/sesiones",
        json={"documento_identidad": doc, "nombre": "Usuario prueba E2E"},
    )
    if r.status_code != 200:
        pytest.skip(f"No se pudo crear sesion (HTTP {r.status_code}): {r.text[:500]}")
    body = r.json()
    return {"session_id": str(body["session_id"]), "documento_identidad": doc}


@pytest.fixture
def e2e_modo_llm_real() -> bool:
    """Si es True, no se exige ``MOCK_LLM`` en el servidor (aserciones de tool mas laxas)."""
    return os.environ.get("E2E_LLM_REAL", "").strip() == "1"
