"""Enmascaramiento de PII en logs y documentacion (Ruta B TAAM)."""

from __future__ import annotations


def enmascarar_chat_id_telegram(chat_id: int | str) -> str:
    """Ultimos 4 digitos visibles; alineado con proyecto-2/privacidad_staff."""
    texto = str(chat_id).strip()
    if len(texto) <= 4:
        return "****"
    return "*" * (len(texto) - 4) + texto[-4:]
