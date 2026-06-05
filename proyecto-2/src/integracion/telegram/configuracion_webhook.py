"""Registro y consulta del webhook del bot (setWebhook / getWebhookInfo)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from src.configuracion import Configuracion, obtener_configuracion

RUTA_WEBHOOK_CANONICA = "/api/integracion/telegram/webhook"


class TelegramWebhookConfiguracionError(Exception):
    """Error de configuracion local (token o secret ausentes)."""


class TelegramWebhookValidacionError(Exception):
    """URL de webhook invalida para TAAM."""


class TelegramApiRespuestaError(Exception):
    """La Bot API de Telegram respondio ok=false."""

    def __init__(self, datos: dict[str, Any]) -> None:
        self.datos = datos
        super().__init__(str(datos.get("description") or datos))


@dataclass(frozen=True, slots=True)
class TelegramWebhookEstado:
    """Estado legible del webhook registrado en Telegram."""

    url: str
    configurado: bool
    pending_update_count: int
    last_error_message: str | None
    last_error_date: int | None


def validar_url_webhook(url: str) -> str:
    """Normaliza y valida la URL publica HTTPS del webhook."""
    normalizada = url.strip()
    if not normalizada:
        raise TelegramWebhookValidacionError("La URL del webhook no puede estar vacia.")

    parsed = urlparse(normalizada)
    if parsed.scheme != "https":
        raise TelegramWebhookValidacionError(
            "La URL debe usar HTTPS (Telegram no acepta HTTP plano en produccion)."
        )
    if not parsed.netloc:
        raise TelegramWebhookValidacionError("La URL debe incluir un host valido.")

    ruta = (parsed.path or "").rstrip("/")
    canonica = RUTA_WEBHOOK_CANONICA.rstrip("/")
    if ruta != canonica:
        raise TelegramWebhookValidacionError(
            f"La ruta debe ser exactamente {RUTA_WEBHOOK_CANONICA} "
            f"(recibida: {parsed.path or '/'})."
        )

    return normalizada


def _credenciales_telegram(cfg: Configuracion | None = None) -> tuple[str, str]:
    configuracion = cfg or obtener_configuracion()
    token = (configuracion.telegram_bot_token or "").strip()
    secret = (configuracion.telegram_webhook_secret or "").strip()
    if not token:
        raise TelegramWebhookConfiguracionError(
            "Defina TELEGRAM_BOT_TOKEN en el entorno del servidor."
        )
    if not secret:
        raise TelegramWebhookConfiguracionError(
            "Defina TELEGRAM_WEBHOOK_SECRET en el entorno del servidor."
        )
    return token, secret


def _url_api(token: str, metodo: str) -> str:
    return f"https://api.telegram.org/bot{token}/{metodo}"


async def _post_telegram(
    token: str,
    metodo: str,
    payload: dict[str, str | bool],
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as cliente:
        resp = await cliente.post(_url_api(token, metodo), json=payload)
        resp.raise_for_status()
        datos: dict[str, Any] = resp.json()
    if not datos.get("ok"):
        raise TelegramApiRespuestaError(datos)
    return datos


async def registrar_webhook(
    url: str,
    *,
    drop_pending_updates: bool = False,
    cfg: Configuracion | None = None,
) -> str:
    """Registra el webhook en Telegram (setWebhook). Devuelve la URL normalizada."""
    url_normalizada = validar_url_webhook(url)
    token, secret = _credenciales_telegram(cfg)
    payload: dict[str, str | bool] = {
        "url": url_normalizada,
        "secret_token": secret,
    }
    if drop_pending_updates:
        payload["drop_pending_updates"] = True
    await _post_telegram(token, "setWebhook", payload)
    return url_normalizada


async def obtener_estado_webhook(cfg: Configuracion | None = None) -> TelegramWebhookEstado:
    """Consulta getWebhookInfo y devuelve un resumen para el panel admin."""
    token, _ = _credenciales_telegram(cfg)
    datos = await _post_telegram(token, "getWebhookInfo", {})
    resultado = datos.get("result") or {}
    url = str(resultado.get("url") or "").strip()
    last_error = resultado.get("last_error_message")
    last_error_date = resultado.get("last_error_date")
    return TelegramWebhookEstado(
        url=url,
        configurado=bool(url),
        pending_update_count=int(resultado.get("pending_update_count") or 0),
        last_error_message=str(last_error).strip() if last_error else None,
        last_error_date=int(last_error_date) if last_error_date is not None else None,
    )
