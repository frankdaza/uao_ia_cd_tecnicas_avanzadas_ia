"""Pruebas de utilidades de descarga (sin red, salvo marcador network)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.scraping.descarga import (
    calcular_hash,
    calcular_slug,
    descargar_pagina,
    extraer_enlaces,
    normalizar_url,
)
from src.scraping.robots import USER_AGENT_DEFECTO

HTML_ENLACES = (
    b'<html><body><a href="/p">local</a>'
    b'<a href="https://valledellili.org/z">d</a>'
    b'<a href="https://otro.com/x">e</a>'
    b'<a href="/a.pdf">pdf</a>'
    b"</body></html>"
)


def test_normalizar_url_basics() -> None:
    u = normalizar_url("/r", "https://valledellili.org/yo")
    assert u == "https://valledellili.org/r"
    n = normalizar_url("  https://valledellili.org/A/b/  ")
    assert "valledellili.org" in n
    assert n.lower().startswith("https://valledellili.org")


def test_normalizar_url_sin_fragmento() -> None:
    n = normalizar_url("https://valledellili.org/x#h")
    assert "#" not in n
    assert n.endswith("x") or n.endswith("x/")


def test_normalizar_ruta_raiz() -> None:
    s = normalizar_url("https://valledellili.org/")
    assert s == "https://valledellili.org/"


def test_calcular_slug_index() -> None:
    assert calcular_slug("https://valledellili.org/") == "index"


def test_calcular_slug_kebab_y_ascii() -> None:
    s = calcular_slug("https://valledellili.org/qui%C3%A9n-es/ni%C3%B1o")
    assert s.isascii()
    assert "-" in s
    assert "nino" in s or "mino" in s  # n con tilde -> n
    # sin eñe literal en el slug (ASCII)
    assert "ñ" not in s and "Ñ" not in s


def test_extraer_enlaces_filtra_dominio_y_pdf() -> None:
    h = HTML_ENLACES.decode()
    s = extraer_enlaces(
        h,
        "https://valledellili.org/actual",
        "valledellili.org",
    )
    assert "https://valledellili.org/p" in s
    assert "https://valledellili.org/z" in s
    assert all("otro.com" not in x for x in s)
    assert not any("pdf" in x.lower() for x in s)


@patch("src.scraping.descarga.time.sleep", autospec=True)
def test_descargar_pagina_reintento_5xx(
    m_sleep: MagicMock,
) -> None:
    sesion = requests.Session()
    m_resp_error = MagicMock()
    m_resp_error.status_code = 503
    m_resp_ok = MagicMock()
    m_resp_ok.status_code = 200
    m_get = MagicMock(side_effect=[m_resp_error, m_resp_error, m_resp_ok])
    with patch.object(sesion, "get", m_get):
        r = descargar_pagina(
            sesion, "https://e/e", USER_AGENT_DEFECTO, 30, 3
        )
    assert r.status_code == 200
    assert m_sleep.call_count == 2


@patch("src.scraping.descarga.time.sleep", autospec=True)
def test_descargar_pagina_sin_reintento_404(
    m_sleep: MagicMock,
) -> None:
    sesion = requests.Session()
    m_resp = MagicMock()
    m_resp.status_code = 404
    m_get = MagicMock(return_value=m_resp)
    with patch.object(sesion, "get", m_get):
        r = descargar_pagina(
            sesion, "https://e/e", USER_AGENT_DEFECTO, 30, 3
        )
    assert r.status_code == 404
    m_sleep.assert_not_called()


def test_calcular_hash() -> None:
    assert len(calcular_hash(b"abc")) == 64
    assert calcular_hash(b"abc") != calcular_hash(b"abd")


@pytest.mark.network
@pytest.mark.skipif(
    os.environ.get("EJECUTAR_TESTS_CON_RED", "") != "1",
    reason="definir EJECUTAR_TESTS_CON_RED=1 para integracion con valledellili.org",
)
def test_descarga_home_status_200() -> None:
    s = requests.Session()
    r = s.get(
        "https://valledellili.org/",
        headers={"User-Agent": USER_AGENT_DEFECTO},
        timeout=30,
    )
    assert r.status_code == 200
    cuerpo = r.content
    assert b"html" in cuerpo.lower() or len(cuerpo) > 100
