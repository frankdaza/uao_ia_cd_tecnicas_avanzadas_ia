"""Pruebas admin del webhook Telegram (setWebhook / getWebhookInfo)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from src.configuracion import obtener_configuracion
from tests.api.conftest import (
    EMAIL_ADMIN_DEMO,
    PASSWORD_STAFF_ADMIN_TEST,
    SECRETO_TELEGRAM_TEST,
)

URL_WEBHOOK_VALIDA = "https://tunnel.example/api/integracion/telegram/webhook"


@pytest.fixture
def telegram_bot_token(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:test-bot-token")
    obtener_configuracion.cache_clear()
    return "123456:test-bot-token"


@pytest.fixture
async def token_staff_admin(
    cliente_api: AsyncClient,
    usuarios_staff_sembrados: None,  # noqa: ARG001
) -> str:
    resp = await cliente_api.post(
        "/api/auth/staff/login",
        json={"email": EMAIL_ADMIN_DEMO, "password": PASSWORD_STAFF_ADMIN_TEST},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def cabecera_staff_admin(token_staff_admin: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_staff_admin}"}


def _respuesta_telegram_json(datos: dict) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = datos
    return resp


@pytest.fixture
def mock_telegram_http(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Mock de httpx.AsyncClient hacia api.telegram.org."""
    post = AsyncMock(
        return_value=_respuesta_telegram_json(
            {
                "ok": True,
                "result": {
                    "url": URL_WEBHOOK_VALIDA,
                    "pending_update_count": 2,
                    "last_error_message": "Connection timed out",
                    "last_error_date": 1710000000,
                },
            }
        )
    )
    cliente = AsyncMock()
    cliente.post = post
    cliente.__aenter__.return_value = cliente
    cliente.__aexit__.return_value = None

    factory = MagicMock(return_value=cliente)
    monkeypatch.setattr(
        "src.integracion.telegram.configuracion_webhook.httpx.AsyncClient",
        factory,
    )
    return post


@pytest.mark.asyncio
async def test_get_telegram_webhook_admin_jwt(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
    telegram_bot_token: str,  # noqa: ARG001
    mock_telegram_http: AsyncMock,
) -> None:
    resp = await cliente_api.get(
        "/api/admin/telegram-webhook",
        headers=cabecera_staff_admin,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["url"] == URL_WEBHOOK_VALIDA
    assert data["configurado"] is True
    assert data["pending_update_count"] == 2
    assert data["last_error_message"] == "Connection timed out"
    assert data["last_error_date"] == 1710000000
    mock_telegram_http.assert_awaited_once()
    assert mock_telegram_http.await_args.args[0].endswith("/getWebhookInfo")


@pytest.mark.asyncio
async def test_post_telegram_webhook_admin_jwt(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
    telegram_bot_token: str,  # noqa: ARG001
    mock_telegram_http: AsyncMock,
) -> None:
    mock_telegram_http.return_value = _respuesta_telegram_json({"ok": True, "result": True})

    resp = await cliente_api.post(
        "/api/admin/telegram-webhook",
        headers=cabecera_staff_admin,
        json={"url": URL_WEBHOOK_VALIDA, "drop_pending_updates": True},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["ok"] is True
    assert data["url"] == URL_WEBHOOK_VALIDA

    assert mock_telegram_http.await_count == 1
    payload = mock_telegram_http.await_args.kwargs["json"]
    assert payload["url"] == URL_WEBHOOK_VALIDA
    assert payload["secret_token"] == SECRETO_TELEGRAM_TEST
    assert payload["drop_pending_updates"] is True


@pytest.mark.asyncio
async def test_get_telegram_webhook_staff_no_admin_403(
    cliente_api: AsyncClient,
    cabecera_staff: dict[str, str],
    telegram_bot_token: str,  # noqa: ARG001
    mock_telegram_http: AsyncMock,  # noqa: ARG001
) -> None:
    resp = await cliente_api.get(
        "/api/admin/telegram-webhook",
        headers=cabecera_staff,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_post_telegram_webhook_url_invalida_422(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
    telegram_bot_token: str,  # noqa: ARG001
) -> None:
    resp = await cliente_api.post(
        "/api/admin/telegram-webhook",
        headers=cabecera_staff_admin,
        json={"url": "http://inseguro.example/api/integracion/telegram/webhook"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_post_telegram_webhook_ruta_incorrecta_422(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
    telegram_bot_token: str,  # noqa: ARG001
) -> None:
    resp = await cliente_api.post(
        "/api/admin/telegram-webhook",
        headers=cabecera_staff_admin,
        json={"url": "https://tunnel.example/api/otro/webhook"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_telegram_webhook_sin_token_503(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.integracion.telegram.configuracion_webhook import (
        TelegramWebhookConfiguracionError,
    )

    def _sin_token(cfg=None):  # noqa: ANN001, ARG001
        raise TelegramWebhookConfiguracionError(
            "Defina TELEGRAM_BOT_TOKEN en el entorno del servidor."
        )

    monkeypatch.setattr(
        "src.integracion.telegram.configuracion_webhook._credenciales_telegram",
        _sin_token,
    )

    resp = await cliente_api.get(
        "/api/admin/telegram-webhook",
        headers=cabecera_staff_admin,
    )
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_post_telegram_webhook_telegram_error_502(
    cliente_api: AsyncClient,
    cabecera_staff_admin: dict[str, str],
    telegram_bot_token: str,  # noqa: ARG001
    mock_telegram_http: AsyncMock,
) -> None:
    mock_telegram_http.return_value = _respuesta_telegram_json(
        {"ok": False, "description": "Bad Request: invalid webhook URL"}
    )

    resp = await cliente_api.post(
        "/api/admin/telegram-webhook",
        headers=cabecera_staff_admin,
        json={"url": URL_WEBHOOK_VALIDA},
    )
    assert resp.status_code == 502
