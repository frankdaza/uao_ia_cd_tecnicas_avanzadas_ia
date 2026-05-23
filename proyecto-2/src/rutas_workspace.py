"""
Resolucion de raices del workspace (corpus en ``data/``) y del proyecto (``pyproject.toml``).

En el layout multi-proyecto, ``data/`` vive en la raiz del repositorio y el codigo
ejecutable bajo ``proyecto-2/``. Los scripts y la API deben usar ``encontrar_raiz_workspace``
para rutas bajo ``data/`` y ``encontrar_raiz_proyecto`` para ``config/``, ``.env``, etc.

Patron copiado de ``proyecto-1/src/rutas_workspace.py``; sin import cruzado entre proyectos.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

_MARCA_WORKSPACE = Path("data") / "markdown"


def encontrar_raiz_proyecto(inicio: Path | None = None) -> Path:
    """Sube directorios hasta hallar ``pyproject.toml`` (p. ej. ``proyecto-2/``)."""
    p = (inicio or Path.cwd()).resolve()
    for cand in [p, *p.parents]:
        if (cand / "pyproject.toml").is_file():
            return cand
    return p


def encontrar_raiz_workspace(inicio: Path | None = None) -> Path:
    """
    Raiz del workspace donde reside ``data/`` (hermano de ``proyecto-2/``).

    Orden: variable ``UAO_WORKSPACE_ROOT``; si el padre del proyecto tiene
    ``data/markdown``, ese padre; si el proyecto tiene ``data/markdown``, el proyecto;
    si no, la raiz del proyecto.
    """
    override = os.environ.get("UAO_WORKSPACE_ROOT", "").strip()
    if override:
        return Path(override).resolve()
    proyecto = encontrar_raiz_proyecto(inicio)
    padre = proyecto.parent
    if (padre / _MARCA_WORKSPACE).is_dir():
        return padre.resolve()
    if (proyecto / _MARCA_WORKSPACE).is_dir():
        return proyecto.resolve()
    return proyecto.resolve()


def encontrar_raiz_repo(inicio: Path | None = None) -> Path:
    """Alias historico: raiz del workspace (datos ``data/``)."""
    return encontrar_raiz_workspace(inicio)


def resolver_ruta_workspace(rel: str | Path, inicio: Path | None = None) -> Path:
    """Ruta absoluta bajo la raiz del workspace."""
    p = Path(rel)
    if p.is_absolute():
        return p.resolve()
    return (encontrar_raiz_workspace(inicio) / p).resolve()


def resolver_ruta_proyecto(rel: str | Path, inicio: Path | None = None) -> Path:
    """Ruta absoluta bajo la raiz del proyecto (``frontend/``, ``scripts/``, etc.)."""
    p = Path(rel)
    if p.is_absolute():
        return p.resolve()
    return (encontrar_raiz_proyecto(inicio) / p).resolve()


@lru_cache
def raiz_proyecto_desde_modulo() -> Path:
    """Raiz del proyecto anclada al modulo (cacheada)."""
    return encontrar_raiz_proyecto(Path(__file__).resolve())


@lru_cache
def raiz_workspace_desde_modulo() -> Path:
    """Raiz del workspace anclada al modulo (cacheada)."""
    return encontrar_raiz_workspace(Path(__file__).resolve())
