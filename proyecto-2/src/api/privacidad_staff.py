"""Enmascaramiento de PII en respuestas staff segun rol (UC-MVP-05)."""

from __future__ import annotations


def enmascarar_valor_sensible(valor: str, rol: str) -> str:
    """Ultimos 4 caracteres visibles para rol ``asistente``."""
    if rol in ("clinico", "admin"):
        return valor
    texto = valor.strip()
    if len(texto) <= 4:
        return "****"
    return "*" * (len(texto) - 4) + texto[-4:]


def enmascarar_chat_id_telegram(chat_id: int, rol: str) -> str:
    return enmascarar_valor_sensible(str(chat_id), rol)
