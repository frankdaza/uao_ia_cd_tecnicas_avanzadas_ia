"""Parseo de marcas de tiempo en registros OpenFang (JSONL / SQLite)."""

from __future__ import annotations

from datetime import UTC, datetime

_CLAVES_MARCA_TIEMPO = ("ts", "timestamp", "created_at", "time", "at")


def parsear_marca_tiempo(valor: object) -> datetime | None:
    """Convierte epoch, ISO-8601 o cadena vacia a datetime UTC."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return datetime.fromtimestamp(float(valor), tz=UTC)
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            return None
        if texto.endswith("Z"):
            texto = texto[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(texto)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None


def extraer_marca_tiempo(registro: dict) -> datetime | None:
    """Primera marca de tiempo reconocida en el registro."""
    for clave in _CLAVES_MARCA_TIEMPO:
        parsed = parsear_marca_tiempo(registro.get(clave))
        if parsed is not None:
            return parsed
    return None


def marca_tiempo_a_iso(marca: datetime | None) -> str:
    """Serializa a ISO-8601 UTC para parquet."""
    if marca is None:
        return ""
    return marca.astimezone(UTC).isoformat()
