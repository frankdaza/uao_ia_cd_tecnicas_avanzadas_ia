"""Pruebas unitarias de validacion del webhook Telegram."""

from __future__ import annotations

import pytest

from src.integracion.telegram.configuracion_webhook import (
    RUTA_WEBHOOK_CANONICA,
    TelegramWebhookValidacionError,
    validar_url_webhook,
)


def test_validar_url_webhook_acepta_https_canonica() -> None:
    url = f"https://tunnel.example{RUTA_WEBHOOK_CANONICA}"
    assert validar_url_webhook(url) == url


def test_validar_url_webhook_rechaza_http() -> None:
    url = f"http://tunnel.example{RUTA_WEBHOOK_CANONICA}"
    with pytest.raises(TelegramWebhookValidacionError, match="HTTPS"):
        validar_url_webhook(url)


def test_validar_url_webhook_rechaza_ruta_incorrecta() -> None:
    with pytest.raises(TelegramWebhookValidacionError, match=RUTA_WEBHOOK_CANONICA):
        validar_url_webhook("https://tunnel.example/api/otro/webhook")
