"""Pruebas del cliente Telegram (sendMessage)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.integracion.telegram.cliente import ClienteTelegram
from src.integracion.telegram.errores import TelegramEnvioError


@pytest.mark.asyncio
async def test_enviar_mensaje_lanza_telegram_envio_error_sin_raise_for_status() -> None:
    """Errores 4xx no usan httpx.raise_for_status (evita URL con token en el mensaje)."""
    resp = MagicMock()
    resp.status_code = 400
    resp.text = '{"ok":false,"description":"Bad Request: chat not found"}'

    cliente_http = AsyncMock()
    cliente_http.post = AsyncMock(return_value=resp)

    cfg = MagicMock()
    cfg.telegram_bot_token = "token-prueba"

    cliente = ClienteTelegram(cfg, cliente_http=cliente_http)

    with pytest.raises(TelegramEnvioError) as exc_info:
        await cliente.enviar_mensaje(111111111, "Hola demo")

    assert exc_info.value.status_code == 400
    assert "chat not found" in exc_info.value.cuerpo
