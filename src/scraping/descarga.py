"""
Crawler BFS con requests + BeautifulSoup para un dominio fijo (valledellili.org).

Flujo: cola (URL, profundidad) -> por cada URL se consulta ``GestorRobots`` antes
del GET. Las respuestas 200 con HTML se escriben en ``data/raw/valledellili-org/``
junto a un sidecar JSON. Los enlaces se extraen y se encolan mientras el nivel sea
``< profundidad_maxima`` y no se haya alcanzado ``max_paginas``.

**Idempotencia**: si el sidecar existente y el nuevo cuerpo comparten
``hash_sha256``, no se reescriben el HTML ni el JSON y se notifica
``omitido_por_hash=True`` en :class:`ResultadoDescarga`.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import unicodedata
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final, Iterator
from urllib.parse import (
    unquote,
    urldefrag,
    urljoin,
    urlparse,
    urlunparse,
)

import requests
from bs4 import BeautifulSoup
from requests import Response, Session
from requests.exceptions import ConnectionError, RequestException, Timeout

from src.scraping.robots import USER_AGENT_DEFECTO, GestorRobots

REGISTRORO = logging.getLogger(__name__)

# Extensiones a no seguir (no GET).
_EXT_BINARIA: Final = frozenset(
    {
        ".pdf",
        ".zip",
        ".rar",
        ".7z",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".svg",
        ".mp4",
        ".mp3",
        ".wav",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
    }
)

# Extensiones o rutas de página (GET permitido).
_EXT_PAGINA: Final = frozenset(
    {
        ".html",
        ".htm",
        ".php",
        ".php3",
        ".asp",
        ".aspx",
    }
)

REINTENTOS_S: Final = (1, 2, 4)
DIRECTORIO_CRUDO_POR_DEFECTO = Path("data/raw/valledellili-org")


@dataclass
class ConfiguracionCrawler:
    """Parametros del rastreo (dominio, limites, tiempos)."""

    url_inicio: str
    dominio_permitido: str = "valledellili.org"
    max_paginas: int = 200
    profundidad_maxima: int = 5
    delay_segundos: float = 1.5
    user_agent: str = USER_AGENT_DEFECTO
    timeout: int = 30
    reintentos: int = 3
    directorio_salida: Path = field(default_factory=lambda: DIRECTORIO_CRUDO_POR_DEFECTO)


@dataclass
class ResultadoDescarga:
    """Resultado de un intento de descarga o omision (robots o hash)."""

    url: str
    ruta_html: Path | None
    ruta_metadata: Path | None
    http_status: int
    hash_sha256: str
    omitido_por_robots: bool
    omitido_por_hash: bool
    error: str | None


def _a_ascii_plano(texto: str) -> str:
    """Aproximacion a ASCII: elimina tildes y pasa n con tilde a n."""
    t = texto.replace("ñ", "n").replace("Ñ", "N")
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c))


def calcular_hash(contenido: bytes) -> str:
    """Hash SHA-256 en hexadecimal (minúsculas)."""
    return hashlib.sha256(contenido).hexdigest()


def _segmento_a_kebab(segmento: str) -> str:
    s = _a_ascii_plano(unquote(segmento))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = s.strip("-")
    if not s:
        return "pagina"
    return s


def calcular_slug(url_normalizada: str) -> str:
    """
    Slug en kebab-case ASCII a partir de path (y carga de query si existe).
    La raiz se mapea a ``index``.
    """
    p = urlparse(url_normalizada)
    ruta = p.path or "/"
    ruta = ruta.rstrip("/") or "/"
    if ruta == "/":
        base = "index"
    else:
        partes = [x for x in ruta.split("/") if x]
        segs = [_segmento_a_kebab(c) for c in partes]
        base = "-".join(segs)
    if p.query:
        h = hashlib.sha256(p.query.encode("utf-8", errors="replace")).hexdigest()[:8]
        base = f"{base}-q-{h}"
    return base


def normalizar_url(url: str, base: str | None = None) -> str:
    """
    Resuelve contra *base* si hace falta, quita fragmento, fuerza esquema http(s),
    host en minúsculas y ruta mínima ``/`` si aplica.
    """
    u = url.strip()
    if not u:
        return ""
    if base:
        u = urljoin(base, u)
    u, _ = urldefrag(u)
    p = urlparse(u)
    if p.scheme and p.scheme not in ("http", "https"):
        return ""
    if not p.netloc and p.path and not p.scheme and base is None:
        u2 = f"https://{u.lstrip()}"
        p = urlparse(u2)
    esquema = p.scheme or "https"
    host = p.hostname
    if not host:
        return ""
    host_l = host.lower()
    if p.port and not (
        (esquema == "http" and p.port == 80) or (esquema == "https" and p.port == 443)
    ):
        red = f"{host_l}:{p.port}"
    else:
        red = host_l
    ruta = p.path
    if not ruta or ruta == "":
        ruta = "/"
    if not ruta.startswith("/"):
        ruta = f"/{ruta}"
    return urlunparse((esquema, red, ruta, "", p.query, ""))


def _host_permitido(host: str | None, dominio: str) -> bool:
    if not host:
        return False
    h = host.lower()
    d = dominio.lower()
    return h == d or h.endswith(f".{d}")


def _ruta_tiene_ext_binaria_inaceptable(ruta: str) -> bool:
    """True si el path apunta a un recurso no HTML según la extensión."""
    s = (ruta or "").split("?")[0].lower()
    suf = Path(s).suffix
    if not suf:
        return False
    if suf in _EXT_PAGINA:
        return False
    if suf in _EXT_BINARIA:
        return True
    # otra extensión: no asumir HTML
    return True


def extraer_enlaces(
    html: str,
    url_base: str,
    dominio_permitido: str,
) -> list[str]:
    """
    Enlaces `a[href]` y `area[href]` resueltos, http(s), del dominio, sin
    fragmento; descarta recursos con extensión binaria.
    """
    sopa = BeautifulSoup(html, "html.parser")
    salida: list[str] = []
    for etiqueta in sopa.find_all(["a", "area"]):
        href = etiqueta.get("href")
        if not href or not isinstance(href, str):
            continue
        href = href.strip()
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue
        abs_url = urljoin(url_base, href)
        n = normalizar_url(abs_url)
        if not n:
            continue
        p = urlparse(n)
        if p.scheme not in ("http", "https"):
            continue
        if not _host_permitido(p.hostname, dominio_permitido):
            continue
        if _ruta_tiene_ext_binaria_inaceptable(p.path or "/"):
            continue
        if n not in salida:
            salida.append(n)
    return salida


def descargar_pagina(
    sesion: Session,
    url: str,
    user_agent: str,
    timeout: int,
    reintentos: int,
) -> Response:
    """
    GET con reintentos y backoff 1/2/4 s ante 5xx/429 (y timeout/conexion).
    """
    cab = {"User-Agent": user_agent}
    ultima: Response | None = None
    for intento in range(reintentos):
        try:
            r = sesion.get(url, headers=cab, timeout=timeout)
            ultima = r
            if r.status_code < 500 and r.status_code != 429:
                return r
        except (Timeout, ConnectionError) as e:
            ultima = None
            REGISTRORO.warning("peticion %s error %s (intento %s)", url, e, intento + 1)
        if intento < reintentos - 1:
            espera = (
                REINTENTOS_S[intento]
                if intento < len(REINTENTOS_S)
                else REINTENTOS_S[-1]
            )
            time.sleep(float(espera))
    if ultima is not None:
        return ultima
    raise RequestException("sin respuesta valida tras reintentos")


def _es_html(resp: Response) -> bool:
    ct = (resp.headers.get("Content-Type") or "").lower()
    if "text/html" in ct or "application/xhtml" in ct:
        return True
    return resp.url.rstrip("/").endswith((".html", ".htm", ".php", ".aspx", ".asp"))


def _cabeceras_relevantes(resp: Response) -> dict[str, str]:
    claves = ("Content-Type", "Date", "Last-Modified", "ETag", "Server")
    return {c: v for c, v in resp.headers.items() if c in claves}


class _ResolucionSlug:
    """
    Asegura nombres de fichero unicos: mismo slug kebab; si otra URL lo reclama, -2, -3.
    """

    def __init__(self) -> None:
        self._slug_a_url: dict[str, str] = {}

    def asignar_stem(self, url: str, stem_base: str) -> str:
        if self._slug_a_url.get(stem_base) == url:
            return stem_base
        if stem_base not in self._slug_a_url:
            self._slug_a_url[stem_base] = url
            return stem_base
        n = 2
        while True:
            cand = f"{stem_base}-{n}"
            u = self._slug_a_url.get(cand)
            if u is None or u == url:
                if u is None:
                    self._slug_a_url[cand] = url
                return cand
            n += 1

    def precargar_desde_disco(self, directorio: Path) -> None:
        if not directorio.is_dir():
            return
        for p in directorio.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                u = data.get("url")
                st = p.stem
                if u and st:
                    self._slug_a_url[st] = u
            except (OSError, json.JSONDecodeError, TypeError) as e:
                REGISTRORO.debug("ignorando %s: %s", p, e)


class Crawler:
    """Rastreo BFS con respecto a robots, persistencia e idempotencia por hash."""

    def __init__(self, config: ConfiguracionCrawler, gestor_robots: GestorRobots) -> None:
        self._config = config
        self._gestor = gestor_robots
        self._sesion = requests.Session()
        self._vistos_en_cola: set[str] = set()
        self._resolucion = _ResolucionSlug()
        self._contador_exitos: int = 0

    def _delay(self) -> None:
        d = max(
            float(self._gestor.obtener_crawl_delay()),
            float(self._config.delay_segundos),
        )
        if d > 0:
            time.sleep(d)

    def _persistir(
        self,
        url: str,
        profundidad: int,
        cuerpo: bytes,
        resp: Response,
        hash_hex: str,
    ) -> tuple[Path, Path, bool, bool]:
        """
        Escribe HTML y JSON. Devuelve (html, json, escrito, omitido_por_hash).
        """
        dir_out = self._config.directorio_salida
        dir_out.mkdir(parents=True, exist_ok=True)
        stem_base = calcular_slug(url)
        stem = self._resolucion.asignar_stem(url, stem_base)
        ruta_html = dir_out / f"{stem}.html"
        ruta_meta = dir_out / f"{stem}.json"
        ahora = datetime.now(timezone.utc)
        if ruta_meta.is_file():
            try:
                prev = json.loads(ruta_meta.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                prev = {}
            if (
                prev.get("hash_sha256") == hash_hex
                and ruta_html.is_file()
            ):
                return ruta_html, ruta_meta, False, True
        ct = (resp.headers.get("Content-Type") or "").split(";")[0].strip()
        meta: dict[str, Any] = {
            "url": url,
            "http_status": resp.status_code,
            "content_type": ct,
            "fecha_extraccion": ahora.replace(microsecond=0).isoformat(),
            "hash_sha256": hash_hex,
            "profundidad": profundidad,
            "headers_relevantes": _cabeceras_relevantes(resp),
        }
        ruta_html.write_bytes(cuerpo)
        ruta_meta.write_text(
            json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return ruta_html, ruta_meta, True, False

    def ejecutar(self) -> Iterator[ResultadoDescarga]:
        """Explora en BFS y produce un resultado por URL procesada o omitida."""
        self._resolucion.precargar_desde_disco(self._config.directorio_salida)
        inicio = normalizar_url(self._config.url_inicio)
        if not inicio or not _host_permitido(
            urlparse(inicio).hostname,
            self._config.dominio_permitido,
        ):
            yield ResultadoDescarga(
                url=self._config.url_inicio,
                ruta_html=None,
                ruta_metadata=None,
                http_status=0,
                hash_sha256="",
                omitido_por_robots=True,
                omitido_por_hash=False,
                error="url de inicio invalida o dominio no permitido",
            )
            return
        cola: deque[tuple[str, int]] = deque()
        cola.append((inicio, 0))
        self._vistos_en_cola.add(inicio)
        vistos_proceso: set[str] = set()

        while cola and self._contador_exitos < self._config.max_paginas:
            url, profundidad = cola.popleft()
            if url in vistos_proceso:
                continue
            vistos_proceso.add(url)

            if not _host_permitido(
                urlparse(url).hostname,
                self._config.dominio_permitido,
            ):
                continue
            if _ruta_tiene_ext_binaria_inaceptable(urlparse(url).path or "/"):
                continue
            if not self._gestor.puede_descargar(url):
                REGISTRORO.info("omitido por robots: %s", url)
                yield ResultadoDescarga(
                    url=url,
                    ruta_html=None,
                    ruta_metadata=None,
                    http_status=0,
                    hash_sha256="",
                    omitido_por_robots=True,
                    omitido_por_hash=False,
                    error=None,
                )
                continue
            self._delay()
            try:
                r = descargar_pagina(
                    self._sesion,
                    url,
                    self._config.user_agent,
                    self._config.timeout,
                    self._config.reintentos,
                )
            except RequestException as e:
                yield ResultadoDescarga(
                    url=url,
                    ruta_html=None,
                    ruta_metadata=None,
                    http_status=0,
                    hash_sha256="",
                    omitido_por_robots=False,
                    omitido_por_hash=False,
                    error=str(e),
                )
                continue
            cuerpo = r.content
            h = calcular_hash(cuerpo) if cuerpo else ""
            if r.status_code != 200:
                yield ResultadoDescarga(
                    url=url,
                    ruta_html=None,
                    ruta_metadata=None,
                    http_status=r.status_code,
                    hash_sha256=h,
                    omitido_por_robots=False,
                    omitido_por_hash=False,
                    error=None,
                )
                continue
            ruta_h, ruta_m, escrito, omit_hash = self._persistir(
                url, profundidad, cuerpo, r, h
            )
            if escrito or omit_hash:
                self._contador_exitos += 1
            yield ResultadoDescarga(
                url=url,
                ruta_html=ruta_h,
                ruta_metadata=ruta_m,
                http_status=200,
                hash_sha256=h,
                omitido_por_robots=False,
                omitido_por_hash=omit_hash,
                error=None,
            )
            if _es_html(r) and profundidad < self._config.profundidad_maxima:
                base_href = r.url
                for enlace in extraer_enlaces(
                    cuerpo.decode("utf-8", errors="replace"),
                    base_href,
                    self._config.dominio_permitido,
                ):
                    n2 = normalizar_url(enlace)
                    if n2 in self._vistos_en_cola:
                        continue
                    self._vistos_en_cola.add(n2)
                    cola.append((n2, profundidad + 1))

    def cerrar_sesion(self) -> None:
        """Libera el ``Session`` de requests (llamar al terminar el rastreo)."""
        self._sesion.close()
