"""Errores de dominio al enviar mensajes por Bot API."""

from __future__ import annotations


class TelegramEnvioError(Exception):
    """Fallo de ``sendMessage`` sin exponer la URL con token en el mensaje."""

    def __init__(self, status_code: int, cuerpo: str) -> None:
        self.status_code = status_code
        self.cuerpo = cuerpo
        super().__init__(f"Telegram sendMessage fallo (HTTP {status_code})")


def es_error_envio_esperado(cuerpo: str) -> bool:
    """Errores 4xx habituales cuando el chat no es alcanzable (demo o usuario nuevo)."""
    texto = cuerpo.lower()
    return "chat not found" in texto or "bot was blocked" in texto
