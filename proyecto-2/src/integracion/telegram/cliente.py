"""Cliente async de la Bot API de Telegram (sendMessage)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from src.configuracion import Configuracion, obtener_configuracion
from src.integracion.telegram.errores import TelegramEnvioError
from src.integracion.telegram.formateo import (
    es_markdown_probable,
    markdown_a_html_telegram,
)

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

    def _token(self) -> str | None:
        token = (self._cfg.telegram_bot_token or "").strip()
        return token or None

    def _url_api(self, metodo: str) -> str | None:
        token = self._token()
        if not token:
            return None
        return f"https://api.telegram.org/bot{token}/{metodo}"

    def _url_send_message(self) -> str | None:
        return self._url_api("sendMessage")

    async def enviar_mensaje(
        self,
        chat_id: int,
        texto: str,
        *,
        formatear_markdown: bool = False,
    ) -> None:
        """Envia texto al chat; no lanza si falta token (solo log en dev/tests)."""
        url = self._url_send_message()
        if not url:
            logger.warning(
                "telegram_send_omitido chat_id=%s (TELEGRAM_BOT_TOKEN vacio)",
                chat_id,
            )
            return

        texto_plano = truncar_texto_telegram(texto)
        if not texto_plano:
            return

        usar_html = formatear_markdown and es_markdown_probable(texto)
        if usar_html:
            cuerpo = truncar_texto_telegram(markdown_a_html_telegram(texto))
            payload: dict[str, Any] = {
                "chat_id": chat_id,
                "text": cuerpo,
                "parse_mode": "HTML",
            }
        else:
            payload = {
                "chat_id": chat_id,
                "text": texto_plano,
            }

        if self._cliente_http is not None:
            await self._enviar_payload(
                self._cliente_http,
                url,
                payload,
                texto_plano=texto_plano,
                reintentar_plano=usar_html,
            )
            return

        async with httpx.AsyncClient(timeout=30.0) as cliente:
            await self._enviar_payload(
                cliente,
                url,
                payload,
                texto_plano=texto_plano,
                reintentar_plano=usar_html,
            )

    async def _enviar_payload(
        self,
        cliente: httpx.AsyncClient,
        url: str,
        payload: dict[str, Any],
        *,
        texto_plano: str,
        reintentar_plano: bool,
    ) -> None:
        resp = await cliente.post(url, json=payload)
        if resp.status_code == 400 and reintentar_plano and payload.get("parse_mode"):
            logger.warning(
                "telegram_sendMessage_html_fallo chat_id=%s; reintento texto plano",
                payload.get("chat_id"),
            )
            payload_plano: dict[str, Any] = {
                "chat_id": payload["chat_id"],
                "text": texto_plano,
            }
            resp = await cliente.post(url, json=payload_plano)
        if resp.status_code >= 400:
            cuerpo = resp.text[:500]
            logger.error(
                "telegram_sendMessage_fallo status=%s body=%s chat_id=%s",
                resp.status_code,
                cuerpo,
                payload.get("chat_id"),
            )
            raise TelegramEnvioError(resp.status_code, cuerpo)

    async def obtener_ruta_archivo(self, file_id: str) -> str:
        """Llama ``getFile`` y retorna ``file_path`` relativo de Telegram."""
        url = self._url_api("getFile")
        if not url:
            raise TelegramEnvioError(0, "TELEGRAM_BOT_TOKEN vacio")

        async def _pedir(cliente: httpx.AsyncClient) -> str:
            resp = await cliente.post(url, json={"file_id": file_id})
            if resp.status_code >= 400:
                cuerpo = resp.text[:500]
                raise TelegramEnvioError(resp.status_code, cuerpo)
            datos = resp.json()
            resultado = datos.get("result") if isinstance(datos, dict) else None
            ruta = resultado.get("file_path") if isinstance(resultado, dict) else None
            if not isinstance(ruta, str) or not ruta.strip():
                raise TelegramEnvioError(resp.status_code, "getFile sin file_path")
            return ruta.strip()

        if self._cliente_http is not None:
            return await _pedir(self._cliente_http)
        async with httpx.AsyncClient(timeout=60.0) as cliente:
            return await _pedir(cliente)

    async def descargar_archivo(self, file_path: str) -> bytes:
        """Descarga bytes desde ``https://api.telegram.org/file/bot<token>/<file_path>``."""
        token = self._token()
        if not token:
            raise TelegramEnvioError(0, "TELEGRAM_BOT_TOKEN vacio")
        url = f"https://api.telegram.org/file/bot{token}/{file_path.lstrip('/')}"

        async def _descargar(cliente: httpx.AsyncClient) -> bytes:
            resp = await cliente.get(url)
            if resp.status_code >= 400:
                raise TelegramEnvioError(resp.status_code, resp.text[:500])
            return resp.content

        if self._cliente_http is not None:
            return await _descargar(self._cliente_http)
        async with httpx.AsyncClient(timeout=120.0) as cliente:
            return await _descargar(cliente)

    async def descargar_por_file_id(self, file_id: str) -> bytes:
        """Conveniencia: ``getFile`` + descarga."""
        ruta = await self.obtener_ruta_archivo(file_id)
        return await self.descargar_archivo(ruta)

    async def aclose(self) -> None:
        if self._cliente_propio and self._cliente_http is not None:
            await self._cliente_http.aclose()
