"""Lectura de archivos Markdown con front matter YAML."""

from __future__ import annotations

from pathlib import Path

import yaml


def leer_markdown(ruta: Path) -> tuple[dict, str]:
    """Devuelve metadatos YAML y cuerpo sin front matter."""
    raw = ruta.read_text(encoding="utf-8")
    if raw.startswith("---"):
        partes = raw.split("---", 2)
        if len(partes) >= 3:
            meta = yaml.safe_load(partes[1]) or {}
            if not isinstance(meta, dict):
                meta = {}
            return meta, partes[2].strip()
    return {}, raw.strip()


def titulo_desde_meta(meta: dict, ruta: Path) -> str:
    """Titulo legible desde front matter o nombre de archivo."""
    for clave in ("title", "titulo", "nombre"):
        valor = meta.get(clave)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return ruta.stem.replace("-", " ").strip()
