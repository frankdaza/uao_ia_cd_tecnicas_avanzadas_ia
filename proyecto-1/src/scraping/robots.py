"""Carga y consulta de robots.txt (stdlib, sin I/O al importar)."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Optional
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

REGISTRORO = logging.getLogger(__name__)

USER_AGENT_DEFECTO = "uao-tecnicas-ia-bot/1.0 (+contacto@example.org)"
TIMEOUT_SEG_CARGA_ROBOTS = 30.0


def construir_url_robots(url_base: str) -> str:
    """Devuelve la URL de robots.txt a partir de la base del sitio (sin I/O)."""
    s = url_base.strip()
    if not s:
        msg = "url_base no puede estar vacia"
        raise ValueError(msg)
    if not s.endswith("/"):
        s = f"{s}/"
    return urljoin(s, "robots.txt")


def cargar_robots(
    lineas: Iterable[str],
    url_robots: str,
) -> RobotFileParser:
    """
    Construye un ``RobotFileParser`` a partir de lineas (funcion pura, util para tests).
    Debe alinearse con el mismo ``url_robots`` usado al descargar.
    """
    rfp = RobotFileParser()
    rfp.set_url(url_robots)
    lineas_lista = [line.rstrip("\r\n") for line in lineas]
    rfp.parse(lineas_lista)
    return rfp


def crawl_delay_con_defecto(
    parser: RobotFileParser,
    user_agent: str,
    defecto: float = 1.0,
) -> float:
    """
    Devuelve el Crawl-delay del parser (segundos) o *defecto* si no hay valor util.
    """
    d = parser.crawl_delay(user_agent)
    if d is None:
        return defecto
    return float(d)


def _descargar_texto_robots(
    url_robots: str,
    user_agent: str,
) -> str:
    """Obtiene el cuerpo de robots.txt por HTTP. Lanza excepciones de red/HTTP."""
    cabecera = f"UaoBot compatible; {user_agent}"
    solicitud = Request(url_robots, headers={"User-Agent": cabecera})
    with urlopen(  # noqa: S310 - URL acotada a robots.txt del origen
        solicitud, timeout=TIMEOUT_SEG_CARGA_ROBOTS
    ) as resp:
        cuerpo = resp.read()
    return cuerpo.decode("utf-8", errors="replace")


class GestorRobots:
    """
    Carga perezosa de robots.txt para un origen, con modo conservador si falla la lectura.
    """

    def __init__(self, url_base: str, user_agent: str = USER_AGENT_DEFECTO) -> None:
        self.url_base: str = url_base
        self.user_agent: str = user_agent
        self._url_robots: str = construir_url_robots(url_base)
        self._parser: Optional[RobotFileParser] = None
        self._modo_conservador: bool = False
        self._carga_ejecutada: bool = False
        self._ultimo_motivo_fallo: Optional[str] = None

    def _cargar_si_hace_falta(self) -> None:
        if self._carga_ejecutada:
            return
        self._carga_ejecutada = True
        try:
            texto = _descargar_texto_robots(self._url_robots, self.user_agent)
            self._parser = cargar_robots(texto.splitlines(), self._url_robots)
        except OSError as e:
            self._modo_conservador = True
            self._parser = None
            self._ultimo_motivo_fallo = f"{type(e).__name__}: {e}"
            REGISTRORO.warning("robots.txt no disponible, modo conservador: %s", e)

    def puede_descargar(self, url: str) -> bool:
        self._cargar_si_hace_falta()
        if self._modo_conservador:
            return False
        assert self._parser is not None
        return self._parser.can_fetch(self.user_agent, url)

    def obtener_crawl_delay(self) -> float:
        self._cargar_si_hace_falta()
        if self._modo_conservador or self._parser is None:
            return 1.0
        return crawl_delay_con_defecto(self._parser, self.user_agent, 1.0)
