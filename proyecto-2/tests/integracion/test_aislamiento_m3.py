"""Regresión de aislamiento M3 (TAAM) frente a M2 (proyecto-1).

Ver decision-7: proyecto-2 no debe importar runtime de proyecto-1.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.main import crear_app

_RAIZ_PROYECTO_2 = Path(__file__).resolve().parents[2]
_SRC = _RAIZ_PROYECTO_2 / "src"
_IMPORTS_PROHIBIDOS = (
    "proyecto_1",
    "proyecto-1",
)


def _archivos_python_bajo_src() -> list[Path]:
    return sorted(_SRC.rglob("*.py"))


def _imports_en_archivo(ruta: Path) -> set[str]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))
    encontrados: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                encontrados.add(alias.name.split(".")[0])
        elif isinstance(nodo, ast.ImportFrom) and nodo.module:
            encontrados.add(nodo.module.split(".")[0])
    return encontrados


@pytest.mark.parametrize("ruta_py", _archivos_python_bajo_src(), ids=lambda p: p.relative_to(_SRC).as_posix())
def test_src_no_importa_proyecto_1(ruta_py: Path) -> None:
    imports = _imports_en_archivo(ruta_py)
    for prohibido in _IMPORTS_PROHIBIDOS:
        assert prohibido not in imports, (
            f"{ruta_py.relative_to(_RAIZ_PROYECTO_2)} no debe importar {prohibido!r}"
        )


def test_paquete_src_no_carga_proyecto_1() -> None:
    modulos_src = [k for k in sys.modules if k == "src" or k.startswith("src.")]
    assert modulos_src, "se esperaba al menos un submodulo src cargado en la sesion de tests"
    for nombre in sys.modules:
        if nombre.startswith("proyecto_1") or nombre.startswith("proyecto-1"):
            pytest.fail(f"modulo M2 cargado en runtime TAAM: {nombre}")


def test_salud_identifica_proyecto_taam() -> None:
    app = crear_app(url_bd="sqlite+aiosqlite:///:memory:")
    with TestClient(app) as cliente:
        resp = cliente.get("/api/salud")
    assert resp.status_code == 200
    assert resp.json()["proyecto"] == "taam"


def test_docker_compose_documenta_puertos_distintos_m2() -> None:
    compose = (_RAIZ_PROYECTO_2 / "docker-compose.yml").read_text(encoding="utf-8")
    assert "8001" in compose or ":8001" in compose
    assert "15433" in compose
    assert "6334" in compose
    assert "8000" not in compose.split("#", 1)[0]
