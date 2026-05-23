"""Prueba de encolado de ingesta tras POST admin con PDF."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from tests.api.conftest import PDF_FIXTURE_MINIMO


@pytest.mark.asyncio
async def test_post_procedimiento_encola_ingesta_background(
    cliente_api: AsyncClient,
    cabecera_admin: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_ingesta = AsyncMock()
    monkeypatch.setattr(
        "src.api.routers.admin_procedimientos.ingesta_protocolo_background",
        mock_ingesta,
    )

    resp = await cliente_api.post(
        "/api/admin/procedimientos",
        headers=cabecera_admin,
        files={
            "metadata": (None, json.dumps({"codigo": "bg-ing", "nombre": "Con ingesta"}), "application/json"),
            "archivo": ("protocolo.pdf", PDF_FIXTURE_MINIMO, "application/pdf"),
        },
    )
    assert resp.status_code == 201
    assert resp.json()["indexacion_estado"] == "pendiente"

    # BackgroundTasks se ejecutan al cerrar la respuesta en ASGI transport
    mock_ingesta.assert_awaited_once()
    args = mock_ingesta.await_args
    assert args is not None
    assert str(args.args[1]) == resp.json()["id"]
