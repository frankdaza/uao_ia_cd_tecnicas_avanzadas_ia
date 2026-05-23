"""Pruebas del modulo robots (fixtures locales, sin red salvo mocks)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from urllib.error import HTTPError, URLError

from src.scraping import robots
from src.scraping.robots import (
    USER_AGENT_DEFECTO,
    GestorRobots,
    _descargar_texto_robots,
    cargar_robots,
    construir_url_robots,
    crawl_delay_con_defecto,
)

_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "robots_ejemplo.txt"
_URL_ROBOTS = construir_url_robots("https://valledellili.org")


def leer_lineas_robots_ejemplo() -> list[str]:
    return _FIXTURE.read_text(encoding="utf-8").splitlines()


def test_construir_url_robots() -> None:
    assert construir_url_robots("https://valledellili.org/") == (
        "https://valledellili.org/robots.txt"
    )
    assert construir_url_robots("https://valledellili.org") == (
        "https://valledellili.org/robots.txt"
    )


def test_construir_url_robots_rechaza_vacia() -> None:
    with pytest.raises(ValueError, match="url_base no puede estar vacia"):
        construir_url_robots("   ")


@patch("src.scraping.robots.urlopen")
def test_descargar_texto_robots_lectura_real(m_urlopen: MagicMock) -> None:
    cuerpo = "User-agent: *\n"
    m_resp = MagicMock()
    m_resp.read.return_value = cuerpo.encode("utf-8")
    m_urlopen.return_value.__enter__.return_value = m_resp
    m_urlopen.return_value.__exit__.return_value = None
    t = _descargar_texto_robots("https://valledellili.org/robots.txt", "bot/1")
    assert t == cuerpo
    m_urlopen.assert_called_once()
    _, kwargs = m_urlopen.call_args
    assert kwargs.get("timeout") == robots.TIMEOUT_SEG_CARGA_ROBOTS


def test_puede_descargar_permitido() -> None:
    parser = cargar_robots(leer_lineas_robots_ejemplo(), _URL_ROBOTS)
    assert parser.can_fetch(USER_AGENT_DEFECTO, "https://valledellili.org/") is True
    assert (
        parser.can_fetch(USER_AGENT_DEFECTO, "https://valledellili.org/guia/intro")
        is True
    )


def test_puede_descargar_denegado() -> None:
    parser = cargar_robots(leer_lineas_robots_ejemplo(), _URL_ROBOTS)
    assert (
        parser.can_fetch(USER_AGENT_DEFECTO, "https://valledellili.org/admin/secret")
        is False
    )


def test_crawl_delay_declarado_en_fixture() -> None:
    parser = cargar_robots(leer_lineas_robots_ejemplo(), _URL_ROBOTS)
    d = parser.crawl_delay(USER_AGENT_DEFECTO)
    assert d is not None
    assert float(d) == pytest.approx(3.0)
    assert crawl_delay_con_defecto(parser, USER_AGENT_DEFECTO, 1.0) == pytest.approx(
        3.0
    )


def test_crawl_delay_con_defecto_cae_en_uno() -> None:
    parser = cargar_robots("User-agent: *\n".splitlines(), _URL_ROBOTS)
    assert crawl_delay_con_defecto(parser, USER_AGENT_DEFECTO, 1.0) == pytest.approx(
        1.0
    )


@patch("src.scraping.robots._descargar_texto_robots", autospec=True)
def test_invocar_solo_obtener_crawl_delay_carga_igual(
    m_descarga: MagicMock,
) -> None:
    cuerpo = _FIXTURE.read_text(encoding="utf-8")
    m_descarga.return_value = cuerpo
    g = GestorRobots("https://valledellili.org")
    assert g.obtener_crawl_delay() == pytest.approx(3.0)
    m_descarga.assert_called_once()
    assert g.puede_descargar("https://valledellili.org/") is True
    m_descarga.assert_called_once()


@patch("src.scraping.robots._descargar_texto_robots", autospec=True)
def test_carga_perezosa_solo_bajo_lectura(
    m_descarga: MagicMock,
) -> None:
    cuerpo = _FIXTURE.read_text(encoding="utf-8")
    m_descarga.return_value = cuerpo
    g = GestorRobots("https://valledellili.org")
    m_descarga.assert_not_called()
    assert g.puede_descargar("https://valledellili.org/") is True
    m_descarga.assert_called_once()
    m_descarga.reset_mock()
    assert g.puede_descargar("https://valledellili.org/otro") is True
    m_descarga.assert_not_called()
    m_descarga.reset_mock()
    assert g.obtener_crawl_delay() == pytest.approx(3.0)
    m_descarga.assert_not_called()


@patch("src.scraping.robots._descargar_texto_robots", autospec=True)
def test_gestor_falla_carga_hace_falso_y_delay_uno(
    m_descarga: MagicMock,
) -> None:
    m_descarga.side_effect = HTTPError(
        "https://x/robots.txt", 503, "Servicio", None, None
    )
    g = GestorRobots("https://valledellili.org")
    assert g.puede_descargar("https://valledellili.org/") is False
    assert g.puede_descargar("https://valledellili.org/cualquier/") is False
    assert g.obtener_crawl_delay() == pytest.approx(1.0)


@patch("src.scraping.robots._descargar_texto_robots", autospec=True)
def test_gestor_acepta_robots_txt_via_descarga_mockeada(
    m_descarga: MagicMock,
) -> None:
    m_descarga.return_value = _FIXTURE.read_text(encoding="utf-8")
    g = GestorRobots("https://valledellili.org", user_agent=USER_AGENT_DEFECTO)
    assert g.puede_descargar("https://valledellili.org/") is True
    assert g.puede_descargar("https://valledellili.org/admin/") is False
    assert g.obtener_crawl_delay() == pytest.approx(3.0)


@pytest.mark.parametrize(
    "exc",
    [URLError("timeout"), OSError(61, "Connection refused")],
    ids=["url_error", "os_error"],
)
@patch("src.scraping.robots._descargar_texto_robots", autospec=True)
def test_gestor_falla_de_red_mockeada_conservador(
    m_descarga: MagicMock,
    exc: BaseException,
) -> None:
    m_descarga.side_effect = exc
    g = GestorRobots("https://valledellili.org")
    assert g.puede_descargar("https://valledellili.org/a") is False
