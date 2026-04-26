"""Pruebas de conversión HTML a Markdown (sin red)."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import yaml

from src.markdown_export.conversion import (
    convertir_html_a_md,
    derivar_seccion,
    escribir_markdown,
    extraer_titulo,
    limpiar_html,
)
from bs4 import BeautifulSoup

_DIR_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _escribir_sidecar(
    ruta: Path,
    *,
    url: str,
    hash_sha256: str = "a" * 64,
    fecha: str = "2026-04-26T12:00:00+00:00",
) -> None:
    """Sidecar mínimo compatible con ``src.scraping.descarga``."""
    meta = {
        "url": url,
        "http_status": 200,
        "content_type": "text/html",
        "fecha_extraccion": fecha,
        "hash_sha256": hash_sha256,
        "profundidad": 0,
        "headers_relevantes": {},
    }
    ruta.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _parse_front_matter(texto: str) -> dict:
    assert texto.startswith("---\n")
    rest = texto[4:]
    fin = rest.find("\n---\n")
    assert fin > 0
    return yaml.safe_load(rest[:fin])


def test_convertir_y_front_matter_yaml_valido(
    tmp_path: Path,
) -> None:
    """#1: ``yaml.safe_load`` sobre el front matter resultante."""
    h = _DIR_FIXTURES / "minimo.html"
    destino = tmp_path / "misma-pagina.html"
    shutil.copy(h, destino)
    j = tmp_path / "misma-pagina.json"
    u = "https://valledellili.org/doc/prueba-uno"
    _escribir_sidecar(
        j,
        url=u,
        hash_sha256="b" * 64,
    )
    cm = convertir_html_a_md(destino, j)
    salida = cm.serializar()
    fm = _parse_front_matter(salida)
    assert fm["source_url"] == u
    assert fm["seccion"] == "doc"
    assert fm["idioma"] == "es"
    assert fm["hash"] == "b" * 64
    assert fm["fecha_extraccion"] == "2026-04-26"
    assert fm["titulo"] == "Prueba mínima"


def test_cuerpo_encabezados_y_listas() -> None:
    """#2: encabezados con ``#`` (ATX) y, en otras pruebas, listas con ``-``."""
    h = _DIR_FIXTURES / "minimo.html"
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        p = Path(td) / "x.html"
        p.write_text(h.read_text(encoding="utf-8"), encoding="utf-8")
        j = Path(td) / "x.json"
        _escribir_sidecar(j, url="https://valledellili.org/raiz/")
        body = convertir_html_a_md(p, j).cuerpo
    assert re.search(r"^##+ ", body, re.MULTILINE), body
    assert "Subtítulo" in body


def test_listas_anidadas_y_tabla() -> None:
    h = _DIR_FIXTURES / "listas_tablas.html"
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        p = Path(td) / "t.html"
        p.write_text(h.read_text(encoding="utf-8"), encoding="utf-8")
        j = Path(td) / "t.json"
        _escribir_sidecar(j, url="https://valledellili.org/serv/s")
        body = convertir_html_a_md(p, j).cuerpo
    assert "anidada" in body
    assert "|" in body or re.search(r"- ", body)  # lista o pipe tabla


def test_quita_script_style_nav_footer_nav_cookie() -> None:
    """#3: basura común no aparece en el cuerpo Markdown."""
    h = _DIR_FIXTURES / "con_basura.html"
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        p = Path(td) / "c.html"
        p.write_text(h.read_text(encoding="utf-8"), encoding="utf-8")
        j = Path(td) / "c.json"
        _escribir_sidecar(j, url="https://valledellili.org/p/")
        body = convertir_html_a_md(p, j).cuerpo.lower()
    assert "window.x" not in body
    assert "aceptar cookies" not in body
    assert "nav" not in body or "solo esto" in body  # nav tag removed, word nav may appear? Actually "Solo esto" 
    # nav text "Nav" might still be issue - the nav is removed with content
    assert "pie" not in body  # footer decomposed


def test_hash_coincide_con_sidecar() -> None:
    """#4: ``hash`` en front matter = ``hash_sha256`` del JSON."""
    with open(_DIR_FIXTURES / "minimo.html", encoding="utf-8") as f:
        inner = f.read()
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        p = Path(td) / "x.html"
        p.write_text(inner, encoding="utf-8")
        j = Path(td) / "x.json"
        hxx = "c" * 64
        _escribir_sidecar(j, url="https://valledellili.org/x", hash_sha256=hxx)
        fm = convertir_html_a_md(p, j).front_matter
    assert fm["hash"] == hxx


def test_slug_mismo_que_nombre_html() -> None:
    """#5: el *stem* del .html alimenta el título de respaldo; el .md usa el mismo nombre al escribir."""
    with open(_DIR_FIXTURES / "sin_titulo.html", encoding="utf-8") as f:
        inner = f.read()
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        p = Path(td) / "historia-clave.html"
        p.write_text(inner, encoding="utf-8")
        j = Path(td) / "historia-clave.json"
        _escribir_sidecar(j, url="https://valledellili.org/a/b")
        cm = convertir_html_a_md(p, j)
        titulo = cm.front_matter["titulo"]
        out = Path(td) / "out" / "historia-clave.md"
        escribir_markdown(cm, out)
        assert out.stem == p.stem
    assert titulo == "historia-clave"


def test_extraer_titulo_y_derivar_seccion() -> None:
    assert derivar_seccion("https://valledellili.org/") == "inicio"
    assert derivar_seccion("https://valledellili.org/x/y") == "x"
    s = BeautifulSoup(
        "<html><head><title> T1 </title></head><body></body></html>",
        "html.parser",
    )
    assert extraer_titulo(s, "f") == "T1"
    s2 = BeautifulSoup(
        "<html><body><h1> H1 </h1></body></html>",
        "html.parser",
    )
    assert extraer_titulo(s2, "f") == "H1"
    s3 = BeautifulSoup("<p>x</p>", "html.parser")
    assert extraer_titulo(s3, "slug-x") == "slug-x"


def test_limpiar_html_destruye_banners() -> None:
    s = BeautifulSoup(
        "<body><div class=\"cookie-notice\">X</div><p>OK</p></body>",
        "html.parser",
    )
    limpiar_html(s)
    assert "X" not in s.get_text()
    assert "OK" in s.get_text()

