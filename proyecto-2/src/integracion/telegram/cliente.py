"""Cliente async de la Bot API de Telegram (sendMessage)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.configuracion import Configuracion, obtener_configuracion

logger = logging.getLogger(__name__)

LIMITE_TEXTO_TELEGRAM = 4096


def truncar_texto_telegram(texto: str, maximo: int = LIMITE_TEXTO_TELEGRAM) -> str:
    """Trunca el texto al limite de Telegram (4096 caracteres)."""
    limpio = texto.strip()
    if len(limpio) <= maximo:
        return limpio
    return limpio[: maximo - 3] + "..."


class ClienteTelegram:
    """Envio de mensajes via ``sendMessage`` (httpx async)."""

    def __init__(
        self,
        cfg: Configuracion | None = None,
        *,
        cliente_http: httpx.AsyncClient | None = None,
    ) -> None:
        self._cfg = cfg or obtener_configuracion()
        self._cliente_http = cliente_http
        self._cliente_propio = cliente_http is None

    def _url_send_message(self) -> str | None:
        token = (self._cfg.telegram_bot_token or "").strip()
        if not token:
            return None
        return f"https://api.telegram.org/bot{token}/sendMessage"

    async def enviar_mensaje(self, chat_id: int, texto: str) -> None:
        """Envia texto al chat; no lanza si falta token (solo log en dev/tests)."""
        url = self._url_send_message()
        cuerpo = truncar_texto_telegram(texto)
        if not url:
            logger.warning(
                "telegram_send_omitido chat_id=%s (TELEGRAM_BOT_TOKEN vacio)",
                chat_id,
            )
            return
        if not cuerpo:
            return

        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": cuerpo,
        }

        if self._cliente_http is not None:
            await self._enviar_con_cliente(self._cliente_http, url, payload)
            return

        async with httpx.AsyncClient(timeout=30.0) as cliente:
            await self._enviar_con_cliente(cliente, url, payload)

    async def _enviar_con_cliente(
        self,
        cliente: httpx.AsyncClient,
        url: str,
        payload: dict[str, Any],
    ) -> None:
        resp = await cliente.post(url, json=payload)
        if resp.status_code >= 400:
            logger.error(
                "telegram_sendMessage_fallo status=%s body=%s",
                resp.status_code,
                resp.text[:500],
            )
            resp.raise_for_status()

    async def aclose(self) -> None:
        if self._cliente_propio and self._cliente_http is not None:
            await self._cliente_http.aclose()
