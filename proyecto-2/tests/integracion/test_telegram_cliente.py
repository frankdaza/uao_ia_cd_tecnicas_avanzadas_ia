"""Pruebas del cliente Telegram (sendMessage)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.integracion.telegram.cliente import ClienteTelegram
from src.integracion.telegram.errores import TelegramEnvioError

_TEXTO_MD = """### Titulo:
- **Item**: detalle.
"""


@pytest.mark.asyncio
async def test_enviar_mensaje_con_markdown_usa_parse_mode_html() -> None:
    resp_ok = MagicMock()
    resp_ok.status_code = 200
    resp_ok.text = '{"ok":true}'

    cliente_http = AsyncMock()
    cliente_http.post = AsyncMock(return_value=resp_ok)

    cfg = MagicMock()
    cfg.telegram_bot_token = "token-prueba"

    cliente = ClienteTelegram(cfg, cliente_http=cliente_http)
    await cliente.enviar_mensaje(111111111, _TEXTO_MD, formatear_markdown=True)

    payload = cliente_http.post.await_args.kwargs["json"]
    assert payload["parse_mode"] == "HTML"
    assert "###" not in payload["text"]
    assert "<b>" in payload["text"]


@pytest.mark.asyncio
async def test_enviar_mensaje_html_falla_reintenta_plano() -> None:
    resp_error = MagicMock()
    resp_error.status_code = 400
    resp_error.text = '{"ok":false,"description":"Bad Request: can\'t parse entities"}'
    resp_ok = MagicMock()
    resp_ok.status_code = 200
    resp_ok.text = '{"ok":true}'

    cliente_http = AsyncMock()
    cliente_http.post = AsyncMock(side_effect=[resp_error, resp_ok])

    cfg = MagicMock()
    cfg.telegram_bot_token = "token-prueba"

    cliente = ClienteTelegram(cfg, cliente_http=cliente_http)
    await cliente.enviar_mensaje(111111111, _TEXTO_MD, formatear_markdown=True)

    assert cliente_http.post.await_count == 2
    segundo = cliente_http.post.await_args_list[1].kwargs["json"]
    assert "parse_mode" not in segundo
    assert "###" in segundo["text"]


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
