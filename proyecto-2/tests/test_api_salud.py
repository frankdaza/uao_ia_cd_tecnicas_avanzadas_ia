"""Prueba del endpoint GET /api/salud."""

from __future__ import annotations

from fastapi.testclient import TestClient

from src.api.main import crear_app


def test_salud_ok_taam() -> None:
    app = crear_app(url_bd="sqlite+aiosqlite:///:memory:")
    with TestClient(app) as cliente:
        resp = cliente.get("/api/salud")
    assert resp.status_code == 200
    cuerpo = resp.json()
    assert cuerpo["estado"] == "ok"
    assert cuerpo["proyecto"] == "taam"
    assert cuerpo["version"] == "0.1.0"
